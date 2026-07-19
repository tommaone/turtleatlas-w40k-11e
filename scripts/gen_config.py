#!/usr/bin/env python3
"""
Generate faction config JSONs from merged BSData + MFM data.

Reads:  data/merged/{faction}.json
Writes: data/config/{faction}/{squads,characters,vehicles,weapon_options,notes,supported}.json

Unit classification:
  CHARACTER keyword → characters.json
  VEHICLE keyword  → vehicles.json
  everything else  → squads.json (infantry squads)
  VEHICLE with multiple ranged weapons → also weapon_options.json

Info fields extracted from BSData:
  M, T, SV (from Sv), W, OC, INV (from InSv or rules), deep_strike, FNP (from rules)

Weapon loadout:
  Squads: first ranged = default, first melee = default, remaining ranged = specials
  Characters: all ranged/melee as lists
  Vehicles: all ranged/melee as [{name, unit_name}] lists

Pricing from MFM.
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MERGED_DIR = REPO_ROOT / "data" / "merged"
CONFIG_DIR = REPO_ROOT / "data" / "config"


def parse_stat(val):
    """Parse a stat value: strip quotes, plus signs, asterisks, convert to int where possible."""
    if val is None:
        return None
    s = str(val).strip().replace('"', '').replace('+', '').replace('*', '').replace("'", "")
    # Handle dash (e.g. Aircraft OC '-')
    if s == '-' or s == '':
        return None
    try:
        return int(s)
    except ValueError:
        return s  # Keep as string for non-numeric values like "D6"


def parse_inv_from_rules(rules, stats):
    """Extract invulnerable save from rules list or stats."""
    # Check InSv stat first (BSData format)
    inv_raw = stats.get("InSv") or stats.get("INV")
    if inv_raw:
        inv = parse_stat(inv_raw)
        if isinstance(inv, int) and 2 <= inv <= 6:
            return inv

    # Check rules for invulnerable save
    for rule in rules:
        if isinstance(rule, str) and "invulnerable" in rule.lower():
            m = re.search(r'(\d)\+?', rule)
            if m:
                return int(m.group(1))
    return None


def parse_fnp_from_rules(rules, abilities):
    """Extract Feel No Pain value from rules or abilities."""
    sources = []
    if isinstance(rules, list):
        sources.extend(rules)
    if isinstance(abilities, list):
        for a in abilities:
            if isinstance(a, dict):
                sources.append(a.get("name", "") + " " + a.get("description", ""))
            elif isinstance(a, str):
                sources.append(a)

    for src in sources:
        if not isinstance(src, str):
            continue
        src_lower = src.lower()
        # Match "Feel No Pain X+" or "FNP X+" or "Disgustingly Resilient X+"
        if any(kw in src_lower for kw in ("feel no pain", "fnp", "disgusting resilience", "nurgling resilience")):
            m = re.search(r'(\d)\+', src)
            if m:
                val = int(m.group(1))
                if 2 <= val <= 6:
                    return val
    return None


def extract_info(profile):
    """Extract info{} dict from a BSData profile."""
    if not profile:
        return {}

    stats = profile.get("stats", {})
    rules = profile.get("rules", [])
    abilities = profile.get("abilities", [])

    info = {}

    # Movement
    m = stats.get("M")
    if m:
        info["M"] = str(m).strip()

    # Toughness
    t = parse_stat(stats.get("T"))
    if t is not None:
        info["T"] = t

    # Save — default to 6+ if not present (some units only have invuln)
    sv_raw = stats.get("Sv") or stats.get("SV")
    sv = parse_stat(sv_raw)
    if sv is not None:
        info["SV"] = sv
    else:
        info["SV"] = 6  # fallback: 6+ save

    # Wounds
    w = parse_stat(stats.get("W"))
    if w is not None:
        info["W"] = w

    # OC
    oc = parse_stat(stats.get("OC"))
    if oc is not None:
        info["OC"] = oc

    # Invulnerable save
    inv = parse_inv_from_rules(rules, stats)
    if inv is not None:
        info["INV"] = inv

    # Feel No Pain
    fnp = parse_fnp_from_rules(rules, abilities)
    if fnp is not None:
        info["FNP"] = fnp

    # Deep Strike — from merged unit-level field (set by merge.py)
    # This is handled at the unit level, not profile level

    return info


def get_points(pricing, models=1):
    """Extract base points from MFM pricing data."""
    if not pricing:
        return None
    for tier in pricing:
        for cost in tier.get("costs", []):
            if cost.get("models") == models:
                return cost.get("points")
    # Fallback: first cost
    if pricing:
        for cost in pricing[0].get("costs", []):
            return cost.get("points")
    return None


def get_squad_size(pricing):
    """Get default squad size from pricing."""
    if not pricing:
        return 5  # default
    for tier in pricing:
        for cost in tier.get("costs", []):
            return cost.get("models", 5)
    return 5


def classify_unit(keywords):
    """Classify unit type from keywords."""
    kw_upper = [k.upper() for k in keywords]
    is_char = "CHARACTER" in kw_upper
    is_vehicle = "VEHICLE" in kw_upper
    is_monster = "MONSTER" in kw_upper
    is_fortification = "FORTIFICATION" in kw_upper
    is_infantry = "INFANTRY" in kw_upper
    return {
        "is_character": is_char,
        "is_vehicle": is_vehicle or is_monster,
        "is_infantry": is_infantry,
        "is_fortification": is_fortification,
    }


def get_faction_keyword(faction_slug):
    """Determine the faction keyword for filtering (e.g. 'Faction: Chaos Knights')."""
    # Map slugs to expected faction keywords
    FACTION_KEYWORD_MAP = {
        "chaos-knights": "Faction: Chaos Knights",
        "chaos-daemons": "Faction: Legiones Daemonica",
        "space-marines": "Faction: Adeptus Astartes",
        "dark-angels": "Faction: Adeptus Astartes",
        "grey-knights": "Faction: Grey Knights",
        "death-guard": "Faction: Death Guard",
        "thousand-sons": "Faction: Thousand Sons",
        "world-eaters": "Faction: World Eaters",
        "chaos-space-marines": "Faction: Heretic Astartes",
        "imperial-knights": "Faction: Imperial Knights",
        "adepta-sororitas": "Faction: Adepta Sororitas",
        "adeptus-custodes": "Faction: Adeptus Custodes",
        "adeptus-mechanicus": "Faction: Adeptus Mechanicus",
        "astra-militarum": "Faction: Astra Militarum",
        "aeldari": "Faction: Asuryani",
        "drukhari": "Faction: Drukhari",
        "necrons": "Faction: Necrons",
        "orks": "Faction: Orks",
        "tau-empire": "Faction: T\u2019au Empire",
        "tyranids": "Faction: Tyranids",
        "genestealer-cults": "Faction: Genestealer Cults",
        "leagues-of-votann": "Faction: Leagues of Votann",
        "black-templars": "Faction: Adeptus Astartes",
        "blood-angels": "Faction: Adeptus Astartes",
        "space-wolves": "Faction: Adeptus Astartes",
        "deathwatch": "Faction: Adeptus Astartes",
        "imperial-agents": "Faction: Agents of the Imperium",
        "chaos-titan-legions": "Faction: Chaos Titan Legions",
        "titan-legions": "Faction: Titan Legions",
        "emperors-children": "Faction: Emperor\u2019s Children",
    }
    return FACTION_KEYWORD_MAP.get(faction_slug)


def gen_supported_json(faction_slug, data):
    """Generate supported.json from merged data (dispositions from MFM detachments)."""
    # Faction display name
    faction_name = data.get("faction_name", faction_slug.replace("-", " ").title())

    # Faction keyword
    faction_kw = get_faction_keyword(faction_slug)
    keywords = [faction_kw] if faction_kw else []

    # Detachments → dispositions mapping
    dispositions = {}
    for det in data.get("detachments", []):
        det_name = det.get("name", "")
        obj = det.get("objective", "")
        if det_name and obj:
            det_key = det_name.lower().replace(" ", "-").replace("'", "").replace("'", "")
            disp_key = obj.lower().replace(" ", "-")
            dispositions[det_key] = disp_key

    return {
        "_extends": "_base",
        "_note": f"{faction_name} config — auto-generated from BSData + MFM",
        "_source": "BSData 11e + MFM (auto-generated)",
        "key": faction_slug,
        "name": faction_name,
        "keywords": keywords,
        "dispositions": dispositions,
    }


def extract_weapons(profile):
    """Extract weapon names grouped by type (ranged vs melee)."""
    if not profile:
        return [], []

    weapons = profile.get("weapons", [])
    ranged_names = []
    melee_names = []
    seen_ranged = set()
    seen_melee = set()

    for weapon_group in weapons:
        group_name = weapon_group.get("name", "")
        for wp in weapon_group.get("profiles", []):
            wp_name = wp.get("name", "")
            # Strip leading unicode arrows (➤, ►, ▸) from BSData weapon names
            for prefix in ("\u27A4", "\u25BA", "\u25B8"):
                if wp_name.startswith(prefix):
                    wp_name = wp_name[len(prefix):].lstrip()
            stats = wp.get("stats", {})
            range_val = stats.get("Range", "")

            if range_val == "Melee" or not range_val:
                if wp_name not in seen_melee:
                    melee_names.append(wp_name)
                    seen_melee.add(wp_name)
            else:
                if wp_name not in seen_ranged:
                    ranged_names.append(wp_name)
                    seen_ranged.add(wp_name)

    return ranged_names, melee_names


def gen_squad_config(name, unit, pricing_data):
    """Generate squad config entry."""
    profile = unit.get("profile") or {}
    info = extract_info(profile)
    deep_strike = unit.get("deep_strike", False)
    if deep_strike:
        info["deep_strike"] = True

    pricing = unit.get("pricing")
    n = get_squad_size(pricing)
    pts = get_points(pricing, n)
    if pts is None:
        pts = 0

    ranged_names, melee_names = extract_weapons(profile)

    # Default loadout: first ranged, first melee
    default_ranged = ranged_names[0] if ranged_names else None
    default_melee = melee_names[0] if melee_names else "Close combat weapon"

    # Specials: remaining ranged weapons
    specials = ranged_names[1:] if len(ranged_names) > 1 else []

    entry = {
        "n": n,
        "pts": pts,
        "ranged": default_ranged,
        "melee": default_melee,
        "special_max": min(len(specials), 2),  # reasonable default
        "specials": specials,
        "sp_loses_r": False,
        "sp_loses_m": False,
        "apoth_loses_r": False,
        "innate": [],
        "info": info,
    }
    return entry


def gen_character_config(name, unit, pricing_data):
    """Generate character config entry."""
    profile = unit.get("profile") or {}
    info = extract_info(profile)
    deep_strike = unit.get("deep_strike", False)
    if deep_strike:
        info["deep_strike"] = True

    pricing = unit.get("pricing")
    pts = get_points(pricing, 1)
    if pts is None:
        pts = 0

    ranged_names, melee_names = extract_weapons(profile)

    entry = {
        "pts": pts,
        "ranged": ranged_names,
        "melee": melee_names,
        "innate": [],
        "info": info,
    }
    return entry


def gen_vehicle_config(name, unit, pricing_data):
    """Generate vehicle config entry."""
    profile = unit.get("profile") or {}
    info = extract_info(profile)
    deep_strike = unit.get("deep_strike", False)
    if deep_strike:
        info["deep_strike"] = True

    pricing = unit.get("pricing")
    pts = get_points(pricing, 1)
    if pts is None:
        pts = 0

    ranged_names, melee_names = extract_weapons(profile)

    # Vehicle format: [{name, unit_name}]
    ranged = [{"name": n, "unit_name": name} for n in ranged_names]
    melee = [{"name": n, "unit_name": name} for n in melee_names]

    entry = {
        "pts": pts,
        "ranged": ranged,
        "melee": melee,
        "innate": [],
        "info": info,
    }
    return entry


def gen_weapon_options(name, unit, pricing_data):
    """Generate weapon_options entry if unit has multiple ranged weapons."""
    profile = unit.get("profile") or {}
    info = extract_info(profile)
    deep_strike = unit.get("deep_strike", False)
    if deep_strike:
        info["deep_strike"] = True

    ranged_names, melee_names = extract_weapons(profile)

    # Only generate if there are actual weapon options
    if len(ranged_names) <= 1 and len(melee_names) <= 1:
        return None

    entry = {
        "ranged": ranged_names,
        "melee": melee_names,
        "info": info,
    }
    return entry


def generate_faction_config(faction_slug, dry_run=False, skip_existing=False):
    """Generate all config files for a faction."""
    merged_path = MERGED_DIR / f"{faction_slug}.json"
    if not merged_path.exists():
        print(f"  SKIP: no merged data for {faction_slug}")
        return

    # Skip if config already exists and skip_existing is set
    faction_dir = CONFIG_DIR / faction_slug
    if skip_existing and faction_dir.exists():
        # Check if any config files exist
        existing = list(faction_dir.glob("*.json"))
        if existing:
            print(f"  SKIP: {faction_slug} already has config ({len(existing)} files)")
            return

    data = json.loads(merged_path.read_text())
    units = data.get("units", [])

    # Filter: use in_mfm as primary (MFM lists only faction-specific units)
    # For units only in BSData, check faction keyword
    faction_kw = get_faction_keyword(faction_slug)

    # Classify units
    squads = {}
    characters = {}
    vehicles = {}
    weapon_options = {}
    skipped = 0

    for unit in units:
        name = unit.get("name", "")
        profile = unit.get("profile")

        # Skip units without profile or without stats (empty stats = no M/T/SV/W/OC)
        if not profile:
            skipped += 1
            continue
        stats = profile.get("stats", {})
        if not stats or not stats.get("T"):
            skipped += 1
            continue

        # Skip Legends and Crucible
        if "[Legends]" in name or "[Crucible]" in name:
            skipped += 1
            continue

        # Filter: must be in MFM, or match faction keyword if BSData-only
        in_mfm = unit.get("in_mfm", False)
        in_bsdata = unit.get("in_bsdata", False)
        keywords = profile.get("keywords", [])

        if not in_mfm:
            # BSData-only: check faction keyword
            kw_upper = [k.upper() for k in keywords]
            if faction_kw and faction_kw.upper() not in kw_upper:
                skipped += 1
                continue
        cls = classify_unit(keywords)

        # Skip Fortifications
        if cls["is_fortification"]:
            skipped += 1
            continue

        if cls["is_character"]:
            characters[name] = gen_character_config(name, unit, data)
        elif cls["is_vehicle"]:
            vehicles[name] = gen_vehicle_config(name, unit, data)
            # Also check for weapon options
            wo = gen_weapon_options(name, unit, data)
            if wo:
                weapon_options[name] = wo
        else:
            squads[name] = gen_squad_config(name, unit, data)

    if dry_run:
        print(f"  {faction_slug}: {len(squads)} squads, {len(characters)} chars, "
              f"{len(vehicles)} vehicles, {len(weapon_options)} weapon_opts, {skipped} skipped")
        return

    # Write config files
    faction_dir = CONFIG_DIR / faction_slug
    faction_dir.mkdir(parents=True, exist_ok=True)

    # squads.json (always create, even if empty)
    squads_data = {"_note": f"{faction_slug} squads — generated from BSData + MFM",
                   "_source": "BSData 11e + MFM (auto-generated)"}
    squads_data.update(squads)
    (faction_dir / "squads.json").write_text(
        json.dumps(squads_data, indent=2, ensure_ascii=False) + "\n")

    # characters.json
    if characters:
        chars_data = {"_note": f"{faction_slug} characters — generated from BSData + MFM",
                      "_source": "BSData 11e + MFM (auto-generated)"}
        chars_data.update(characters)
        (faction_dir / "characters.json").write_text(
            json.dumps(chars_data, indent=2, ensure_ascii=False) + "\n")

    # vehicles.json
    if vehicles:
        veh_data = {"_note": f"{faction_slug} vehicles — generated from BSData + MFM",
                    "_source": "BSData 11e + MFM (auto-generated)"}
        veh_data.update(vehicles)
        (faction_dir / "vehicles.json").write_text(
            json.dumps(veh_data, indent=2, ensure_ascii=False) + "\n")

    # weapon_options.json
    if weapon_options:
        wo_data = {"_note": f"{faction_slug} weapon options — generated from BSData + MFM",
                   "_source": "BSData 11e + MFM (auto-generated)"}
        wo_data.update(weapon_options)
        (faction_dir / "weapon_options.json").write_text(
            json.dumps(wo_data, indent=2, ensure_ascii=False) + "\n")

    # notes.json (empty)
    notes_path = faction_dir / "notes.json"
    if not notes_path.exists():
        notes_path.write_text("{}\n")

    # supported.json (dispositions, keywords, etc.)
    supported_path = faction_dir / "supported.json"
    if not supported_path.exists():
        supported = gen_supported_json(faction_slug, data)
        supported_path.write_text(
            json.dumps(supported, indent=2, ensure_ascii=False) + "\n")

    print(f"  {faction_slug}: {len(squads)} squads, {len(characters)} chars, "
          f"{len(vehicles)} vehicles, {len(weapon_options)} weapon_opts, {skipped} skipped")


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Generate faction config from merged BSData + MFM")
    ap.add_argument("--faction", type=str, help="Single faction slug")
    ap.add_argument("--all", action="store_true", help="Generate for all factions with merged data")
    ap.add_argument("--dry-run", action="store_true", help="Show stats without writing")
    ap.add_argument("--skip-existing", action="store_true", help="Skip factions that already have config")
    ap.add_argument("--list", action="store_true", help="List available factions")
    args = ap.parse_args()

    if args.list:
        for f in sorted(MERGED_DIR.glob("*.json")):
            print(f.stem)
        return

    if args.faction:
        generate_faction_config(args.faction, dry_run=args.dry_run, skip_existing=args.skip_existing)
    elif args.all:
        for f in sorted(MERGED_DIR.glob("*.json")):
            slug = f.stem
            generate_faction_config(slug, dry_run=args.dry_run, skip_existing=args.skip_existing)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
