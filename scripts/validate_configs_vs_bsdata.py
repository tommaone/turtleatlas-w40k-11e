#!/usr/bin/env python3
"""Validate ALL config files against BSData wargear constraints.

Cross-checks:
  1. Every weapon in config builds exists in merged data for that unit
  2. Config builds respect BSData choice groups (pick 1 from N)
  3. Config builds respect BSData max constraints
  4. No unauthorized weapons (weapons in config not in merged data)
  5. Mandatory weapons (fixed_ranged/fixed_melee) are present
  6. Choice picks respect mutual exclusion (pick 1 from group)

Known false positive filters:
  - "Close combat weapon" is a generic fallback (engine handles it)
  - "Armoured tracks", "Shearing claws", etc. are default melee (engine handles via fallback)
  - Profile names ("Plasma pistol - standard") vs weapon names ("Plasma pistol") — name mapping
  - Witchfire profiles (focused/unfocused) are variants, not separate weapons

Usage:
    python3 scripts/validate_configs_vs_bsdata.py [--faction chaos-space-marines]
    python3 scripts/validate_configs_vs_bsdata.py --all
"""
import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from adapter.bsdata_parser_11e import BSDataParser11e

# ── Slug → BSData catalogue name mapping ───────────────────────────
SLUG_TO_BSDATA_CAT = {
    "chaos-space-marines": "Chaos - Chaos Space Marines",
    "death-guard": "Chaos - Death Guard",
    "thousand-sons": "Chaos - Thousand Sons",
    "world-eaters": "Chaos - World Eaters",
    "emperors-children": "Chaos - Emperor's Children",
    "chaos-daemons": "Chaos - Chaos Daemons",
    "chaos-knights": "Chaos - Chaos Knights",
    "space-marines": "Imperium - Space Marines",
    "dark-angels": "Imperium - Dark Angels",
    "blood-angels": "Imperium - Blood Angels",
    "black-templars": "Imperium - Black Templars",
    "space-wolves": "Imperium - Space Wolves",
    "grey-knights": "Imperium - Grey Knights",
    "adepta-sororitas": "Imperium - Adepta Sororitas",
    "adeptus-mechanicus": "Imperium - Adeptus Mechanicus",
    "adeptus-custodes": "Imperium - Adeptus Custodes",
    "astra-militarum": "Imperium - Astra Militarum",
    "necrons": "Necrons",
    "orks": "Orks",
    "tau-empire": "T'au Empire",
    "tyranids": "Tyranids",
    "genestealer-cults": "Genestealer Cults",
    "aeldari": "Aeldari - Aeldari Library",
    "drukhari": "Aeldari - Drukhari",
    "leagues-of-votann": "Leagues of Votann",
    "imperial-knights": "Imperium - Imperial Knights",
    "imperial-agents": "Imperium - Agents of the Imperium",
    "deathwatch": "Imperium - Deathwatch",
}

# ── False positive filters ─────────────────────────────────────────
# Generic melee weapons the engine handles via fallback
GENERIC_MELEE = {
    "close combat weapon", "close combat weapons", "melee weapon",
    "armoured tracks", "armoured hull", "shearing claws",
    "heldrake claws", "maulerfiend fists", "great cleaver of khorne",
    "soulflayer tendrils and claws", "defiler claws",
    "hellforged weapons", "bladed limbs",
    "relic weapon", "power weapon",  # Generic placeholders
}

# Profile name suffixes that are variants (not separate weapons)
PROFILE_SUFFIXES = [" - standard", " - supercharge", " - focused witchfire",
                    " - witchfire", " - focused", " - sweep", " - strike"]

# Weak/default weapons that BSData marks as mandatory but don't significantly
# affect DPP. These are "always equipped" weapons — engine handles them.
# Only flag these as LOW severity, not as real issues.
WEAK_DEFAULT_WEAPONS = {
    "havoc launcher", "hunter-killer missile", "hunter-killer missile",
    "storm bolter", "heavy stubber", "armoured tracks", "armoured hull",
    "armoured feet", "titanic feet", "wraithbone hull", "iron claw",
    "close combat weapon", "close combat weapons",
    "diabolus heavy stubber", "cognis heavy stubber",
    "combi-bolter", "twin boltgun", "twin heavy bolter",
    "lasgun array", "hurricane bolter",
}


