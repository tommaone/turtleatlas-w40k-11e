#!/usr/bin/env python3
"""Fix character weapon choices by querying BSData wargear constraints.

Many characters have all weapons as "fixed" in their builds, but BSData
shows they should have weapon CHOICES (pick 1 ranged from X, pick 1 melee from Y).
This script queries BSData and rebuilds configs with proper choices.

Usage:
    python3 scripts/fix_character_choices.py [--dry-run] [--faction NAME] [--verbose]
"""

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from adapter.bsdata_parser_11e import BSDataParser11e

CONFIG_DIR = PROJECT_ROOT / "data" / "config"
MERGED_DIR = PROJECT_ROOT / "data" / "merged"


def count_fixed(build: dict) -> int:
    """Count total fixed weapons in a build."""
    return len(build.get("ranged", [])) + len(build.get("melee", []))


def count_choices(build: dict) -> int:
    """Count total choice options in a build."""
    rc = sum(len(cl) for cl in build.get("ranged_choices", []))
    mc = sum(len(cl) for cl in build.get("melee_choices", []))
    return rc + mc


def is_suspicious(cfg: dict) -> bool:
    """Character has many fixed weapons and no choices."""
    builds = cfg.get("weapon_options", {}).get("builds", [])
    if len(builds) != 1:
        return False
    build = builds[0]
    return count_fixed(build) > 4 and count_choices(build) == 0


def load_merged_weapon_index(faction_slug: str) -> dict[str, list[dict]]:
    """Load merged data and build a deduplicated weapon profile index.

    Returns: weapon_entry_name (lower) -> [{profile_name, type_name}]
    Deduplicated by profile_name so weapons that appear on multiple units
    only appear once.
    """
    merged_path = MERGED_DIR / f"{faction_slug}.json"
    if not merged_path.exists():
        return {}
    with open(merged_path) as f:
        merged = json.load(f)

    # Collect all profile names per entry
    raw: dict[str, dict[str, dict]] = {}  # entry_key -> profile_key -> {name, type}
    for u in merged.get("units", []):
        prof = u.get("profile")
        if not prof or not isinstance(prof, dict):
            continue
        for w in prof.get("weapons", []):
            entry_key = w.get("name", "").lower()
            for p in w.get("profiles", []):
                pname = p.get("name", "")
                pkey = pname.lower()
                if entry_key not in raw:
                    raw[entry_key] = {}
                raw[entry_key][pkey] = {
                    "profile_name": pname,
                    "type_name": p.get("typeName", ""),
                }
    # Flatten to list (deduplicated)
    return {k: list(v.values()) for k, v in raw.items()}


def resolve_weapon(bsdata_name: str, merged: dict) -> tuple[list[str], list[str]]:
    """Resolve a BSData weapon name to (ranged_profile_names, melee_profile_names).

    Tries: exact match, partial match (key in merged or vice versa),
    splitting on " and " for combined weapons.
    """
    key = bsdata_name.lower()

    def _extract(entry_key: str) -> tuple[list[str], list[str]]:
        ranged, melee = [], []
        for p in merged.get(entry_key, []):
            tn = p["type_name"].lower()
            if "ranged" in tn:
                ranged.append(p["profile_name"])
            elif "melee" in tn:
                melee.append(p["profile_name"])
        return ranged, melee

    # 1. Exact match
    if key in merged:
        return _extract(key)

    # 2. Partial: bsdata key is substring of a merged key
    for mk in merged:
        if key in mk:
            return _extract(mk)

    # 3. Partial: merged key is substring of bsdata key
    for mk in merged:
        if mk in key and len(mk) > 3:
            return _extract(mk)

    # 4. Split on " and "
    if " and " in bsdata_name:
        parts = bsdata_name.split(" and ", 1)
        r_all, m_all = [], []
        for part in parts:
            r, m = resolve_weapon(part.strip(), merged)
            r_all.extend(r)
            m_all.extend(m)
        if r_all or m_all:
            return r_all, m_all

    # 5. No match — skip (weapon not in merged data, would cause KeyError)
    return [], []


def rebuild_build(bsdata_build: dict, char_name: str, merged: dict) -> dict:
    """Rebuild a config build from BSData constraints, resolving weapon names."""
    # Resolve fixed weapons — skip those not in merged data
    fixed_r, fixed_m = [], []
    for w in bsdata_build.get("fixed_ranged", []):
        r, m = resolve_weapon(w, merged)
        fixed_r.extend(r)
    for w in bsdata_build.get("fixed_melee", []):
        r, m = resolve_weapon(w, merged)
        fixed_m.extend(m)

    # Resolve choice lists — split each BSData choice into ranged and melee components
    ranged_choices = []
    melee_choices = []
    for cl in bsdata_build.get("ranged_choices", []):
        cl_r, cl_m = [], []
        for w in cl:
            r, m = resolve_weapon(w, merged)
            cl_r.extend(r)
            cl_m.extend(m)
        if cl_r:
            ranged_choices.append(cl_r)
        if cl_m:
            melee_choices.append(cl_m)
    for cl in bsdata_build.get("melee_choices", []):
        cl_r, cl_m = [], []
        for w in cl:
            r, m = resolve_weapon(w, merged)
            cl_r.extend(r)
            cl_m.extend(m)
        if cl_r:
            ranged_choices.append(cl_r)
        if cl_m:
            melee_choices.append(cl_m)

    result = {
        "name": bsdata_build.get("name", char_name),
        "ranged": fixed_r,
        "melee": fixed_m,
        "ranged_choices": ranged_choices,
        "melee_choices": melee_choices,
    }
    if bsdata_build.get("max_ranged") is not None:
        result["max_ranged"] = bsdata_build["max_ranged"]
    if bsdata_build.get("max_melee") is not None:
        result["max_melee"] = bsdata_build["max_melee"]
    return result


