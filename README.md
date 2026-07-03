# turtleatlas-w40k-11e

Warhammer 40,000 **11th Edition** knowledge base — merges BSData 10e datasheet profiles with official GW Munitorum Field Manual points for 11e.

## Architecture

```
turtleatlas-w40k-11e/
├── bsdata/        ← git submodule → https://github.com/BSData/wh40k-10e
│                     10e unit profiles (stats, weapons, abilities) — still valid in 11e
├── mfm/           ← git submodule → https://github.com/BSData/wh40k-11e-mfm
│                     11e points, detachments, enhancements (YAML)
├── adapter/
│   └── merge.py   ← Merges BSData profiles + MFM points → unified JSON
├── engine/        ← DPP computation for 11e (WIP)
├── mcp-server/    ← MCP tools (WIP)
└── tests/
```

## Why two submodules?

| Data | Source | Format | What |
|------|--------|--------|------|
| Unit profiles (M/T/SV/W, S/AP/D, abilities) | `bsdata/` (wh40k-10e) | XML `.cat` | 10e datasheets — mostly unchanged in 11e |
| Points, detachments, enhancements | `mfm/` (wh40k-11e-mfm) | YAML | 11e official MFM scraped from GW's site |

The **adapter** merges them by unit name: 10e profile + 11e pricing.

## Quick start

```bash
# Init submodules
git submodule update --init --recursive

# Install Python deps
pip install pyyaml

# Merge one faction
python3 adapter/merge.py --faction grey-knights

# Merge all factions
python3 adapter/merge.py --all --output data/merged
```

## Merged output

```json
{
  "faction": "Grey Knights",
  "slug": "grey-knights",
  "detachments": [
    {
      "name": "Warpbane Task Force",
      "dp": 3,
      "objective": "PURGE THE FOE",
      "enhancements": [
        { "name": "Mandulian Reliquary", "points": 20 }
      ]
    }
  ],
  "units": [
    {
      "name": "Brotherhood Terminator Squad",
      "profile": {
        "M": "5\"", "T": "5", "SV": "2+", "W": "3", "Ld": "6+", "OC": "1",
        "weapons": [
          { "name": "Storm bolter", "range": "24\"", "S": "4", "AP": "0", "D": "1" }
        ],
        "abilities": [
          { "name": "Teleport Assault", "description": "..." }
        ]
      },
      "pricing": [
        { "range": "[1,3]", "costs": [
          { "models": 4, "points": 140 },
          { "models": 5, "points": 175 }
        ]}
      ],
      "wargear_options": [
        { "item": "Psycannon", "points": 5 }
      ]
    }
  ]
}
```

## MCP Server (planned)

Will expose tools matching turtleatlas-w40k (13 tools), but pointing at 11e data.