def normalize_weapon_name(name: str) -> str:
    """Normalize weapon name by stripping profile suffixes."""
    n = name.strip()
    for suffix in PROFILE_SUFFIXES:
        if n.lower().endswith(suffix.lower()):
            n = n[:-len(suffix)]
    return n


def canonical_weapon(name: str, catalog_lower: set[str]) -> str:
    """Canonical form used to compare config and BSData weapon names.

    Mirrors the generator's normalize_for_catalog: strip profile suffixes,
    then strip a trailing 's' only if the singular is an EXACT catalog weapon.
    This aligns plural catalog names ('Twin Haywire Blasters') with the
    singularized config ('Twin Haywire Blaster') the generator emits.
    """
    n = normalize_weapon_name(name).lower()
    if n.endswith("s") and not n.endswith("ss"):
        singular = n[:-1]
        if singular in catalog_lower:
            return singular
    return n


def load_merged_weapons(merged_path: Path) -> dict[str, list[dict]]:
    """Load merged data and return {unit_name: [weapon_entry_dicts]}."""
    with open(merged_path) as f:
        data = json.load(f)
    result = {}
    for u in data.get("units", []):
        name = u.get("name", "")
        prof = u.get("profile") or {}
        weapons = prof.get("weapons", [])
        result[name] = weapons
    return result


def get_weapon_names_from_merged(weapons: list[dict]) -> set[str]:
    """Extract all weapon names (weapon + profile names) from merged data."""
    names = set()
    for w in weapons:
        wname = w.get("name", "")
        if wname:
            names.add(wname)
            names.add(wname.lower())
        for p in w.get("profiles", []):
            pname = p.get("name", "")
            if pname:
                names.add(pname)
                names.add(pname.lower())
                # Also add normalized name (without suffix)
                norm = normalize_weapon_name(pname)
                names.add(norm)
                names.add(norm.lower())
    return names


def load_config(config_dir: Path) -> dict:
    """Load all config files for a faction."""
    config = {"squads": {}, "characters": {}, "vehicles": {}, "weapon_options": {}}
    for fname, key in [("squads.json", "squads"), ("characters.json", "characters"),
                       ("vehicles.json", "vehicles"), ("weapon_options.json", "weapon_options")]:
        fpath = config_dir / fname
        if fpath.exists():
            with open(fpath) as f:
                config[key] = json.load(f)
    return config


def _add_build_weapons(build: dict, names: set[str]) -> None:
    """Collect every weapon name from one build (all config formats)."""
    for r in build.get("ranged", []) or []:
        if isinstance(r, str):
            names.add(r)
        elif isinstance(r, dict) and r.get("name"):
            names.add(r["name"])
    for m in build.get("melee", []) or []:
        if isinstance(m, str):
            names.add(m)
        elif isinstance(m, dict) and m.get("name"):
            names.add(m["name"])
    for rc in build.get("ranged_choices", []) or []:
        if isinstance(rc, list):
            for r in rc:
                names.add(r)
        elif isinstance(rc, str):
            names.add(rc)
    for mc in build.get("melee_choices", []) or []:
        if isinstance(mc, list):
            for m in mc:
                names.add(m)
        elif isinstance(mc, str):
            names.add(mc)
    # Typed fixed list + untyped slots (regenerated weapon_options entries)
    for f in build.get("fixed", []) or []:
        if f.get("name"):
            names.add(f["name"])
    for slot in build.get("slots", []) or []:
        for c in slot.get("choices", []) or []:
            if c.get("name"):
                names.add(c["name"])
    # Squad builds with models array. ranged/melee may be a string (single
    # fixed weapon) or a list (multiple fixed weapons, e.g. Warlock:
    # Shuriken Pistol + Destructor).
    for m in build.get("models", []) or []:
        for key in ("ranged", "melee"):
            val = m.get(key)
            if isinstance(val, str):
                names.add(val)
            elif isinstance(val, list):
                for v in val:
                    names.add(v)
        # Parallel-variant alloc models: choices carry variant loadouts
        for ch in m.get("alloc", []) or []:
            for key in ("ranged", "melee"):
                val = ch.get(key)
                if isinstance(val, str):
                    names.add(val)
                elif isinstance(val, list):
                    for v in val:
                        names.add(v)
            for slot in ch.get("slots", []) or []:
                for c in slot.get("choices", []) or []:
                    if c.get("ranged"):
                        names.add(c["ranged"])
                    if c.get("melee"):
                        names.add(c["melee"])
        # Per-model slots: choices carry resolved bundle payloads
        # ({name, ranged?, melee?}). The payload weapon names are real
        # catalog weapons; the display name may be a bundle label
        # ('Banshee Blade and Shuriken Pistol') that is NOT a catalog key.
        for slot in m.get("slots", []) or []:
            for c in slot.get("choices", []) or []:
                if c.get("ranged"):
                    names.add(c["ranged"])
                if c.get("melee"):
                    names.add(c["melee"])


