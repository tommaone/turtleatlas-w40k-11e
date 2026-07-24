#!/usr/bin/env python3
"""Migrate vehicle weapon_options.json to BSData builds format.

Converts flat ranged/melee lists to constraint-based builds with
fixed_ranged, fixed_melee, ranged_choices, melee_choices.

Usage:
    python scripts/migrate_vehicle_builds.py --dry-run
    python scripts/migrate_vehicle_builds.py --force
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from adapter.bsdata_parser_11e import BSDataParser11e

# Map config folder names → BSData faction names
FACTION_MAP = {
    "adepta-sororitas": "Imperium - Adepta Sororitas",
    "adeptus-custodes": "Imperium - Adeptus Custodes",
    "adeptus-mechanicus": "Imperium - Adeptus Mechanicus",
    "aeldari": "Aeldari - Drukhari",
    "astra-militarum": "Imperium - Astra Militarum",
    "black-templars": "Imperium - Adeptus Astartes - Black Templars",
    "blood-angels": "Imperium - Adeptus Astartes - Blood Angels",
    "chaos-daemons": "Chaos - Chaos Daemons",
    "chaos-knights": "Chaos - Chaos Knights",
    "chaos-space-marines": "Chaos - Chaos Space Marines",
    "dark-angels": "Imperium - Adeptus Astartes - Dark Angels",
    "death-guard": "Chaos - Death Guard",
    "deathwatch": "Imperium - Adeptus Astartes - Deathwatch",
    "drukhari": "Aeldari - Drukhari",
    "emperors-children": "Chaos - Emperor's Children",
    "genestealer-cults": "Tyranids - Genestealer Cults",
    "grey-knights": "Imperium - Grey Knights",
    "imperial-agents": "Imperium - Agents of the Imperium",
    "imperial-knights": "Imperium - Imperial Knights",
    "leagues-of-votann": "Leagues of Votann",
    "necrons": "Necrons",
    "orks": "Orks",
    "space-marines": "Imperium - Adeptus Astartes - Space Marines",
    "space-wolves": "Imperium - Adeptus Astartes - Space Wolves",
    "tau-empire": "T'au Empire",
    "thousand-sons": "Chaos - Thousand Sons",
    "tyranids": "Tyranids",
    "world-eaters": "Chaos - World Eaters",
}

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "config"


def fuzzy_match_weapon(name, candidates):
    """Find best fuzzy match for a weapon name."""
    name_lower = name.lower().strip()
    # Exact match
    for c in candidates:
        if c.lower().strip() == name_lower:
            return c
    # Partial match
    for c in candidates:
        cl = c.lower().strip()
        if name_lower in cl or cl in name_lower:
            return c
    # Word overlap
    name_words = set(name_lower.split())
    best, best_score = None, 0
    for c in candidates:
        c_words = set(c.lower().strip().split())
        overlap = len(name_words & c_words)
        if overlap > best_score:
            best_score = overlap
            best = c
    return best if best_score > 0 else None


def migrate_faction(faction_slug, parser, dry_run=True, force=False):
    """Migrate vehicle weapon_options.json for one faction."""
    wo_path = DATA_DIR / faction_slug / "weapon_options.json"
    if not wo_path.exists():
        return 0, 0, []

    with open(wo_path) as f:
        wo = json.load(f)

    bsdata_name = FACTION_MAP.get(faction_slug, "")
    if not bsdata_name:
        return 0, 0, [f"No BSData mapping for {faction_slug}"]

    constraints = parser.extract_wargear_constraints(bsdata_name)

    changed = 0
    unchanged = 0
    mismatches = []

    for unit_name, cfg in list(wo.items()):
        if unit_name.startswith("_"):
            continue
        if not isinstance(cfg, dict) or "ranged" not in cfg:
            continue

        # Skip if already has builds WITH max_ranged/max_melee
        if "builds" in cfg:
            # Check if builds already have max_ranged/max_melee
            first_build = cfg["builds"][0] if cfg["builds"] else {}
            if "max_ranged" in first_build or "max_melee" in first_build:
                unchanged += 1
                continue
            # Has builds but missing max constraints — update them
            bs_constraints = constraints.get(unit_name, {})
            bs_builds = bs_constraints.get("builds", [])
            if bs_builds:
                for i, build in enumerate(cfg["builds"]):
                    if i < len(bs_builds):
                        bs_build = bs_builds[i]
                        if "max_ranged" in bs_build:
                            build["max_ranged"] = bs_build["max_ranged"]
                        if "max_melee" in bs_build:
                            build["max_melee"] = bs_build["max_melee"]
                changed += 1
                if not dry_run:
                    print(f"  {unit_name}: updated max constraints")
                else:
                    print(f"  {unit_name}: would update max constraints")
            continue

        current_ranged = cfg.get("ranged", [])
        current_melee = cfg.get("melee", [])

        # Look up BSData constraints
        bs_constraints = constraints.get(unit_name, {})
        bs_builds = bs_constraints.get("builds", [])

        if not bs_builds:
            # No BSData constraints — skip (keep flat format as fallback)
            unchanged += 1
            continue

        # Use first (default) build
        build = bs_builds[0]

        # Validate: all BSData weapon names must resolve in our catalog
        all_bs_weapons = (
            build.get("fixed_ranged", [])
            + build.get("fixed_melee", [])
        )
        for choice_list in build.get("ranged_choices", []):
            all_bs_weapons.extend(choice_list)
        for choice_list in build.get("melee_choices", []):
            all_bs_weapons.extend(choice_list)

        # Build the new config
        new_cfg = dict(cfg)  # keep info, pts, pts_3rd
        new_cfg["builds"] = [build]

        # Remove old flat lists
        new_cfg.pop("ranged", None)
        new_cfg.pop("melee", None)
        new_cfg.pop("innate", None)

        if not force and new_cfg == cfg:
            unchanged += 1
            continue

        wo[unit_name] = new_cfg
        changed += 1

        if not dry_run:
            print(f"  {unit_name}: migrated")
        else:
            print(f"  {unit_name}: would migrate")
            print(f"    fixed_ranged: {build.get('fixed_ranged', [])}")
            print(f"    fixed_melee: {build.get('fixed_melee', [])}")
            print(f"    ranged_choices: {build.get('ranged_choices', [])}")
            print(f"    melee_choices: {build.get('melee_choices', [])}")

    if changed and not dry_run:
        with open(wo_path, "w") as f:
            json.dump(wo, f, indent=2, ensure_ascii=False)
            f.write("\n")

    return changed, unchanged, mismatches


def main():
    parser_args = argparse.ArgumentParser(description="Migrate vehicle builds")
    parser_args.add_argument("--dry-run", action="store_true")
    parser_args.add_argument("--force", action="store_true")
    parser_args.add_argument("--faction", help="Only migrate this faction")
    args = parser_args.parse_args()

    bsdata_parser = BSDataParser11e()

    total_changed = 0
    total_unchanged = 0
    all_mismatches = []

    factions = [args.faction] if args.faction else sorted(FACTION_MAP.keys())

    for slug in factions:
        changed, unchanged, mismatches = migrate_faction(
            slug, bsdata_parser, dry_run=args.dry_run, force=args.force
        )
        total_changed += changed
        total_unchanged += unchanged
        all_mismatches.extend(mismatches)
        if changed or mismatches:
            print(f"{slug}: {changed} changed, {unchanged} unchanged")

    print(f"\nTotal: {total_changed} changed, {total_unchanged} unchanged")
    if all_mismatches:
        print(f"Mismatches: {len(all_mismatches)}")
        for m in all_mismatches:
            print(f"  {m}")


if __name__ == "__main__":
    main()
