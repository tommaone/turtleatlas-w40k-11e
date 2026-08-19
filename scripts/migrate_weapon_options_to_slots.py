#!/usr/bin/env python3
"""Migrate weapon_options.json from legacy builds schema to slots.

Legacy build schema (weapon_options.json):
    {fixed_ranged: [str], fixed_melee: [str],
     ranged_choices: [[str], ...], melee_choices: [[str], ...],
     max_ranged: int|None, max_melee: int|None, name: str}

New slots schema (what the roadmap's "slot setup" requires):
    {name: str,
     fixed: [{name, type: "ranged"|"melee"}],
     slots: [{name, choices: [{name, type}]}],
     no_duplicates: bool?}

Conversion semantics:
  - fixed_ranged + fixed_melee -> fixed entries typed by slot
  - ranged_choices, no max -> one slot per list
  - ranged_choices, max=N -> N slots over the deduped union + no_duplicates
  - Same rules for melee_choices
  - Empty choice lists skipped

Also handles the character-envelope format (weapon_options.builds[]) by
detecting and unwrapping it.

Usage:
    python3 scripts/migrate_weapon_options_to_slots.py [--dry-run] [--faction NAME]
Idempotent: skips builds that already have the slots schema.
"""
import argparse
import json
import sys
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent / "data" / "config"


def _dedupe_ordered(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out


def convert_build(build: dict) -> dict:
    """Convert ONE legacy weapon_options build to the slots schema."""
    if "slots" in build and "fixed" in build:
        return build  # already new format

    fixed = [{"name": w, "type": "ranged"} for w in build.get("fixed_ranged", [])]
    fixed += [{"name": w, "type": "melee"} for w in build.get("fixed_melee", [])]

    slots = []
    no_duplicates = False

    # Ranged choices
    rc = build.get("ranged_choices") or []
    if rc:
        max_r = build.get("max_ranged")
        if max_r is None:
            for i, cl in enumerate(rc):
                if not cl:
                    continue
                slots.append({
                    "name": f"Ranged weapon {i + 1}",
                    "choices": [{"name": w, "type": "ranged"} for w in cl],
                })
        else:
            union = _dedupe_ordered([w for cl in rc for w in cl])
            n = min(max_r, len(union))
            if n >= 1:
                if n > 1:
                    no_duplicates = True
                for i in range(n):
                    slots.append({
                        "name": f"Ranged weapon {i + 1}",
                        "choices": [{"name": w, "type": "ranged"} for w in union],
                    })

    # Melee choices
    mc = build.get("melee_choices") or []
    if mc:
        max_m = build.get("max_melee")
        if max_m is None:
            for i, cl in enumerate(mc):
                if not cl:
                    continue
                slots.append({
                    "name": f"Melee weapon {i + 1}",
                    "choices": [{"name": w, "type": "melee"} for w in cl],
                })
        else:
            union = _dedupe_ordered([w for cl in mc for w in cl])
            n = min(max_m, len(union))
            if n >= 1:
                if n > 1:
                    no_duplicates = True
                for i in range(n):
                    slots.append({
                        "name": f"Melee weapon {i + 1}",
                        "choices": [{"name": w, "type": "melee"} for w in union],
                    })

    out = {"name": build.get("name", "default"), "fixed": fixed, "slots": slots}
    if no_duplicates:
        out["no_duplicates"] = True
    return out


def convert_weapon_options_file(data: dict) -> int:
    """Convert all builds in a weapon_options.json file. Returns count changed."""
    changed = 0
    for name, unit_data in data.items():
        if name.startswith("_"):
            continue

        builds = unit_data.get("builds")
        if builds is None:
            # Check for character-envelope: weapon_options.builds
            wo = unit_data.get("weapon_options", {})
            builds = wo.get("builds")
            if builds is None:
                continue

        new_builds = []
        unit_changed = False
        for b in builds:
            nb = convert_build(b)
            if nb is not b:
                unit_changed = True
            new_builds.append(nb)

        if unit_changed:
            changed += 1
            if "weapon_options" in unit_data and "builds" in unit_data.get("weapon_options", {}):
                unit_data["weapon_options"]["builds"] = new_builds
            else:
                unit_data["builds"] = new_builds

    return changed


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--faction", type=str,
                    help="Single faction directory name (e.g. 'world-eaters')")
    args = ap.parse_args()

    if args.faction:
        factions = [args.faction]
    else:
        factions = sorted(
            d.name for d in CONFIG_DIR.iterdir()
            if d.is_dir() and (d / "weapon_options.json").exists()
        )

    total = 0
    for faction in factions:
        fp = CONFIG_DIR / faction / "weapon_options.json"
        if not fp.exists():
            print(f"  SKIP {faction}: no weapon_options.json")
            continue

        data = json.load(open(fp))
        changed = convert_weapon_options_file(data)
        if changed:
            total += changed
            print(f"{faction}: {changed} builds converted")
            if not args.dry_run:
                fp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    print(f"\ntotal builds converted: {total}")


if __name__ == "__main__":
    main()
