#!/usr/bin/env python3
"""Compare two character-loadout snapshots for A/B parity.

Usage:
    python3 scripts/compare_char_loadouts.py data/tmp_char_loadouts_before.json data/tmp_char_loadouts_after.json

Exits 0 if identical, 1 if diffs found (prints them).
Compares only weapon-name tuples per (faction, character, target);
None (no loadout) must match too.
"""
import json
import sys


def main():
    a = json.load(open(sys.argv[1]))
    b = json.load(open(sys.argv[2]))
    diffs = []
    for faction in sorted(set(a) | set(b)):
        fa, fb = a.get(faction, {}), b.get(faction, {})
        for name in sorted(set(fa) | set(fb)):
            ca, cb = fa.get(name), fb.get(name)
            if ca != cb:
                for target in sorted(set(ca or {}) | set(cb or {})):
                    if (ca or {}).get(target) != (cb or {}).get(target):
                        diffs.append((faction, name, target, (ca or {}).get(target), (cb or {}).get(target)))
    if not diffs:
        print("PARITY OK — all loadouts identical after conversion")
        return 0
    for faction, name, target, va, vb in diffs:
        print(f"[{faction}] {name} vs {target}:\n  before={va}\n  after ={vb}")
    print(f"\n{diff_count} diffs" if (diff_count := len(diffs)) else "")
    return 1


if __name__ == "__main__":
    sys.exit(main())
