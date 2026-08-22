#!/usr/bin/env python3
"""Regenerate tests/test_golden_vulnerable_units.json from the engine.

Run after a legitimate engine improvement trips the golden tests:
    python3 -m pytest tests/test_golden_vulnerable_units.py   # confirm drift
    python3 scripts/capture_golden_tests.py                   # recapture
    git diff tests/test_golden_vulnerable_units.json          # review the delta
"""
import json, sys
from pathlib import Path
PROJ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJ))
from engine.ranking import RankingEngine

M = "Take and Hold"
TARGETS = [
    ("adeptus-custodes", "Pallas Grav-Attack"),
    ("adeptus-custodes", "Contemptor-Galatus Dreadnought"),
    ("adeptus-mechanicus", "Archaeopter Fusilave"),
    ("adeptus-mechanicus", "Skorpius Dunerider"),
    ("adeptus-mechanicus", "Archaeopter Transvector"),
    ("black-templars", "Gladiator Lancer"),
    ("black-templars", "Gladiator Valiant"),
    ("black-templars", "Impulsor"),
    ("black-templars", "Repulsor"),
    ("black-templars", "Land Raider Crusader"),
    ("chaos-space-marines", "Venomcrawler"),
    ("death-guard", "Foetid Bloat-Drone With Heavy Blight Launcher"),
    ("necrons", "Obelisk"),
    ("necrons", "Canoptek Reanimator"),
    ("necrons", "Night Scythe"),
    ("necrons", "Ghost Ark"),
    ("necrons", "Tesseract Vault"),
    ("space-marines", "Impulsor"),
]
engines = {}
def eng(slug):
    return engines.setdefault(slug, RankingEngine(slug))

def row(slug, name):
    res = eng(slug).compute_ranking(mission=M)
    return next(r for r in res if str(r.get("name","")).lower() == name.lower())

golden = {}
for slug, name in TARGETS:
    r = row(slug, name)
    golden[f"{slug}|{name}"] = {"dpp": round(float(r["dpp"]), 6), "pts": int(r["points"])}

parity = {}
for slug in ("black-templars", "space-marines", "dark-angels"):
    parity[slug] = round(float(row(slug, "Land Raider Crusader")["dpp"]), 6)

out = {"mission": M, "captured": "2026-08-22", "golden": golden, "parity_lrc": parity}
p = PROJ / "tests" / "test_golden_vulnerable_units.json"
with open(p, "w") as f:
    json.dump(out, f, indent=1)
print(f"wrote {len(golden)} goldens + parity={parity}")
