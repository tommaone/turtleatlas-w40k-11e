# turtleatlas-w40k-11e

11th Edition Warhammer 40k structured data + DPP engine + MCP server.

## IP & Copyright Notice

**This repository contains NO Games Workshop copyrighted rule text or PDFs.**
- `data/merged/*.json` — Community-maintained BSData game data (points, profiles, keywords). Game mechanics data only, no verbatim rule text.
- `data/config/*/` — Our own derived configuration files. Machine-readable modifiers only.
- Engine code — Original work. No GW IP.

**NEVER commit GW copyrighted material:**
- ⛔ No PDFs of rulebooks, faction packs, or indexes
- ⛔ No verbatim rule text (ability descriptions, stratagem text, lore)
- ⛔ No official GW images, logos, or artwork

**Safe to include (game mechanics / community data):**
- ✅ Points values (Munitorum Field Manual data)
- ✅ Unit profiles (M/WS/BS/S/T/W/A/Ld/Sv — game stats)
- ✅ Weapon profiles (range, type, S, AP, D, ability keywords)
- ✅ Keywords
- ✅ Machine-readable modifier data (+1 to hit, Sustained Hits, etc.)
- ✅ Our own analysis, rankings, and derived metrics (DPP, SURV)

This is an unofficial, non-commercial fan project. Warhammer 40,000 is a registered trademark of Games Workshop Limited.

## Architecture

```
data/                          # Game data (community sources, no GW IP)
├── merged/                    # BSData profiles + MFM points merged
│   ├── grey-knights.json
│   ├── chaos-knights.json
│   └── chaos-daemons.json
└── config/                    # Our own config per faction
    ├── _base.json             # Shared target/mission profiles
    ├── chaos-knights/
    ├── chaos-daemons/
    └── grey-knights/

adapter/                       # Data parsers (run locally, not in repo)
├── bsdata_parser.py           # BSData XML → JSON profiles
├── merge.py                   # Merge profiles + points
├── core_rules_parser.py       # Local PDF → JSON (output not committed)
└── faction_pack_parser.py     # Local PDF → JSON (output not committed)

engine/                        # DPP engine
├── dpp.py                     # Damage Per Point engine (11e rules)
├── ranking.py                 # Generic 3-vector ranking engine
└── weapon_loader.py           # Weapon catalog from merged data

mcp-server/                    # MCP server
├── index.js                   # 7 tools, stdio or HTTP
└── package.json               # @modelcontextprotocol/sdk ^1.29.0

resources/                     # Human-readable knowledge files
├── guardrails.md              # 11e rules reference & DPP pitfalls
├── non-dpp-value.md           # OC/screening/SURV framework
└── experts/                   # Faction domain knowledge
    └── grey-knights.md

run_dpp.py                     # CLI runner (any faction)
```

## Key 11e Rule Changes

Everything in this section critically affects DPP calculations. Get these right before calling `compute_dpp`.

### Cover = BS modifier (not save)
- 11e: "worsen the BS characteristic by 1" → `hit_mode: "cover"`
- NOT a save modifier (that was 10e)
- Engine handles this via `hit_mode` parameter

### Psychic [24.29] ignores all BS/WS/hit roll modifiers
- Psychic weapons ignore Cover, Plunging Fire, and any other BS/WS modifier
- `hit_mode: "normal"` ALWAYS for Psychic weapons, even if the target is in cover
- Check a weapon's ability list for the `Psychic` keyword

### Plunging Fire
- TOWERING units or units on terrain 3"+ high get -1BS (improvement) when shooting ground targets
- `hit_mode: "plunging_fire"` narrows BS by 1 (i.e. BS3+ → BS2+)

### Torrent = auto-hit
- No hit roll needed. BS value is irrelevant.
- The engine accounts for this — Torrent weapons bypass hit rolls entirely.

## Critical Gotchas

1. **Squad weapon limits**: Not every model carries the best gun. Each squad type has fixed max special weapons per X models. Check `resources/experts/grey-knights.md` or the unit's datasheet in the merged data.
2. **Psychic != Ignore Cover**: Psychic weapons ignore *all* BS/hit roll modifiers, which includes Cover. This is [24.29] in the Core Rules.
3. **AP formula**: `modified_save = save - ap` (ap is negative, so SV3+ AP-2 → save on 5+). The engine uses this correctly now.
4. **Purifying Flame** is an ADDITIONAL weapon on Purifiers — every model carries it in addition to their Storm Bolter.
5. **Special weapon replaces Storm Bolter** — a model that takes a Psycannon loses its Storm Bolter but keeps its Nemesis force weapon.

## Hard Rule — No Fabricated Numbers

Agents MUST use the engine for ALL numerical output. Do NOT fabricate, estimate, approximate, or re-compute DPP/SURV/MOB values.

- Call `engine.compute_ranking()` or `engine.resolve_loadout()` + `_ld_dmg()` for all DPP comparisons
- Call `engine.get_unit_info()` + `compute_surv()` for survivability
- Never present a number you did not get from the engine
- Violation: the finding is unreliable and will be blocked by Shredder review

## How to Use This Codebase

```bash
# Run merge for a faction
python3 adapter/merge.py --faction grey-knights

# Run GK DPP demo
python3 engine/gk_demo.py

# Start MCP server (stdio — for AI clients)
node mcp-server/index.js

# Start MCP server (HTTP — for testing)
node mcp-server/index.js --port 3000

# Core data via MCP:
#   get_core_rules → 35 abilities, 12 stratagems, 6 phases
#   get_unit → unit profile with weapons
#   compute_dpp → expected damage per point
```

## Before Computing DPP for a Squad

1. Load `resources/guardrails.md` — 11e rules reference
2. Load `resources/experts/grey-knights.md` — GK squad limits and gotchas
3. Call `get_unit` for your unit — get the actual weapon profiles
4. Determine realistic loadout based on squad limits
5. Call `compute_dpp` per weapon type, sum the damages
6. Add assumption registry to every DPP result

## What DPP Does NOT Model

Always note these when presenting results:
- Detachment buffs, stratagems, command rerolls
- Feel No Pain on the target
- Melta half-range bonus, Blast minimum attacks
- Heavy movement penalty
- Defensive durability

## Relevant Files

- `resources/guardrails.md` — general 11e rules & DPP pitfalls
- `resources/experts/grey-knights.md` — GK domain knowledge
- `engine/dpp.py` — the DPP engine itself
- `adapter/merge.py` — how data gets merged
- `data/merged/grey-knights.json` — the actual GK data
