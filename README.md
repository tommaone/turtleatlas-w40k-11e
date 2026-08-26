# turtleatlas-w40k-11e

Warhammer 40,000 **11th Edition** knowledge base — DPP (Damage Per Point) engine that ranks every unit across 30 factions, 5 missions, and multiple meta compositions.

**[Live Rankings →](https://tommaone.github.io/turtleatlas-w40k-11e/findings/)**

## What it does

- **1,234 units** scored across **30 factions** and **5 missions** (Take and Hold, Purge the Foe, Reconnaissance, Priority Assets, Disruption)
- Loadout-aware: resolves wargear choices, alloc pools, squad composition, dual-profile weapons, and per-model limits from datasheets
- Meta presets per faction (competitive, anti-horde, infantry-heavy, vehicle-heavy, all-comers)
- Expert assessment layer: detachment ratings, army-rule synergy, playstyle guidance per faction
- Auto-detected army-wide rerolls, conditional rerolls (Surge of Wrath class), and damage boosts (Rend and Tear class)

## Architecture

```
turtleatlas-w40k-11e/
├── bsdata/        ← git submodule → BSData/wh40k-10e (unit profiles)
├── mfm/           ← git submodule → BSData/wh40k-11e-mfm (11e points, detachments)
├── adapter/
│   └── merge.py   ← Merges BSData profiles + MFM points → unified JSON
├── engine/
│   ├── ranking.py ← 3-vector scoring: DPP (damage) + SURV (durability) + MOB (mobility)
│   ├── dpp.py     ← Core DPP engine, weapon resolution, target profiles
│   └── reroll_detect.py ← Auto-detect conditional rerolls from datasheet text
├── data/config/   ← Per-faction loadout configs (squads, characters, vehicles, detachments)
├── resources/
│   └── experts/   ← Detachment assessments + army-rule synergy per faction
├── scripts/
│   ├── gen_findings_html.py ← Generates all findings pages + landing index
│   └── army_advisor.py      ← Army choice guide generator
├── findings/      ← Generated HTML (GitHub Pages)
└── tests/
```

## Data pipeline

| Step | What | Source |
|------|------|--------|
| 1. BSData | Unit profiles (M/T/SV/W, S/AP/D, abilities, weapons) | `bsdata/` submodule |
| 2. MFM | Points, detachments, enhancements | `mfm/` submodule |
| 3. Merge | Unified JSON per faction | `adapter/merge.py` |
| 4. Configs | Loadout configs (builds, slots, alloc pools, info blocks) | `data/config/` |
| 5. Engine | DPP/SURV/MOB scoring per unit vs target profiles | `engine/` |
| 6. Findings | Generated HTML per faction + landing page | `scripts/gen_findings_html.py` |

## Quick start

```bash
# Init submodules
git submodule update --init --recursive

# Merge all factions
python3 adapter/merge.py --all --output data/merged

# Generate findings
PYTHONHASHSEED=1 python3 scripts/gen_findings_html.py --all --index

# Run tests
PYTHONHASHSEED=1 python3 -m pytest tests/ -q
```

## Engine output (3-vector scoring)

Every unit is scored on three dimensions against configurable target profiles:

| Vector | What it measures | Key factors |
|--------|-----------------|-------------|
| **DPP** | Damage Per Point | BS, S vs T, AP vs save, weapon damage, alloc count |
| **SURV** | Survivability per point | T, W, Sv, Invuln, FNP, model count |
| **MOB** | Mobility score | Movement, OC, deep strike, advance/charge abilities |

DPP is computed against 5 meta presets per faction (competitive all-comers, anti-horde, infantry-heavy, vehicle-heavy, elite-heavy) with per-mission weighting.

## Not affiliated with Games Workshop

Warhammer 40,000 is a registered trademark of Games Workshop Limited. This is an unofficial, non-commercial fan project. All game mechanics data is community-maintained (BSData); no GW copyrighted text or images are included.
