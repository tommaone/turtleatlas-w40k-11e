#!/usr/bin/env python3
"""Convert all character flat ranged/melee lists to builds format.

Usage:
    python3 scripts/migrate_characters_to_builds.py [--dry-run] [--force] [--faction NAME]

Idempotent — skips characters that already have builds.
"""

import argparse
import json
import os
import sys
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent / "data" / "config"


def migrate_character(name: str, cfg: dict, force: bool = False) -> bool:
    """Convert a single character from flat lists to builds format.
    Returns True if modified."""
    # Skip if already has builds
    if "weapon_options" in cfg and "builds" in cfg.get("weapon_options", {}):
        if not force:
            return False

    ranged = cfg.get("ranged", [])
    melee = cfg.get("melee", [])
    innate = cfg.get("innate", [])

    if not ranged and not melee:
        return False

    # Create single build with all weapons as fixed
    build = {
        "name": "default",
        "ranged": list(ranged),
        "melee": list(melee),
        "ranged_choices": [],
        "melee_choices": [],
    }

    weapon_options = cfg.get("weapon_options", {})
    weapon_options["builds"] = [build]

    # Remove flat lists (engine reads from builds now)
    cfg["weapon_options"] = weapon_options
    if "ranged" in cfg:
        del cfg["ranged"]
    if "melee" in cfg:
        del cfg["melee"]
    if "innate" in cfg:
        del cfg["innate"]

    return True


def main():
    parser = argparse.ArgumentParser(description="Migrate characters to builds format")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change")
    parser.add_argument("--force", action="store_true", help="Re-migrate even if builds exist")
    parser.add_argument("--faction", type=str, help="Only migrate this faction")
    args = parser.parse_args()

    factions = sorted(
        d.name for d in CONFIG_DIR.iterdir()
        if d.is_dir() and (d / "characters.json").exists()
    )
    if args.faction:
        factions = [args.faction]

    total_migrated = 0
    total_skipped = 0

    for faction in factions:
        fp = CONFIG_DIR / faction / "characters.json"
        with open(fp) as f:
            data = json.load(f)

        migrated = 0
        skipped = 0
        for name, cfg in list(data.items()):
            if name.startswith("_"):
                continue
            if migrate_character(name, cfg, force=args.force):
                migrated += 1
            else:
                skipped += 1

        total_migrated += migrated
        total_skipped += skipped

        if migrated > 0:
            if args.dry_run:
                print(f"  {faction}: would migrate {migrated}, skip {skipped}")
            else:
                with open(fp, "w") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.write("\n")
                print(f"  {faction}: migrated {migrated}, skip {skipped}")

    print(f"\nTotal: migrated={total_migrated} skipped={total_skipped}")
    if args.dry_run:
        print("(dry run — no files modified)")


if __name__ == "__main__":
    main()