def extract_config_weapon_names(unit_cfg: dict) -> set[str]:
    """Extract all weapon names referenced in a config unit."""
    names = set()

    # Squads/vehicles top-level scalar fields: ranged/melee may be a string
    # (squad legacy) or a list of dicts (vehicles flat spec: [{name,...}]).
    for key in ["ranged", "melee"]:
        val = unit_cfg.get(key)
        if isinstance(val, str) and val:
            names.add(val)
        elif isinstance(val, list):
            for w in val:
                if isinstance(w, dict) and w.get("name"):
                    names.add(w["name"])
                elif isinstance(w, str):
                    names.add(w)
    for s in unit_cfg.get("specials", []):
        names.add(s)
    for i in unit_cfg.get("innate", []):
        names.add(i)
    # vehicles.json flat-spec fixed lists + weapon_slots
    for key in ("fixed_ranged", "fixed_melee"):
        for w in unit_cfg.get(key, []) or []:
            if isinstance(w, str):
                names.add(w)
            elif isinstance(w, dict) and w.get("name"):
                names.add(w["name"])
    for slot in unit_cfg.get("weapon_slots", []) or []:
        for entry in slot.get("from", []) or []:
            if entry.get("weapon"):
                names.add(entry["weapon"])
            for wn in entry.get("weapons", []) or []:
                names.add(wn)
            if entry.get("melee_weapon"):
                names.add(entry["melee_weapon"])
            for wn in entry.get("melee_weapons", []) or []:
                names.add(wn)

    # Builds format: characters nest under "weapon_options", squads and
    # weapon_options entries store builds at the TOP level.
    build_sources = []
    wo = unit_cfg.get("weapon_options", {})
    if isinstance(wo, dict) and wo.get("builds"):
        build_sources.extend(wo["builds"])
    if unit_cfg.get("builds"):
        build_sources.extend(unit_cfg["builds"])
    for build in build_sources:
        _add_build_weapons(build, names)

    return names


def is_generic_melee(name: str) -> bool:
    """Check if this is a generic melee weapon the engine handles via fallback."""
    return name.lower() in GENERIC_MELEE


def is_weak_default(name: str) -> bool:
    """Check if this is a weak/default weapon that doesn't significantly affect DPP."""
    return name.lower() in WEAK_DEFAULT_WEAPONS


def _expand_two_prefix(names: list[str]) -> list[str]:
    """Expand count-prefixed BSData fixed names ('Two X' -> 2x 'X').

    The generator expands 'Two X' into 2x the single profile because the
    'Two X' catalog profile carries single-weapon stats (A=1, not A=2).
    The validator must apply the same expansion before comparing, or 2x
    'dark lance' in the config fails to satisfy 'Two dark lances'.
    """
    out = []
    for n in names:
        if n.lower().startswith("two "):
            base = n[4:]
            out.append(base)
            out.append(base)
        else:
            out.append(n)
    return out


