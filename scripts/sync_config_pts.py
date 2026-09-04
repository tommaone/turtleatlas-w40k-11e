#!/usr/bin/env python3
"""Sync config `pts`/`pts_3rd` values to the current MFM snapshot.

Companion to tests/test_config_points_match_mfm.py + tests/test_pricing.py
— run when those tests fail after an MFM update:

    python3 -m pytest tests/test_config_points_match_mfm.py   # see drift
    python3 scripts/sync_config_pts.py --dry-run              # preview
    python3 scripts/sync_config_pts.py                        # apply
    git diff data/config                                      # review

Semantics (mirror tests/test_pricing.py — the gate):
- 1st-unit `pts`   : resolved from the first pricing tier (`pricing[0]`),
                     at the model count matching config `n` (fallback: first
                     cost in the tier).
- 3rd+ `pts_3rd`   : resolved from the `[3,)` tier, at the model count
                     matching config `n` (fallback: first cost). Set when MFM
                     has a 3rd+ tier, removed when it does not.
- Covers all config files: characters, squads, vehicles, weapon_options.
"""
import argparse
import json
import os
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO / "data" / "config"
MFM_DIR = REPO / "mfm" / "data"
FILES = ["characters.json", "squads.json", "vehicles.json", "weapon_options.json"]


def _norm(s):
    return (s.lower().strip().replace("\u2019", "'")
            .replace("-", " ").replace("  ", " ").replace("'", "").strip())


def _mfm_pricing(faction_yaml):
    """Return {norm_name: {"pts": [(models, pts)...], "pts_3rd": [...]|None}}.

    `pts` comes from the first pricing tier, `pts_3rd` from the `[3,)` tier.
    Each is a list of (models, points) rows so the caller can resolve by the
    config unit's own model count `n`.
    """
    out = {}
    for u in faction_yaml.get("units", []):
        pricing = u.get("pricing") or []
        if not pricing:
            continue
        first = [(c.get("models", 1), int(c["points"]))
                 for c in pricing[0].get("costs", [])
                 if c.get("points") is not None]
        third = None
        for pr in pricing:
            if pr.get("range") == "[3,)":
                third = [(c.get("models", 1), int(c["points"]))
                         for c in pr.get("costs", []) if c.get("points") is not None]
                break
        out[_norm(u.get("name", ""))] = {"pts": first, "pts_3rd": third}
    return out


def _resolve(rows, n):
    """Pick the (models, points) row matching config `n`; fall back to first."""
    if not rows:
        return None
    if n is not None:
        for models, points in rows:
            if models == n:
                return points
    return rows[0][1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    fixed, removed = 0, 0
    for slug in sorted(os.listdir(CONFIG_DIR)):
        yml_path = MFM_DIR / f"{slug}.yaml"
        if not yml_path.exists():
            continue
        mfm = _mfm_pricing(yaml.safe_load(yml_path.read_text()))
        for fname in FILES:
            fpath = CONFIG_DIR / slug / fname
            if not fpath.exists():
                continue
            data = json.loads(fpath.read_text())
            changed = False
            for key, val in data.items():
                if key.startswith("_") or not isinstance(val, dict):
                    continue
                if val.get("pts") is None and val.get("pts_3rd") is None:
                    continue
                # weapon_slot vehicles: pts is chassis base, not full price
                if "weapon_slots" in val:
                    continue
                entry = mfm.get(_norm(key))
                if entry is None:
                    continue
                n = val.get("n")
                target = _resolve(entry["pts"], n)
                if target is not None and val.get("pts") != target:
                    print(f"{slug}/{fname}/{key}: pts {val.get('pts')} -> {target}")
                    val["pts"] = target
                    changed = True
                    fixed += 1
                target_3rd = _resolve(entry["pts_3rd"], n)
                if target_3rd is None:
                    if "pts_3rd" in val:
                        print(f"{slug}/{fname}/{key}: remove pts_3rd "
                              f"({val['pts_3rd']}) — no MFM 3rd+ tier")
                        del val["pts_3rd"]
                        changed = True
                        removed += 1
                elif val.get("pts_3rd") != target_3rd:
                    print(f"{slug}/{fname}/{key}: pts_3rd {val.get('pts_3rd')} -> {target_3rd}")
                    val["pts_3rd"] = target_3rd
                    changed = True
                    fixed += 1
            if changed and not args.dry_run:
                with open(fpath, "w") as f:
                    json.dump(data, f, indent=2)
                    f.write("\n")

    print(f"\n{fixed} pts/pts_3rd values synced, {removed} pts_3rd removed"
          + (" (DRY RUN)" if args.dry_run else ""))


if __name__ == "__main__":
    main()
