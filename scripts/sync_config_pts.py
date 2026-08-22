#!/usr/bin/env python3
"""Sync config `pts` values to the current MFM snapshot.

Companion to tests/test_config_points_match_mfm.py — run when that test
fails after an MFM update:

    python3 -m pytest tests/test_config_points_match_mfm.py   # see drift
    python3 scripts/sync_config_pts.py --dry-run              # preview
    python3 scripts/sync_config_pts.py                        # apply
    git diff data/config                                      # review

Semantics:
- min MFM cost = base points ([1,1] first-unit vs [2,) requisition split)
- cheapest tier covering >1 model is skipped (config has no size info)
"""
import argparse
import json
import os
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO / "data" / "config"
MFM_DIR = REPO / "mfm" / "data"
FILES = ["weapon_options.json", "vehicles.json", "characters.json"]


def _norm(s):
    return (s.lower().replace("'", "").replace("\u2019", "")
            .replace("-", " ").replace("  ", " ").strip())


def _mfm_base_points(faction_yaml):
    out = {}
    for u in faction_yaml.get("units", []):
        costs = []
        for pr in u.get("pricing", []):
            for c in pr.get("costs", []):
                if c.get("points") is not None:
                    costs.append((c.get("models", 1), int(c["points"])))
        if costs:
            out[_norm(u.get("name", ""))] = min(costs)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    fixed, skipped = 0, []
    for slug in sorted(os.listdir(CONFIG_DIR)):
        yml_path = MFM_DIR / f"{slug}.yaml"
        if not yml_path.exists():
            continue
        mfm = _mfm_base_points(yaml.safe_load(yml_path.read_text()))
        for fname in FILES:
            fpath = CONFIG_DIR / slug / fname
            if not fpath.exists():
                continue
            data = json.loads(fpath.read_text())
            changed = False
            for key, val in data.items():
                if key.startswith("_") or not isinstance(val, dict):
                    continue
                if val.get("pts") is None:
                    continue
                entry = mfm.get(_norm(key))
                if entry is None:
                    continue
                models, target = entry
                if models != 1:
                    skipped.append(f"{slug}/{key}: {models}-model tier")
                    continue
                if val["pts"] != target:
                    print(f"{slug}/{fname}/{key}: {val['pts']} -> {target}")
                    val["pts"] = target
                    changed = True
                    fixed += 1
            if changed and not args.dry_run:
                with open(fpath, "w") as f:
                    json.dump(data, f, indent=2)
                    f.write("\n")

    print(f"\n{fixed} pts values synced"
          + (" (DRY RUN)" if args.dry_run else ""))
    print(f"{len(skipped)} multi-model-tier entries skipped (uncheckable)")


if __name__ == "__main__":
    main()
