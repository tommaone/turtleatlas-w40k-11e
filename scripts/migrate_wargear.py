#!/usr/bin/env python3
"""Migrate wargear build constraints from BSData to characters.json.

For each faction, calls extract_wargear_constraints() with the correct
BSData catalogue name, maps extracted builds to our characters.json format,
and adds weapon_options.builds to each affected character.

Idempotent: running twice produces the same result.
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from adapter.bsdata_parser_11e import BSDataParser11e

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

FACTION_MAP = {
    "space-marines": "Imperium - Adeptus Astartes - Space Marines",
    "grey-knights": "Imperium - Grey Knights",
    "orks": "Xenos - Orks",
    "necrons": "Xenos - Necrons",
    "aeldari": "Xenos - Aeldari",
    "drukhari": "Xenos - Drukhari",
    "tyranids": "Xenos - Tyranids",
    "tau-empire": "Xenos - T'au Empire",
    "leagues-of-votann": "Xenos - Leagues of Votann",
    "genestealer-cults": "Xenos - Genestealer Cults",
    "astra-militarum": "Imperium - Astra Militarum",
    "adepta-sororitas": "Imperium - Adepta Sororitas",
    "adeptus-custodes": "Imperium - Adeptus Custodes",
    "adeptus-mechanicus": "Imperium - Adeptus Mechanicus",
    "imperial-knights": "Imperium - Imperial Knights",
    "imperial-agents": "Imperium - Agents of the Imperium",
    "chaos-space-marines": "Chaos - Chaos Space Marines",
    "chaos-knights": "Chaos - Chaos Knights",
    "chaos-daemons": "Chaos - Chaos Daemons",
    "death-guard": "Chaos - Death Guard",
    "thousand-sons": "Chaos - Thousand Sons",
    "world-eaters": "Chaos - World Eaters",
    "emperors-children": "Chaos - Emperor's Children",
    "black-templars": "Imperium - Adeptus Astartes - Black Templars",
    "blood-angels": "Imperium - Adeptus Astartes - Blood Angels",
    "dark-angels": "Imperium - Adeptus Astartes - Dark Angels",
    "space-wolves": "Imperium - Adeptus Astartes - Space Wolves",
    "deathwatch": "Imperium - Adeptus Astartes - Deathwatch",
    "chaos-titan-legions": "Chaos - Titanicus Traitoris",
    "titan-legions": "Imperium - Adeptus Titanicus",
}


# ---------------------------------------------------------------------------
# Weapon name normalization
# ---------------------------------------------------------------------------

def normalize_weapon_name(name: str) -> str:
    """Normalize weapon name for fuzzy matching."""
    s = name.lower().strip()
    s = s.replace("\u2019", "'").replace("\u2018", "'")
    s = s.replace("-", " ")
    s = re.sub(r"\s+", " ", s)
    return s


def find_config_weapon(bsdata_name: str, config_weapons: list[str]) -> tuple[int, str] | tuple[None, None]:
    """Find matching weapon in config by fuzzy name match.

    Returns (index, original_config_name) or (None, None).
    """
    target = normalize_weapon_name(bsdata_name)
    if not target:
        return None, None

    # Exact normalized match
    for i, w in enumerate(config_weapons):
        if normalize_weapon_name(w) == target:
            return i, w

    # Prefix/substring match (e.g. "master-crafted power weapon" matches
    # "Master-crafted power weapon")
    for i, w in enumerate(config_weapons):
        wn = normalize_weapon_name(w)
        if not wn:
            continue
        if target.startswith(wn) or wn.startswith(target):
            return i, w

    # Containment match (handles "Smite" → "Smite - Focused Witchfire")
    # Only match if the shorter string is >= 3 chars to avoid false positives
    for i, w in enumerate(config_weapons):
        wn = normalize_weapon_name(w)
        if not wn:
            continue
        shorter = min(len(target), len(wn))
        if shorter >= 3 and (target in wn or wn in target):
            return i, w

    return None, None


# ---------------------------------------------------------------------------
# Character name matching
# ---------------------------------------------------------------------------

def normalize_char_name(name: str) -> str:
    """Normalize character name for case-insensitive matching."""
    return name.lower().strip().replace("\u2019", "'")


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------

def migrate_faction(
    faction_dir: Path,
    parser: BSDataParser11e,
    bsdata_name: str,
    *,
    dry_run: bool = False,
    force: bool = False,
) -> dict:
    """Migrate one faction's characters.json with wargear builds.

    Returns summary dict.
    """
    chars_path = faction_dir / "characters.json"
    if not chars_path.exists():
        return {"skipped": True, "reason": "no characters.json"}

    with open(chars_path, encoding="utf-8") as f:
        chars = json.load(f)

    # Extract wargear constraints from BSData
    wargear = parser.extract_wargear_constraints(bsdata_name)
    if not wargear:
        return {"skipped": True, "reason": "no wargear data from BSData"}

    # Build case-insensitive map of BSData characters
    bs_map: dict[str, dict] = {}
    for bs_char_name, bs_data in wargear.items():
        key = normalize_char_name(bs_char_name)
        bs_map[key] = {"name": bs_char_name, "data": bs_data}

    # Collect all valid weapon names for this faction from config files.
    # Filter out single-char entries (pre-existing bug in squads.json where
    # some weapon strings are split into individual characters).
    MIN_WEAPON_LEN = 3
    config_weapon_names: set[str] = set()
    for fname in ("characters.json", "squads.json", "vehicles.json", "weapon_options.json"):
        fpath = faction_dir / fname
        if not fpath.exists():
            continue
        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)
        for unit_name, unit_data in data.items():
            if unit_name.startswith("_"):
                continue
            if not isinstance(unit_data, dict):
                continue
            for w in unit_data.get("ranged", []) or []:
                if isinstance(w, str) and len(w.strip()) >= MIN_WEAPON_LEN:
                    config_weapon_names.add(w)
            for w in unit_data.get("melee", []) or []:
                if isinstance(w, str) and len(w.strip()) >= MIN_WEAPON_LEN:
                    config_weapon_names.add(w)

    config_weapon_list = sorted(config_weapon_names)

    # Process each character in config
    updated = 0
    skipped_existing = 0
    skipped_no_match = 0
    weapon_mismatches: list[str] = []

    for char_name, char_data in list(chars.items()):
        if char_name.startswith("_"):
            continue
        if not isinstance(char_data, dict):
            continue

        # Skip if already has weapon_options (unless --force)
        if "weapon_options" in char_data and not force:
            skipped_existing += 1
            continue

        # Find matching BSData character
        char_key = normalize_char_name(char_name)
        bs_match = bs_map.get(char_key)
        if bs_match is None:
            skipped_no_match += 1
            continue

        bs_data = bs_match["data"]
        bs_char_name = bs_match["name"]

        # Build the weapon_options.builds list
        builds = []
        for build in bs_data["builds"]:
            mapped_ranged: list[str] = []
            mapped_melee: list[str] = []
            mapped_ranged_choices: list[list[str]] = []
            mapped_melee_choices: list[list[str]] = []

            # Map fixed ranged weapons
            for wname in build["fixed_ranged"]:
                idx, cfg_name = find_config_weapon(wname, config_weapon_list)
                if cfg_name is not None:
                    if cfg_name not in mapped_ranged:
                        mapped_ranged.append(cfg_name)
                else:
                    # Use BSData name if no config match
                    if wname not in mapped_ranged:
                        mapped_ranged.append(wname)
                    weapon_mismatches.append(f"{char_name}: ranged '{wname}' not in config")

            # Map fixed melee weapons
            for wname in build["fixed_melee"]:
                idx, cfg_name = find_config_weapon(wname, config_weapon_list)
                if cfg_name is not None:
                    if cfg_name not in mapped_melee:
                        mapped_melee.append(cfg_name)
                else:
                    if wname not in mapped_melee:
                        mapped_melee.append(wname)
                    weapon_mismatches.append(f"{char_name}: melee '{wname}' not in config")

            # Map ranged choice groups
            for group in build["ranged_choices"]:
                mapped_group = []
                for wname in group:
                    if not wname or not wname.strip():
                        continue  # skip empty/whitespace-only BSData entries
                    idx, cfg_name = find_config_weapon(wname, config_weapon_list)
                    mapped_group.append(cfg_name if cfg_name else wname)
                if mapped_group:
                    mapped_ranged_choices.append(mapped_group)

            # Map melee choice groups
            for group in build["melee_choices"]:
                mapped_group = []
                for wname in group:
                    if not wname or not wname.strip():
                        continue  # skip empty/whitespace-only BSData entries
                    idx, cfg_name = find_config_weapon(wname, config_weapon_list)
                    mapped_group.append(cfg_name if cfg_name else wname)
                if mapped_group:
                    mapped_melee_choices.append(mapped_group)

            entry: dict = {"name": build["name"]}
            if mapped_ranged:
                entry["ranged"] = mapped_ranged
            else:
                entry["ranged"] = []
            if mapped_melee:
                entry["melee"] = mapped_melee
            else:
                entry["melee"] = []
            if mapped_ranged_choices:
                entry["ranged_choices"] = mapped_ranged_choices
            if mapped_melee_choices:
                entry["melee_choices"] = mapped_melee_choices

            builds.append(entry)

        if builds:
            char_data["weapon_options"] = {"builds": builds}
            updated += 1

    # Write back
    if not dry_run and updated > 0:
        with open(chars_path, "w", encoding="utf-8") as f:
            json.dump(chars, f, indent=2, ensure_ascii=False)
            f.write("\n")

    return {
        "updated": updated,
        "skipped_existing": skipped_existing,
        "skipped_no_match": skipped_no_match,
        "weapon_mismatches": weapon_mismatches,
        "total_builds": sum(
            len(char_data.get("weapon_options", {}).get("builds", []))
            for char_name, char_data in chars.items()
            if not char_name.startswith("_") and isinstance(char_data, dict)
        ),
    }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_faction(faction_dir: Path) -> list[str]:
    """Verify all weapon names in builds exist in the faction's weapon catalog."""
    chars_path = faction_dir / "characters.json"
    if not chars_path.exists():
        return []

    with open(chars_path, encoding="utf-8") as f:
        chars = json.load(f)

    # Collect all valid weapon names
    valid_weapons: set[str] = set()
    for fname in ("characters.json", "squads.json", "vehicles.json", "weapon_options.json"):
        fpath = faction_dir / fname
        if not fpath.exists():
            continue
        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)
        for unit_name, unit_data in data.items():
            if unit_name.startswith("_"):
                continue
            if not isinstance(unit_data, dict):
                continue
            for w in unit_data.get("ranged", []) or []:
                if isinstance(w, str):
                    valid_weapons.add(normalize_weapon_name(w))
            for w in unit_data.get("melee", []) or []:
                if isinstance(w, str):
                    valid_weapons.add(normalize_weapon_name(w))
            # Also check weapon_options.builds
            for build in unit_data.get("weapon_options", {}).get("builds", []):
                for w in build.get("ranged", []):
                    if isinstance(w, str):
                        valid_weapons.add(normalize_weapon_name(w))
                for w in build.get("melee", []):
                    if isinstance(w, str):
                        valid_weapons.add(normalize_weapon_name(w))

    errors = []
    for char_name, char_data in chars.items():
        if char_name.startswith("_"):
            continue
        if not isinstance(char_data, dict):
            continue
        for build in char_data.get("weapon_options", {}).get("builds", []):
            for w in build.get("ranged", []):
                if normalize_weapon_name(w) not in valid_weapons:
                    errors.append(f"{char_name}/{build['name']}: ranged '{w}' not in any config file")
            for w in build.get("melee", []):
                if normalize_weapon_name(w) not in valid_weapons:
                    errors.append(f"{char_name}/{build['name']}: melee '{w}' not in any config file")

    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def discover_bsdata_name(parser: BSDataParser11e, faction_dir_name: str) -> str | None:
    """Discover BSData catalogue name for a faction directory name.

    Uses the same slug_to_faction mapping as the parser, with FACTION_MAP
    override for known slugs.
    """
    if faction_dir_name in FACTION_MAP:
        target = FACTION_MAP[faction_dir_name]
        for f in parser.list_factions():
            if f.lower() == target.lower():
                return f
        return None

    # Fallback: use parser's slug_to_faction
    return parser.slug_to_faction(faction_dir_name)


