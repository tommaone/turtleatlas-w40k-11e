#!/usr/bin/env python3
"""Auto-generate config files from BSData wargear constraints.

Reads BSData → extracts constraints → classifies weapons by profile →
generates correct configs for characters, vehicles, and squads.

Usage:
    python3 scripts/generate_configs_from_bsdata.py --faction chaos-space-marines
    python3 scripts/generate_configs_from_bsdata.py --all
    python3 scripts/generate_configs_from_bsdata.py --faction chaos-space-marines --dry-run
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

# ── Profile name normalization ─────────────────────────────────────
PROFILE_SUFFIXES = [" - standard", " - supercharge", " - focused witchfire",
                    " - witchfire", " - focused", " - sweep", " - strike"]

def normalize_weapon_name(name: str) -> str:
    """Strip profile suffixes to get the base weapon name."""
    n = name.strip()
    for suffix in PROFILE_SUFFIXES:
        if n.lower().endswith(suffix.lower()):
            n = n[:-len(suffix)]
    return n


# Decorative BSData prefixes that don't affect weapon stats
# These are faction-specific cosmetic prefixes (e.g. Death Guard's "Plague" variants)
DECORATIVE_PREFIXES = [
    "plague", "blight", "bubotic", "corrupted", "defiled",
]

def strip_bsdata_prefixes(name: str) -> str:
    """Strip BSData cosmetic prefixes from weapon names.
    
    Handles:
    - Count prefixes: "Two X", "2 X", "3 X" etc. → "X"
    - Decorative keywords: "Plague heavy bolter" → "heavy bolter" (Death Guard)
    """
    n = name.strip()
    if n.lower().startswith("two "):
        n = n[4:]
    # Also handle numeric prefixes like "2 ", "3 ", "4 "
    import re
    n = re.sub(r'^\d+\s+', '', n)
    # Strip decorative faction keywords — try each at the start of the remaining name
    for prefix in DECORATIVE_PREFIXES:
        pfx = prefix + " "
        if n.lower().startswith(pfx):
            n = n[len(pfx):].strip()
            break  # only strip one level
    return n


def expand_two_prefix(weapons: list[str], merged_weapons: dict[str, set[str]] | None = None) -> list[str]:
    """Expand 'Two X' entries into 2× 'X' (normalized).
    
    BSData's "Two X" entries have wrong stats (A=2 instead of A=12).
    Strip prefix and duplicate so engine loads single profile twice → correct total.
    """
    result = []
    for w in weapons:
        if w.lower().startswith("two "):
            base = normalize_for_catalog(w, merged_weapons)
            result.append(base)
            result.append(base)
        else:
            result.append(normalize_for_catalog(w, merged_weapons))
    return result


def normalize_for_catalog(name: str, merged_weapons: dict[str, set[str]] | None = None) -> str:
    """Normalize a weapon name for engine lookup.
    
    Strips 'Two ' prefix, profile suffixes, and plural 's' if singular exists.
    Result matches catalog keys.
    """
    n = strip_bsdata_prefixes(name)
    n = normalize_weapon_name(n)
    # BSData uses "cannons" but catalog has "cannon" — strip trailing 's'
    # Only if singular form exists in merged data
    if merged_weapons and n.endswith('s') and not n.endswith('ss'):
        singular = n[:-1]
        all_weapons = merged_weapons.get("ranged", set()) | merged_weapons.get("melee", set())
        if any(singular.lower() in w.lower() or w.lower() in singular.lower() for w in all_weapons):
            return singular
    return n


def load_merged_data(merged_path: Path) -> dict:
    """Load merged data and return full dict."""
    with open(merged_path) as f:
        return json.load(f)


def get_unit_weapons_from_merged(merged_data: dict, unit_name: str) -> dict[str, set[str]]:
    """Get ranged/melee weapon names for a unit from merged data.
    
    Returns {"ranged": {weapon_names}, "melee": {weapon_names}}
    Uses case-insensitive matching.
    """
    result = {"ranged": set(), "melee": set()}
    name_lower = unit_name.lower()
    for u in merged_data.get("units", []):
        if u.get("name", "").lower() != name_lower:
            continue
        prof = u.get("profile") or {}
        for w in prof.get("weapons", []):
            wname = w.get("name", "")
            for p in w.get("profiles", []):
                ptype = p.get("typeName", "")
                pname = p.get("name", "")
                if "Ranged" in ptype:
                    result["ranged"].add(wname)
                    result["ranged"].add(pname)
                    result["ranged"].add(normalize_weapon_name(pname))
                elif "Melee" in ptype:
                    result["melee"].add(wname)
                    result["melee"].add(pname)
                    result["melee"].add(normalize_weapon_name(pname))
        break
    return result


def classify_weapon_by_profile(weapon_name: str, merged_weapons: dict[str, set[str]]) -> str:
    """Classify a weapon as 'ranged', 'melee', or 'unknown' using merged data."""
    wn = weapon_name.lower()
    norm = normalize_weapon_name(weapon_name).lower()
    # Strip BSData "Two " prefix (e.g. "Two magma cutters" → "magma cutter")
    # Both variants share identical profiles — the name difference is cosmetic.
    two_stripped = wn[4:] if wn.startswith("two ") else wn
    
    in_ranged = any(
        wn in r.lower() or r.lower() in wn or
        two_stripped in r.lower() or r.lower() in two_stripped or
        norm in r.lower() or r.lower() in norm
        for r in merged_weapons["ranged"] if r
    )
    in_melee = any(
        wn in m.lower() or m.lower() in wn or
        two_stripped in m.lower() or m.lower() in two_stripped or
        norm in m.lower() or m.lower() in norm
        for m in merged_weapons["melee"] if m
    )
    
    if in_ranged and not in_melee:
        return "ranged"
    elif in_melee and not in_ranged:
        return "melee"
    elif in_ranged and in_melee:
        return "both"  # Dual-profile weapon (like Talon of Horus)
    else:
        return "unknown"


def normalize_choice_group(choices: list[str], merged_weapons: dict[str, set[str]]) -> list[str]:
    """Normalize weapon names in a choice group without splitting by type.
    
    Each group = one SLOT (slot structure > perfect weapon type classification).
    Mixed-type groups (ranged + melee) stay together.
    The minor DPP inaccuracy from treating a melee weapon as ranged (or vice versa)
    is vastly preferable to breaking the slot structure.
    """
    return [normalize_for_catalog(w, merged_weapons) for w in choices]


def reclassify_mixed_group(choices: list[str], merged_weapons: dict[str, set[str]]) -> tuple[list[str], list[str]]:
    """Split a choice group into ranged and melee based on actual profiles.
    
    OBSOLETE: Breaks slot structure. Use normalize_choice_group instead.
    Kept for generate_squad_config where choices are flattened into a single specials list.
    """
    ranged = []
    melee = []
    for w in choices:
        cat = classify_weapon_by_profile(w, merged_weapons)
        clean = normalize_for_catalog(w, merged_weapons)
        if cat == "ranged":
            ranged.append(clean)
        elif cat == "melee":
            melee.append(clean)
        elif cat == "both":
            ranged.append(clean)
            melee.append(clean)
        else:
            ranged.append(clean)
    return ranged, melee


def load_existing_config(config_dir: Path) -> dict:
    """Load existing config to preserve hand-crafted data (pts, info, etc.)."""
    config = {}
    for fname in ["characters.json", "squads.json", "vehicles.json", "weapon_options.json"]:
        fpath = config_dir / fname
        if fpath.exists():
            with open(fpath) as f:
                config[fname] = json.load(f)
    return config


def get_existing_unit_config(existing_config: dict, unit_name: str) -> dict | None:
    """Find existing config for a unit across all config files.
    
    Uses case-insensitive matching.
    """
    name_lower = unit_name.lower()
    for fname, data in existing_config.items():
        for key, val in data.items():
            if key.lower() == name_lower:
                return val
    return None


def generate_character_config(unit_name: str, bsdata_constraint: dict,
                              merged_weapons: dict[str, set[str]],
                              existing: dict | None) -> dict:
    """Generate config for a character from BSData constraints.
    
    Preserves existing pts, info. Only overwrites weapon_options.
    """
    builds = bsdata_constraint.get("builds", [])
    if not builds:
        return existing or {}
    
    # Preserve existing pts/info
    pts = existing.get("pts", 0) if existing else 0
    pts_3rd = existing.get("pts_3rd") if existing else None
    info = existing.get("info", {}) if existing else {}
    
    generated_builds = []
    for build in builds:
        fixed_r = expand_two_prefix(list(build.get("fixed_ranged", [])), merged_weapons)
        fixed_m = expand_two_prefix(list(build.get("fixed_melee", [])), merged_weapons)
        rc_groups = build.get("ranged_choices", [])
        mc_groups = build.get("melee_choices", [])
        
        # Keep groups intact — each group is an independent SLOT
        all_ranged_choices = []
        all_melee_choices = []
        
        for rc in rc_groups:
            all_ranged_choices.append(normalize_choice_group(rc, merged_weapons))
        
        for mc in mc_groups:
            all_melee_choices.append(normalize_choice_group(mc, merged_weapons))
        
        # max_ranged/max_melee = null → engine uses product semantics
        # (picks 1 from each group independently). This is the slot model.
        # New format: untyped fixed weapons with types
        fixed = []
        fixed.extend({"name": n, "type": "ranged"} for n in fixed_r)
        fixed.extend({"name": n, "type": "melee"} for n in fixed_m)
        
        raw_slots = build.get("slots", [])
        slots = []
        for slot in raw_slots:
            choices = []
            for c in slot.get("choices", []):
                clean_name = normalize_for_catalog(c["name"], merged_weapons)
                choices.append({"name": clean_name, "type": c.get("type", "ranged")})
            slots.append({"name": slot.get("name", ""), "choices": choices})
        
        generated_builds.append({
            "name": build.get("name", "default"),
            "ranged": fixed_r,
            "melee": fixed_m,
            "ranged_choices": all_ranged_choices,
            "melee_choices": all_melee_choices,
            "max_ranged": None,
            "max_melee": None,
            # New format: untyped slots + typed choices
            "fixed": fixed,
            "slots": slots,
        })
    
    result = {
        "pts": pts,
        "info": info,
        "weapon_options": {
            "builds": generated_builds
        }
    }
    if pts_3rd is not None:
        result["pts_3rd"] = pts_3rd
    return result


def generate_vehicle_config(unit_name: str, bsdata_constraint: dict,
                            merged_weapons: dict[str, set[str]],
                            existing: dict | None) -> dict:
    """Generate config for a vehicle from BSData constraints.
    
    weapon_options.json has builds at TOP LEVEL: {pts, info, builds: [...]}
    NOT nested under weapon_options key.
    """
    builds = bsdata_constraint.get("builds", [])
    if not builds:
        return existing or {}
    
    pts = existing.get("pts", 0) if existing else 0
    pts_3rd = existing.get("pts_3rd") if existing else None
    info = existing.get("info", {}) if existing else {}
    
    generated_builds = []
    for build in builds:
        fixed_r = expand_two_prefix(list(build.get("fixed_ranged", [])), merged_weapons)
        fixed_m = expand_two_prefix(list(build.get("fixed_melee", [])), merged_weapons)
        rc_groups = build.get("ranged_choices", [])
        mc_groups = build.get("melee_choices", [])
        
        # Each group = independent SLOT → keep intact (no type splitting)
        all_ranged_choices = [normalize_choice_group(rc, merged_weapons) for rc in rc_groups]
        all_melee_choices = [normalize_choice_group(mc, merged_weapons) for mc in mc_groups]
        
        # New format: untyped fixed weapons with types
        fixed = []
        fixed.extend({"name": n, "type": "ranged"} for n in fixed_r)
        fixed.extend({"name": n, "type": "melee"} for n in fixed_m)
        
        raw_slots = build.get("slots", [])
        slots = []
        for slot in raw_slots:
            choices = []
            for c in slot.get("choices", []):
                clean_name = normalize_for_catalog(c["name"], merged_weapons)
                choices.append({"name": clean_name, "type": c.get("type", "ranged")})
            slots.append({"name": slot.get("name", ""), "choices": choices})
        
        generated_builds.append({
            "name": build.get("name", "default"),
            "fixed_ranged": fixed_r,
            "fixed_melee": fixed_m,
            "ranged_choices": all_ranged_choices,
            "melee_choices": all_melee_choices,
            "max_ranged": None,
            "max_melee": None,
            # New format: untyped slots + typed choices
            "fixed": fixed,
            "slots": slots,
        })
    
    result = {
        "pts": pts,
        "info": info,
        "builds": generated_builds,
    }
    if pts_3rd is not None:
        result["pts_3rd"] = pts_3rd
    # Preserve vehicle-specific fields
    if existing:
        for key in ["ignore_cover_aura", "invul_save"]:
            if key in existing and key not in result:
                result[key] = existing[key]
    return result


def generate_squad_config(unit_name: str, bsdata_constraint: dict,
                          merged_weapons: dict[str, set[str]],
                          existing: dict | None) -> dict:
    """Generate config for a squad from BSData constraints.
    
    Squads use legacy format: ranged (string), melee (string), specials (list), special_max (int).
    Preserves existing pts, n, info, sp_loses_r, sp_loses_m, etc.
    """
    builds = bsdata_constraint.get("builds", [])
    if not builds:
        return existing or {}
    
    b = builds[0]  # Most squads have 1 build
    
    fixed_r = b.get("fixed_ranged", [])
    fixed_m = b.get("fixed_melee", [])
    rc_groups = b.get("ranged_choices", [])
    mc_groups = b.get("melee_choices", [])
    max_r = b.get("max_ranged")
    max_m = b.get("max_melee")
    
    # Reclassify mixed groups
    all_ranged_choices = []
    all_melee_choices = []
    for rc in rc_groups:
        r, m = reclassify_mixed_group(rc, merged_weapons)
        all_ranged_choices.extend(r)
        all_melee_choices.extend(m)
    for mc in mc_groups:
        r, m = reclassify_mixed_group(mc, merged_weapons)
        all_ranged_choices.extend(r)
        all_melee_choices.extend(m)
    
    # Default ranged = first fixed ranged weapon (for squads, only the primary weapon)
    ranged = fixed_r[0] if fixed_r else None
    # Default melee = first fixed melee weapon
    melee = fixed_m[0] if fixed_m else None
    # Extra fixed weapons beyond the first go into innate list
    innate = []
    if len(fixed_r) > 1:
        innate.extend(fixed_r[1:])
    if len(fixed_m) > 1:
        innate.extend(fixed_m[1:])
    
    # Collect all choice weapons as specials
    specials = all_ranged_choices + all_melee_choices
    
    # Determine special_max from max constraints
    special_max = 0
    if max_r is not None:
        special_max = max(special_max, int(max_r))
    if max_m is not None:
        special_max = max(special_max, int(max_m))
    
    # Preserve existing data
    pts = existing.get("pts", 0) if existing else 0
    pts_3rd = existing.get("pts_3rd") if existing else None
    n = existing.get("n", 5) if existing else 5
    info = existing.get("info", {}) if existing else {}
    sp_loses_r = existing.get("sp_loses_r", True) if existing else True
    sp_loses_m = existing.get("sp_loses_m", False) if existing else False
    
    result = {
        "pts": pts,
        "n": n,
        "ranged": ranged,
        "melee": melee,
        "innate": innate,
        "specials": specials,
        "special_max": special_max,
        "info": info,
        "sp_loses_r": sp_loses_r,
        "sp_loses_m": sp_loses_m,
    }
    if pts_3rd is not None:
        result["pts_3rd"] = pts_3rd
    return result


def classify_unit_type(unit_name: str, merged_data: dict) -> str:
    """Classify a unit as 'character', 'vehicle', or 'squad'."""
    name_lower = unit_name.lower()
    for u in merged_data.get("units", []):
        if u.get("name", "").lower() != name_lower:
            continue
        prof = u.get("profile") or {}
        keywords = prof.get("keywords", [])
        kw_lower = [k.lower() for k in keywords]
        
        if "character" in kw_lower:
            return "character"
        if any(v in kw_lower for v in ["vehicle", "beast", "monster", "walker"]):
            return "vehicle"
        return "squad"
    return "squad"


def generate_configs_for_faction(slug: str, bsdata_parser: BSDataParser11e,
                                  dry_run: bool = False) -> tuple[int, list[str]]:
    """Generate configs for all units in a faction.
    
    Returns (units_generated, log_lines).
    """
    log = []
    cat_name = SLUG_TO_BSDATA_CAT.get(slug)
    if not cat_name:
        return 0, [f"Unknown slug: {slug}"]
    
    # Load BSData constraints
    bsdata_constraints = bsdata_parser.extract_wargear_constraints(cat_name)
    if not bsdata_constraints:
        return 0, [f"No BSData constraints found for {cat_name}"]
    
    # Load merged data
    merged_path = REPO_ROOT / "data" / "merged" / f"{slug}.json"
    if not merged_path.exists():
        return 0, [f"Merged data not found: {merged_path}"]
    merged_data = load_merged_data(merged_path)
    
    # Load existing config
    config_dir = REPO_ROOT / "data" / "config" / slug
    existing_config = load_existing_config(config_dir) if config_dir.exists() else {}
    
    # Start with EXISTING configs — only update units that have BSData constraints
    characters = dict(existing_config.get("characters.json", {}))
    vehicles = dict(existing_config.get("vehicles.json", {}))
    squads = dict(existing_config.get("squads.json", {}))
    weapon_options = dict(existing_config.get("weapon_options.json", {}))
    
    generated_count = 0
    for unit_name, bsdata_c in bsdata_constraints.items():
        # Skip Legends unless they have existing config
        if "[Legends]" in unit_name:
            existing = get_existing_unit_config(existing_config, unit_name)
            if not existing:
                continue
        
        # Get merged weapons for this unit
        merged_weapons = get_unit_weapons_from_merged(merged_data, unit_name)
        
        # Classify unit type
        unit_type = classify_unit_type(unit_name, merged_data)
        
        # Get existing config
        existing = get_existing_unit_config(existing_config, unit_name)
        
        # Generate config
        if unit_type == "character":
            config = generate_character_config(unit_name, bsdata_c, merged_weapons, existing)
            target_key = unit_name
            for k in characters:
                if k.lower() == unit_name.lower():
                    target_key = k
                    break
            characters[target_key] = config
        elif unit_type == "vehicle":
            config = generate_vehicle_config(unit_name, bsdata_c, merged_weapons, existing)
            # Vehicles go into vehicles.json (flat fallback) AND weapon_options.json (builds)
            target_key = unit_name
            for k in vehicles:
                if k.lower() == unit_name.lower():
                    target_key = k
                    break
            vehicles[target_key] = config
            # weapon_options.json: same builds format
            for k in weapon_options:
                if k.lower() == unit_name.lower():
                    weapon_options[k] = config
                    break
            else:
                weapon_options[unit_name] = config
        else:
            config = generate_squad_config(unit_name, bsdata_c, merged_weapons, existing)
            target_key = unit_name
            for k in squads:
                if k.lower() == unit_name.lower():
                    target_key = k
                    break
            squads[target_key] = config
        
        generated_count += 1
        log.append(f"  Generated: {unit_name} ({unit_type})")
    
    # Write configs
    if not dry_run and config_dir.exists():
        for fname, data in [("characters.json", characters), ("squads.json", squads),
                            ("vehicles.json", vehicles), ("weapon_options.json", weapon_options)]:
            fpath = config_dir / fname
            with open(fpath, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            log.append(f"  Wrote: {fpath} ({len(data)} units)")
    
    return generated_count, log


def main():
    parser = argparse.ArgumentParser(description="Generate configs from BSData")
    parser.add_argument("--faction", "-f", help="Generate for one faction (slug)")
    parser.add_argument("--all", "-a", action="store_true", help="Generate for all factions")
    parser.add_argument("--dry-run", "-d", action="store_true", help="Don't write files")
    args = parser.parse_args()
    
    bsdata_parser = BSDataParser11e(str(REPO_ROOT / "bsdata"))
    
    if args.faction:
        slugs = [args.faction]
    elif args.all:
        slugs = list(SLUG_TO_BSDATA_CAT.keys())
    else:
        print("Usage: python3 generate_configs_from_bsdata.py --faction <slug> | --all")
        sys.exit(1)
    
    total = 0
    for slug in slugs:
        print(f"\n{'='*60}")
        print(f"GENERATING: {slug}")
        print(f"{'='*60}")
        
        count, log = generate_configs_for_faction(slug, bsdata_parser, args.dry_run)
        total += count
        for line in log:
            print(line)
    
    print(f"\n{'='*60}")
    print(f"TOTAL: Generated configs for {total} units across {len(slugs)} factions")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
