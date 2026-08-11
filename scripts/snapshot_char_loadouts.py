#!/usr/bin/env python3
"""Snapshot resolved character loadouts for A/B parity after slots conversion.

For every character in every faction, resolve against the 7 canonical targets
via RankingEngine.resolve_loadout and dump the weapon-name tuples to JSON.

Usage:
    python3 scripts/snapshot_char_loadouts.py data/tmp_char_loadouts_before.json

Run BEFORE converting characters to the slots format; re-run the same file
AFTER and compare with scripts/compare_char_loadouts.py.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tests.crossfaction_common import ALL_FACTIONS, TARGETS, load_engine


def main(out_path: str) -> None:
    snapshot = {}
    for faction in ALL_FACTIONS:
        engine = load_engine(faction)
        chars = sorted(engine.config.characters.keys())
        fac_snap = {}
        for name in chars:
            if name.startswith("_"):
                continue
            for target in TARGETS:
                tprof = engine.resolve_target(target)
                res = engine.resolve_loadout(name, tprof)
                if res is None:
                    fac_snap.setdefault(name, {})[target] = None
                    continue
                _pts, ranged, melee, _innate, _info = res
                fac_snap.setdefault(name, {})[target] = {
                    "ranged": [w.name for w in ranged],
                    "melee": [w.name for w in melee],
                }
        snapshot[faction] = fac_snap
        print(f"{faction}: {len(fac_snap)} characters snapshotted", file=sys.stderr)
    Path(out_path).write_text(json.dumps(snapshot, indent=1, ensure_ascii=False))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main(sys.argv[1])