def main():
    import argparse

    parser_cli = argparse.ArgumentParser(description="Migrate wargear builds to characters.json")
    parser_cli.add_argument("--dry-run", action="store_true", help="Don't write files")
    parser_cli.add_argument("--force", action="store_true", help="Re-process characters that already have weapon_options")
    parser_cli.add_argument("--factions", nargs="*", help="Only process these faction slugs")
    args = parser_cli.parse_args()

    parser = BSDataParser11e()
    config_dir = REPO_ROOT / "data" / "config"

    total_updated = 0
    total_mismatches = 0
    total_errors = 0

    factions_to_process = args.factions or sorted(
        d.name for d in config_dir.iterdir()
        if d.is_dir() and (d / "characters.json").exists()
    )

    for faction_slug in factions_to_process:
        faction_dir = config_dir / faction_slug
        if not faction_dir.is_dir():
            continue
        if not (faction_dir / "characters.json").exists():
            continue

        bsdata_name = discover_bsdata_name(parser, faction_slug)
        if bsdata_name is None:
            print(f"  SKIP {faction_slug}: no BSData catalogue found")
            continue

        print(f"\n{'='*60}")
        print(f"  {faction_slug} → {bsdata_name}")
        print(f"{'='*60}")

        result = migrate_faction(faction_dir, parser, bsdata_name, dry_run=args.dry_run, force=args.force)

        if result.get("skipped"):
            print(f"  Skipped: {result['reason']}")
            continue

        print(f"  Characters updated:  {result['updated']}")
        print(f"  Skipped (existing):  {result['skipped_existing']}")
        print(f"  Skipped (no match):  {result['skipped_no_match']}")
        print(f"  Total builds:        {result['total_builds']}")
        if result["weapon_mismatches"]:
            print(f"  Weapon mismatches:   {len(result['weapon_mismatches'])}")
            for m in result["weapon_mismatches"][:10]:
                print(f"    - {m}")
            if len(result["weapon_mismatches"]) > 10:
                print(f"    ... and {len(result['weapon_mismatches']) - 10} more")

        total_updated += result["updated"]
        total_mismatches += len(result["weapon_mismatches"])

        # Validate
        if not args.dry_run:
            errors = validate_faction(faction_dir)
            if errors:
                print(f"  Validation errors:   {len(errors)}")
                for e in errors[:10]:
                    print(f"    - {e}")
                if len(errors) > 10:
                    print(f"    ... and {len(errors) - 10} more")
                total_errors += len(errors)

    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  Total characters updated:  {total_updated}")
    print(f"  Total weapon mismatches:   {total_mismatches}")
    if not args.dry_run:
        print(f"  Total validation errors:   {total_errors}")
    print(f"  Dry run:                   {args.dry_run}")


if __name__ == "__main__":
    main()
