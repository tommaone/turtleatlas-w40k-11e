#!/usr/bin/env python3
"""Sync config info blocks from merged BSData stats (statline refresh).

Preparedness for fleet-wide statline changes: config `info` blocks are
hand-maintained copies of statlines and drift when GW updates datasheets.
This script re-syncs T/SV/W/OC/INV (+ M, deep_strike) from
data/merged/<fid>.json — the single source of truth for statlines.

Run after any BSData/merge refresh:
    python3 scripts/sync_config_info.py            # apply
    python3 scripts/sync_config_info.py --check     # report only (exit 1 on drift)

Semantics:
- merged value '-' or '' == no characteristic; config 0 for OC is
  equivalent to '-' (both mean none)
- '*' footnotes stripped (loadout-conditional INV is Known Issue #4 and
  is NOT synced — config value wins when merged carries only footnotes)
"""
import json
import glob
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CHECK = "--check" in sys.argv


def norm(v):
    if v is None:
        return None
    s = str(v).replace('"', "").replace("+", "").replace("*", "").replace("-", "").strip()
    if s in ("", "—"):
        return None
    try:
        return int(s)
    except ValueError:
        return s


def main():
    drift = fixed = checked = 0
    missed = []
    for p in sorted(glob.glob(str(REPO / "data/config/*/weapon_options.json"))) + \
             sorted(glob.glob(str(REPO / "data/config/*/characters.json"))):
        fid = Path(p).parts[-2]
        mfile = REPO / "data" / "merged" / f"{fid}.json"
        if not mfile.exists():
            continue
        merged = {u["name"]: u for u in json.load(open(mfile)).get("units", [])}
        d = json.load(open(p))
        changed = False
        for name, u in d.items():
            if name.startswith("_") or not isinstance(u, dict):
                continue
            info = u.get("info")
            if not isinstance(info, dict) or not info:
                continue
            mu = merged.get(name)
            if not mu:
                continue
            st = (mu.get("profile") or {}).get("stats") or {}
            checked += 1
            for ck, mk in (("T", "T"), ("SV", "Sv"), ("W", "W"), ("OC", "OC"), ("INV", "InSv")):
                cv, mv = norm(info.get(ck)), norm(st.get(mk))
                if mv is None:
                    continue  # merged has no static value — config wins
                if cv != mv:
                    drift += 1
                    if not CHECK:
                        info[ck] = mv
                        changed = True
        if changed and not CHECK:
            json.dump(d, open(p, "w"), indent=2, ensure_ascii=False)
            open(p, "a").write("\n")
            fixed += 1
    verb = "drifted fields" if CHECK else "fields synced"
    print(f"checked {checked} info blocks | {verb}: {drift} | files written: {fixed}")
    if CHECK and drift:
        sys.exit(1)


if __name__ == "__main__":
    main()
