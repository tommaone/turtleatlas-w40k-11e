#!/usr/bin/env python3
"""Sync shared god-marine squad entries from origin factions to consumers.

God-marines (Noise/Plague/Rubric/Berzerkers) are datasheet-truth units that
appear in multiple factions' BSData merged data, but are PRICED under their
god faction's MFM (emperors-children, death-guard, thousand-sons, world-eaters).
Chaos Space Marines can legally field them at the god-faction price.

To avoid stale copies (e.g., CSM Noise Marines drifted to n=5 while EC
updated to n=6), this script copies the origin's full squad entry verbatim
into each consumer's squads.json. The companion guard
(tests/test_shared_units_sync.py) fails on drift, so an origin update forces
a re-sync before the suite goes green.

Idempotent: re-running with already-synced configs is a no-op.
Entry metadata (_note, _source, pts_3rd) travels with the origin entry —
consumer and origin stay byte-identical, which is exactly what the guard
enforces. Do NOT hand-edit a synced entry in the consumer; update the origin
and re-run this script.

Usage:
  python3 scripts/sync_shared_units.py            # sync all shared units
  python3 scripts/sync_shared_units.py --dry-run  # report drift, don't write
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# The single source of truth for cross-faction shared squad units.
# origin = the faction that owns the datasheet + MFM pricing
# consumers = factions that may legally field the unit at the origin's price
# Extend this map if another shared unit is identified; the guard picks it
# up automatically (it imports SHARED_UNITS).
SHARED_UNITS: dict[str, dict] = {
    "Noise Marines":     {"origin": "emperors-children",  "consumers": ["chaos-space-marines"]},
    "Plague Marines":    {"origin": "death-guard",        "consumers": ["chaos-space-marines"]},
    "Rubric Marines":    {"origin": "thousand-sons",      "consumers": ["chaos-space-marines"]},
    "Khorne Berzerkers": {"origin": "world-eaters",       "consumers": ["chaos-space-marines"]},
}
# NOTE: Rubric Marines was previously blocked because CSM merged dropped the
# Aspiring Sorcerer (its wargear sat in a "Wargear" choice selectionEntryGroup
# the parser didn't recurse into). Fixed in adapter/bsdata_parser_11e.py —
# _resolve_profiles now recurses into selectionEntryGroups too. All four
# god-marines sync cleanly.


def _load(fid: str) -> dict:
    return json.load(open(REPO / "data" / "config" / fid / "squads.json"))


def _save(fid: str, data: dict) -> None:
    json.dump(data, open(REPO / "data" / "config" / fid / "squads.json", "w"),
              indent=2, ensure_ascii=False)


def sync(dry_run: bool = False) -> list[tuple[str, str, str]]:
    """Copy each shared unit's origin entry into every consumer.

    Returns a list of (unit, consumer, change_kind) for reporting.
    change_kind is 'added', 'updated', or 'unchanged'.
    """
    changes: list[tuple[str, str, str]] = []
    for unit, spec in SHARED_UNITS.items():
        origin_data = _load(spec["origin"])
        if unit not in origin_data:
            changes.append((unit, spec["origin"], "MISSING in origin (skipped)"))
            continue
        origin_entry = origin_data[unit]
        for consumer in spec["consumers"]:
            cdata = _load(consumer)
            current = cdata.get(unit)
            if current == origin_entry:
                changes.append((unit, consumer, "unchanged"))
                continue
            kind = "updated" if current else "added"
            if not dry_run:
                cdata[unit] = json.loads(json.dumps(origin_entry))  # deep copy
                _save(consumer, cdata)
            changes.append((unit, consumer, kind))
    return changes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="report drift, don't write")
    args = ap.parse_args()

    changes = sync(dry_run=args.dry_run)
    actionable = [c for c in changes if c[2] not in ("unchanged",)]
    for unit, consumer, kind in changes:
        flag = "DRY-RUN" if (args.dry_run and kind not in ("unchanged",)) else ""
        print(f"  {unit:20s} -> {consumer:22s} {kind} {flag}")
    if actionable:
        print(f"\n{len(actionable)} change(s) {'would be ' if args.dry_run else ''}applied.")
        return 0
    print("\nAll shared units in sync.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