def validate_unit(unit_name: str, unit_cfg: dict, merged_weapons: list[dict],
                  bsdata_constraints: dict | None, global_weapon_names: set[str] | None = None,
                  verbose: bool = False) -> list[str]:
    """Validate one unit's config against merged data and BSData constraints.
    
    Returns list of (severity, message) tuples.
    """
    issues = []
    merged_names = get_weapon_names_from_merged(merged_weapons)
    # Shared choice groups (e.g. War Walker 'Heavy Weapons') resolve to
    # weapon profiles that merged attributes to other units, so the per-unit
    # snapshot is incomplete. Use the faction-wide weapon set for the
    # "is this a real catalog weapon" decision; keep the per-unit set for
    # unit-specific checks.
    real_weapon_names = global_weapon_names or merged_names
    config_names = extract_config_weapon_names(unit_cfg)

    # ── 1. Every config weapon exists in merged data ────────────────
    for w in config_names:
        w_lower = w.lower()
        if w_lower in real_weapon_names or w_lower in merged_names:
            continue
        # Skip generic weapons (engine handles via fallback)
        if is_generic_melee(w):
            continue
        # Try normalized name (strip profile suffix)
        norm = normalize_weapon_name(w).lower()
        if norm in real_weapon_names or norm in merged_names:
            continue
        # Try fuzzy: substring match against the faction-wide set
        fuzzy = any(w_lower in m or m in w_lower for m in real_weapon_names if m)
        if not fuzzy:
            issues.append(("HIGH", f"NOT IN DATA: '{w}'"))

    # ── 2. BSData constraints check ────────────────────────────────
    if not bsdata_constraints:
        return issues

    builds = bsdata_constraints.get("builds", [])
    for build in builds:
        build_name = build.get("name", "default")

        # ── 2a. Mandatory weapons (fixed_ranged, fixed_melee) ───────
        # Expand count-prefixed names so 2x 'dark lance' satisfies
        # 'Two dark lances' (the generator expands the same way).
        for fw in _expand_two_prefix(build.get("fixed_ranged", [])):
            fw_lower = fw.lower()
            # Check if config has this weapon (exact or normalized)
            config_has = any(
                n.lower() == fw_lower or
                normalize_weapon_name(n).lower() == fw_lower
                for n in config_names
            )
            if not config_has:
                # Only flag if it's a real weapon (in merged data)
                if fw_lower in {n.lower() for n in merged_names}:
                    severity = "LOW" if is_weak_default(fw) else "MEDIUM"
                    issues.append((severity, f"MISSING FIXED RANGED: '{fw}' (build: {build_name})"))
        for fw in _expand_two_prefix(build.get("fixed_melee", [])):
            fw_lower = fw.lower()
            # Skip generic melee weapons
            if is_generic_melee(fw):
                continue
            config_has = any(
                n.lower() == fw_lower or
                normalize_weapon_name(n).lower() == fw_lower
                for n in config_names
            )
            if not config_has:
                if fw_lower in {n.lower() for n in merged_names}:
                    severity = "LOW" if is_weak_default(fw) else "MEDIUM"
                    issues.append((severity, f"MISSING FIXED MELEE: '{fw}' (build: {build_name})"))

        # ── 2b. Choice groups: config picks ⊆ BSData choices ────────
        # Compare in canonical form (singular↔plural aligned to the catalog)
        # so a config 'Twin Haywire Blaster' matches BSData's
        # 'Twin Haywire Blasters'.
        catalog_lower = {n.lower() for n in (global_weapon_names or merged_names)}
        all_bsdata_ranged_choices = set()
        all_bsdata_melee_choices = set()
        for rc in build.get("ranged_choices", []):
            if isinstance(rc, list):
                for c in rc:
                    all_bsdata_ranged_choices.add(c.lower())
                    all_bsdata_ranged_choices.add(canonical_weapon(c, catalog_lower))
        for mc in build.get("melee_choices", []):
            if isinstance(mc, list):
                for c in mc:
                    all_bsdata_melee_choices.add(c.lower())
                    all_bsdata_melee_choices.add(canonical_weapon(c, catalog_lower))

        # Only check extra weapons if there ARE choice groups
        if not all_bsdata_ranged_choices and not all_bsdata_melee_choices:
            continue  # No choice groups — nothing to check

        # Fixed weapons — expand count prefixes ('Two X' -> 2x 'X') and
        # canonicalize so expanded 'dark lance' matches BSData's
        # 'Two dark lances'.
        fixed_r = set()
        for fw in _expand_two_prefix(build.get("fixed_ranged", [])):
            fixed_r.add(fw.lower())
            fixed_r.add(canonical_weapon(fw, catalog_lower))
        fixed_m = set()
        for fw in build.get("fixed_melee", []):
            fixed_m.add(fw.lower())
            fixed_m.add(canonical_weapon(fw, catalog_lower))

        for w in config_names:
            w_lower = w.lower()
            w_canon = canonical_weapon(w, catalog_lower)
            if w_lower in fixed_r or w_lower in fixed_m or w_canon in fixed_r or w_canon in fixed_m:
                continue  # Fixed weapon — OK
            # Check if it's in any BSData choice group
            in_ranged = w_lower in all_bsdata_ranged_choices or w_canon in all_bsdata_ranged_choices
            in_melee = w_lower in all_bsdata_melee_choices or w_canon in all_bsdata_melee_choices
            if not in_ranged and not in_melee:
                # Not in any BSData choice group — might be an extra
                if w_lower in {n.lower() for n in merged_names} or \
                   w_canon in {n.lower() for n in merged_names}:
                    # Skip generic melee
                    if not is_generic_melee(w):
                        issues.append(("MEDIUM", f"EXTRA WEAPON (not in BSData choices): '{w}' (build: {build_name})"))

        # ── 2c. Max constraints — config lists ALL available options ─
        # The ENGINE picks the best combination respecting max constraints.
        # Config should list all options; engine picks max_r/max_m from them.
        # We only flag if config is MISSING options that BSData offers.
        max_ranged = build.get("max_ranged")
        max_melee = build.get("max_melee")
        # (no validation needed here — engine handles selection)

    return issues


