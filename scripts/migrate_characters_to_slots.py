#!/usr/bin/env python3
"""Convert character weapon_options.builds from the legacy schema to slots.

Legacy build schema:
    {ranged: [str], melee: [str],
     ranged_choices: [[str], ...], melee_choices: [[str], ...],
     max_ranged: int|None, max_melee: int|None, name: str}

New slots schema (what the roadmap's "slot setup" requires):
    {name: str,
     fixed: [{name, type: "ranged"|"melee"}],
     slots: [{name, choices: [{name, type, count?}]}],
     no_duplicates: bool?}

Conversion semantics (must match the legacy resolver exactly):
  - fixed weapons -> `fixed` entries typed by slot.
  - choice lists, no max -> one slot per list (legacy product(*lists)).
  - choice lists, max=N -> N slots over the DEDUPED union of all lists
    + no_duplicates (legacy combinations(union, min(N, len(union)))).
    max=1 is the common case -> one slot over the union.
  - no_duplicates is emitted only when N > 1 (needed to forbid repeats).

Usage:
    python3 scripts/migrate_characters_to_slots.py [--dry-run] [--faction NAME]
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
    """Convert ONE legacy character build to the slots schema (pure)."""
    if "slots" in build and "fixed" in build:
        return build  # already new format

    fixed = [{"name": w, "type": "ranged"} for w in build.get("ranged", [])]
    fixed += [{"name": w, "type": "melee"} for w in build.get("melee", [])]

    slots = []
    no_duplicates = False

    # Ranged choices
    rc = build.get("ranged_choices") or []
    if rc:
        max_r = build.get("max_ranged")
        if max_r is None:
            # No max: pick 1 from each list (legacy product).
            for i, cl in enumerate(rc):
                slots.append({
                    "name": f"Ranged weapon {i + 1}",
                    "choices": [{"name": w, "type": "ranged"} for w in cl],
                })
        else:
            # max=N: pick N from deduped union (legacy combinations).
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

    # Melee choices (same rules)
    mc = build.get("melee_choices") or []
    if mc:
        max_m = build.get("max_melee")
        if max_m is None:
            for i, cl in enumerate(mc):
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


def convert_character(cfg: dict) -> bool:
    """Convert a character's weapon_options.builds in place. True if changed."""
    wo = cfg.get("weapon_options")
    if not wo or "builds" not in wo:
        return False
    changed = False
    new_builds = []
    for b in wo.get("builds", []):
        nb = convert_build(b)
        if nb is not b:
            changed = True
        new_builds.append(nb)
    if changed:
        wo["builds"] = new_builds
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--faction", type=str)
    args = ap.parse_args()

    factions = sorted(d.name for d in CONFIG_DIR.iterdir()
                      if d.is_dir() and (d / "characters.json").exists())
    if args.faction:
        factions = [args.faction]

    total = 0
    for faction in factions:
        fp = CONFIG_DIR / faction / "characters.json"
        data = json.load(open(fp))
        changed = 0
        for name, cfg in data.items():
            if name.startswith("_"):
                continue
            if convert_character(cfg):
                changed += 1
        if changed:
            total += changed
            print(f"{faction}: {changed} characters converted")
            if not args.dry_run:
                (fp).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"total characters converted: {total}")


if __name__ == "__main__":
    main()
