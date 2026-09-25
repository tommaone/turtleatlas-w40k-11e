"""Guard: config `pts` values must match the current MFM snapshot.

Prevents silent points drift between data/config/*/{weapon_options,
vehicles,characters}.json and mfm/data/<slug>.yaml. Runs on the same
min-cost semantics as scripts/sync_config_pts.py:

- MFM pricing ranges split into [1,1] first-unit vs [2,) requisition
  surcharges -> min cost is the base points.
- Entries whose cheapest cost tier covers >1 model (command squads,
  Inceptor squads...) are skipped: config has no size info to check
  against.

When this test fails after an MFM update:
    python3 scripts/sync_config_pts.py   # review diff, then commit
"""

import json
import os
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO / "data" / "config"
MFM_DIR = REPO / "mfm" / "data"

FILES = ["weapon_options.json", "vehicles.json", "characters.json"]


def _norm(s):
    return (s.lower().replace("'", "").replace("\u2019", "")
            .replace("-", " ").replace("  ", " ").strip())


def _mfm_base_points(faction_yaml):
    """name(norm) -> (models_of_cheapest_tier, points) or absent.

    Duplicate unit names are pricing tiers, not separate units:
    imperial-agents lists 29 units twice, the second carrying groupTitle
    ("Every Model Has The Imperium Keyword") at a different rate. Prefer the
    plain entry — mirrors adapter/merge.py so config, merged and this guard
    all read the same base price. Falls back to a groupTitle entry when a unit
    has no plain one.
    """
    out = {}
    group = {}
    for u in faction_yaml.get("units", []):
        costs = []
        for pr in u.get("pricing", []):
            for c in pr.get("costs", []):
                if c.get("points") is not None:
                    costs.append((c.get("models", 1), int(c["points"])))
        if not costs:
            continue
        name = _norm(u.get("name", ""))
        if u.get("groupTitle"):
            group.setdefault(name, min(costs))
        else:
            out[name] = min(costs)
    for name, costs in group.items():
        out.setdefault(name, costs)
    return out


def _drifted():
    drifts = []
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
                    continue  # no size info in config — uncheckable
                if val["pts"] != target:
                    drifts.append(f"{slug}/{fname}/{key}: "
                                  f"{val['pts']} != MFM {target}")
    return drifts


def test_config_pts_match_mfm():
    drifts = _drifted()
    assert not drifts, (
        f"{len(drifts)} config pts values drifted from MFM. "
        f"Fix: python3 scripts/sync_config_pts.py\n  " + "\n  ".join(drifts[:20])
    )