def match_name(config_name: str, bsdata_names: list[str]) -> str | None:
    """Match a config character name to a BSData entry name."""
    if config_name in bsdata_names:
        return config_name
    lower_map = {n.lower(): n for n in bsdata_names}
    if config_name.lower() in lower_map:
        return lower_map[config_name.lower()]
    stripped = config_name.lower().strip()
    for n in bsdata_names:
        if n.lower().strip() == stripped:
            return n
    for n in bsdata_names:
        nl, cl = n.lower(), config_name.lower()
        if nl in cl or cl in nl:
            return n
    return None


def main():
    parser = argparse.ArgumentParser(description="Fix character weapon choices from BSData")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without modifying files")
    parser.add_argument("--faction", type=str, help="Only process this faction")
    parser.add_argument("--verbose", action="store_true", help="Show detailed info for every character")
    args = parser.parse_args()

    bsdata = BSDataParser11e()

    factions = sorted(
        d.name for d in CONFIG_DIR.iterdir()
        if d.is_dir() and (d / "characters.json").exists()
    )
    if args.faction:
        factions = [args.faction]

    total_fixed = 0
    total_left = 0
    total_no_bsdata = 0
    total_no_match = 0
    total_errors = 0
    examples = {}

    for faction_slug in factions:
        fp = CONFIG_DIR / faction_slug / "characters.json"
        with open(fp) as f:
            data = json.load(f)

        merged = load_merged_weapon_index(faction_slug)

        bsdata_faction = bsdata.slug_to_faction(faction_slug)
        if not bsdata_faction:
            print(f"  {faction_slug}: NO BSData faction mapping")
            total_no_bsdata += sum(1 for n in data if not n.startswith("_"))
            continue

        try:
            constraints = bsdata.extract_wargear_constraints(bsdata_faction)
        except Exception as e:
            print(f"  {faction_slug}: ERROR extracting constraints: {e}")
            total_errors += 1
            continue

        if not constraints:
            if args.verbose:
                print(f"  {faction_slug}: no wargear constraints from BSData")
            continue

        bsdata_names = list(constraints.keys())
        faction_fixed = 0
        faction_left = 0
        faction_no_match = 0
        modified = False

        for name, cfg in list(data.items()):
            if name.startswith("_"):
                continue

            if not is_suspicious(cfg):
                faction_left += 1
                continue

            matched_name = match_name(name, bsdata_names)
            if not matched_name:
                faction_no_match += 1
                if args.verbose:
                    fixed = count_fixed(data[name]["weapon_options"]["builds"][0])
                    print(f"    {name}: suspicious ({fixed} fixed) but NO BSData match")
                continue

            bsdata_entry = constraints[matched_name]
            bsdata_builds = bsdata_entry.get("builds", [])

            if not bsdata_builds:
                faction_left += 1
                if args.verbose:
                    fixed = count_fixed(data[name]["weapon_options"]["builds"][0])
                    print(f"    {name}: BSData match but no builds ({fixed} fixed)")
                continue

            has_bsdata_choices = False
            for bb in bsdata_builds:
                if (bb.get("ranged_choices") or bb.get("melee_choices") or
                    bb.get("max_ranged") or bb.get("max_melee")):
                    has_bsdata_choices = True
                    break

            if not has_bsdata_choices:
                faction_left += 1
                if args.verbose:
                    fixed = count_fixed(data[name]["weapon_options"]["builds"][0])
                    print(f"    {name}: BSData match but no choices ({fixed} fixed, legitimately fixed)")
                continue

            old_builds = data[name]["weapon_options"]["builds"]
            new_builds = [rebuild_build(bb, name, merged) for bb in bsdata_builds]

            if name in ("Autarch Wayleaper", "Troupe Master", "Autarch",
                        "Captain", "Lieutenant", "Farseer Skyrunner",
                        "Farseer", "Warlock"):
                examples[name] = {
                    "old": json.dumps(old_builds, indent=2),
                    "new": json.dumps(new_builds, indent=2),
                }

            data[name]["weapon_options"]["builds"] = new_builds
            modified = True
            faction_fixed += 1

            old_fixed = count_fixed(old_builds[0])
            new_fixed = sum(count_fixed(b) for b in new_builds)
            new_choices = sum(count_choices(b) for b in new_builds)
            print(f"    {name}: {old_fixed} fixed → {new_fixed} fixed + {new_choices} choices ({len(new_builds)} build(s))")

        total_fixed += faction_fixed
        total_left += faction_left
        total_no_match += faction_no_match

        if faction_fixed > 0:
            print(f"  {faction_slug}: {faction_fixed} fixed, {faction_left} left as-is, {faction_no_match} no match")

        if modified and not args.dry_run:
            with open(fp, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")
            print(f"  ✅ {faction_slug}: written")
        elif modified and args.dry_run:
            print(f"  {faction_slug}: DRY RUN — would fix {faction_fixed}")

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Characters fixed (had choices in BSData): {total_fixed}")
    print(f"Characters left as-is (legitimately fixed): {total_left}")
    print(f"Characters not found in BSData: {total_no_match}")
    print(f"Errors: {total_errors}")

    if examples:
        print(f"\n{'='*60}")
        print("BEFORE/AFTER EXAMPLES")
        print(f"{'='*60}")
        for name, ex in examples.items():
            print(f"\n--- {name} ---")
            print(f"BEFORE:\n{ex['old']}")
            print(f"AFTER:\n{ex['new']}")

    if args.dry_run:
        print(f"\n(DRY RUN — no files modified)")


if __name__ == "__main__":
    main()
