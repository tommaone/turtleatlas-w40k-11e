#!/usr/bin/env python3
"""P0 war-plan inventory + pre-detachment score snapshot.

Outputs docs/snapshots/pre-detachment-scores.json:
per faction, rank-decay roster index per disposition + overall.
Reuses gen_findings_html build_data so numbers match the landing page.
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
import gen_findings_html as gfh


def main():
    snap = {"captured": "2026-08-23", "note": "pre-detachment-modifier baseline", "factions": {}}
    for fid, fname in gfh.FACTIONS.items():
        data, n_units = gfh.build_data(fid)
        entry = gfh.compute_tiers_entry(fname, data, n_units)
        snap["factions"][fid] = entry
        print(f"{fname}: overall={entry['overall']}")

    out = REPO / "docs" / "snapshots"
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "pre-detachment-scores.json", "w") as f:
        json.dump(snap, f, indent=1, ensure_ascii=False)
    print(f"\nwrote {out / 'pre-detachment-scores.json'} ({len(snap['factions'])} factions)")


if __name__ == "__main__":
    main()