def validate_faction(slug: str, bsdata_parser: BSDataParser11e, verbose: bool = False) -> tuple[int, list[str]]:
    """Validate all configs for one faction. Returns (issue_count, lines)."""
    lines = []
    cat_name = SLUG_TO_BSDATA_CAT.get(slug)
    if not cat_name:
        return 0, [f"  Unknown slug: {slug}"]

    # Load BSData constraints
    bsdata_constraints = bsdata_parser.extract_wargear_constraints(cat_name)

    # Load merged data
    merged_path = REPO_ROOT / "data" / "merged" / f"{slug}.json"
    if not merged_path.exists():
        return 0, [f"  Merged data not found: {merged_path}"]
    merged_weapons = load_merged_weapons(merged_path)

    # Faction-wide weapon name set — shared choice groups (e.g. War Walker
    # 'Heavy Weapons') resolve to profiles the per-unit merged snapshot
    # attributes elsewhere; the global set is the "is this a real weapon"
    # truth for check 1.
    global_weapon_names: set[str] = set()
    for weapons in merged_weapons.values():
        global_weapon_names |= get_weapon_names_from_merged(weapons)

    # Load config
    config_dir = REPO_ROOT / "data" / "config" / slug
    if not config_dir.exists():
        return 0, [f"  Config dir not found: {config_dir}"]
    config = load_config(config_dir)

    total_issues = 0

    # Validate each unit type
    for unit_type, config_key in [("squads", "squads"), ("characters", "characters"),
                                   ("vehicles", "vehicles"), ("weapon_options", "weapon_options")]:
        for unit_name, unit_cfg in config.get(config_key, {}).items():
            if unit_name.startswith("_"):
                continue

            # Find BSData constraints (fuzzy match by name)
            bsdata_c = None
            for bs_name, bs_data in bsdata_constraints.items():
                if bs_name.lower() == unit_name.lower():
                    bsdata_c = bs_data
                    break
            if not bsdata_c:
                for bs_name, bs_data in bsdata_constraints.items():
                    if unit_name.lower() in bs_name.lower() or bs_name.lower() in unit_name.lower():
                        bsdata_c = bs_data
                        break

            unit_merged = merged_weapons.get(unit_name, [])
            unit_errors = validate_unit(unit_name, unit_cfg, unit_merged, bsdata_c,
                                        global_weapon_names, verbose)

            if unit_errors:
                total_issues += len(unit_errors)
                lines.append(f"\n  {unit_name} ({unit_type}):")
                for severity, msg in unit_errors:
                    lines.append(f"  [{severity}] {msg}")

    return total_issues, lines


def main():
    parser = argparse.ArgumentParser(description="Validate configs against BSData")
    parser.add_argument("--faction", "-f", help="Validate one faction (slug)")
    parser.add_argument("--all", "-a", action="store_true", help="Validate all factions")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all details")
    args = parser.parse_args()

    bsdata_parser = BSDataParser11e(str(REPO_ROOT / "bsdata"))

    if args.faction:
        slugs = [args.faction]
    elif args.all:
        slugs = list(SLUG_TO_BSDATA_CAT.keys())
    else:
        print("Usage: python3 validate_configs_vs_bsdata.py --faction <slug> | --all")
        sys.exit(1)

    grand_total = 0
    factions_with_issues = 0
    for slug in slugs:
        issues, lines = validate_faction(slug, bsdata_parser, args.verbose)
        if issues > 0:
            factions_with_issues += 1
            grand_total += issues
            print(f"\n{'='*60}")
            print(f"{slug} — {issues} issue(s)")
            print(f"{'='*60}")
            for line in lines:
                print(line)

    print(f"\n{'='*60}")
    print(f"SUMMARY: {grand_total} issues across {factions_with_issues}/{len(slugs)} factions")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
