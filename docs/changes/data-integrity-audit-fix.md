# Data Integrity Audit Fix

## Problem Statement

The DPP engine's rankings are built on incorrect data across all 5 factions. Three systemic issues corrupt survivability and mobility calculations:

1. **Config overrides replacing correct BSData stats** — 21 units have wrong T/W/Sv/OC/M in config that override correct merged data
2. **Missing FNP values** — 15+ units have Feel No Pain in ability text but it's not captured anywhere the engine reads
3. **Missing Invulnerable Save in config** — hundreds of units in config lack INV when ability text says they have one

## Root Causes

### Root Cause 1: Config stat drift
Config files (`characters.json`, `squads.json`, `vehicles.json`) were created at one point in time and not updated when BSData was refreshed. The engine reads stats from config `info` dicts via `get_unit_info()`, so wrong config values = wrong rankings.

**Worst offenders:**
- Lion El'Jonson: T=6 (should be 9), W=8 (should be 10), OC=3 (should be 4) — a Primarch being scored as a Terminator
- Brother-Captain (GK): T=4 (should be 5), W=4 (should be 6), M=6" (should be 5")
- Eradicator Squad (SM): T=4 (should be 6), W=2 (should be 3), M=6" (should be 5")

### Root Cause 2: No FNP parsing from ability text
The engine supports FNP (`UnitDefense.fnp`, `compute_surv()`, `expected_damage()`) but only reads it from config `info.fnp` or detachment modifiers. BSData stores FNP as either:
- A rule string: `"Feel No Pain"` (no value)
- An ability with value in description: `"Feel No Pain 4+"` or `"Feel No Pain 3+"`

Neither is parsed by the engine.

### Root Cause 3: Missing INV in config info dicts
The engine reads INV from config `info.INV` or `info.invuln`. For units NOT in config, it falls back to parsing `"Invulnerable Save (X+)"` from the `rules` field (which works). But for units IN config without INV, the engine returns None — even though the merged data's rules field says they have one.

## Fix Strategy

### Fix 1: Correct config stat discrepancies
For each of the 21 discrepancies, update the config `info` dict to match the merged BSData values. BSData is the source of truth for base stats.

### Fix 2: Add FNP to config info dicts
Add `"fnp": X` to the `info` dict for units that have FNP. Values extracted from ability text:

| Unit | Faction | FNP | Source |
|------|---------|-----|--------|
| Great Unclean One | chaos-daemons, chaos-knights | 5 | Nurgle daemon faction rule (Disgustingly Resilient) |
| Rotigus | chaos-daemons, chaos-knights | 5 | Nurgle daemon faction rule |
| Poxbringer | chaos-daemons, chaos-knights | 5 | Nurgle daemon faction rule |
| Karanak | chaos-daemons, chaos-knights | 3 | Brass Collar of Bloody Vengeance |
| Contorted Epitome | chaos-daemons, chaos-knights | 4 | Swallow Energy (Psychic) |
| Brotherhood Librarian | grey-knights | 4 | GK psychic ability |
| Ancient | dark-angels, space-marines | 4 | Unbreakable Duty (conditional) |
| Chaplain In Terminator Armour | dark-angels, space-marines | 4 | Recitation of Faith (vs mortals) |
| Culexus Assassin | dark-angels, grey-knights, space-marines | 2 | Abomination (vs psychic) |
| Lazarus | dark-angels | 3 | Spiritshield Helm (vs psychic/mortals) |
| Lieutenant With Combi-Weapon | dark-angels, space-marines | 5 | Evade and Survive |
| Watch Captain Artemis | dark-angels, grey-knights, space-marines | 5 | Unstoppable Champion |
| Exaction Squad | dark-angels, grey-knights, space-marines | 5 | Arbites medi-kit |
| Rhino | grey-knights | 6 | Truesilver Aegis (vs mortals) |

**Note:** Some FNP values are conditional (vs psychic only, vs mortals only, on objective only). For DPP ranking purposes, we use the unconditional value where available. Conditional FNP is noted but still added — the engine uses it as a flat modifier, which is an acceptable approximation for ranking.

### Fix 3: Add missing INV to config info dicts
For units in config that lack INV but have it in merged data rules/abilities, add the INV value. The engine's fallback path already parses this from rules text for non-config units, but config units bypass the fallback.

**Priority:** Only add INV for units that are actually ranked by the engine (i.e., units in config that appear in rankings). Most basic infantry (Intercessors, etc.) don't have InvSave — only specific units do.

### Fix 4: Clean up da_units.json
This file is an orphan — not referenced anywhere in the codebase. It contains duplicates of units already in the standard DA config files (with wrong stats). Action: Remove the file.

## Files to Modify

### Config stat fixes
- `data/config/dark-angels/characters.json` — Lion El'Jonson T/W/OC
- `data/config/dark-angels/vehicles.json` — Ancient In Terminator Armour, Terminator Squad OC, Nephilim/Dark Talon OC
- `data/config/dark-angels/weapon_options.json` — Redemptor/Dreadnought/Brutalis (if affected)
- `data/config/grey-knights/characters.json` — Brother-Captain, Brotherhood Chaplain, Brotherhood Librarian, Castellan Crowe, Grand Master, Grand Master Voldus
- `data/config/grey-knights/squads.json` — Interceptor Squad M/OC, Champion of Titan W
- `data/config/chaos-daemons/squads.json` — Pink Horrors OC
- `data/config/space-marines/characters.json` — Ancient In Terminator Armour, Lion El'Jonson T/W/OC
- `data/config/space-marines/squads.json` — Terminator Squad OC, Eradicator Squad T/M/W, Vanguard Veteran W
- `data/config/space-marines/vehicles.json` — Land Speeder Vengeance W

### FNP additions
- `data/config/chaos-daemons/characters.json` — GUC, Rotigus, Poxbringer, Karanak, Contorted Epitome
- `data/config/grey-knights/characters.json` — Brotherhood Librarian
- `data/config/dark-angels/characters.json` — Ancient, Chaplain ITA, Culexus, Lazarus, Lt Combi-Weapon, Artemis
- `data/config/space-marines/characters.json` — Ancient, Chaplain ITA, Culexus, Lt Combi-Weapon, Artemis
- `data/config/dark-angels/squads.json` — Exaction Squad
- `data/config/grey-knights/squads.json` — Exaction Squad
- `data/config/space-marines/squads.json` — Exaction Squad
- `data/config/grey-knights/vehicles.json` — Rhino

### INV additions (config units missing it)
- Only for units that are actually ranked and have InvSave per merged data
- Priority: GK Terminator Squad, GK Paladin Squad, NDK, GMNDK, Deathwing units

### Cleanup
- `data/config/dark-angels/da_units.json` — DELETE (orphan file)

## Verification

After applying fixes:
1. Run `python3 engine/ranking.py` for each faction and verify unit stats in output
2. Check Lion El'Jonson shows T=9, W=10, OC=4 in SURV output
3. Check GUC shows FNP 5+ in SURV output
4. Check GK units show correct INV values
5. Run existing tests: `pytest tests/`

### Verification Results (2026-07-17)
- ✅ All config vs merged stat discrepancies fixed (exact-match verification)
- ✅ FNP values added to 14 units across 4 factions
- ✅ INV values added to key GK units (Brother-Captain, Grand Master, Grand Master Voldus, Dreadknight Champion, Champion of Titan)
- ✅ Orphan da_units.json deleted
- ✅ Epidemius: W=5→8, OC=1→2 (corrected to match merged)
- ✅ Champion of Titan [Crucible]: W=2→4, INV=4 added
- ✅ Dreadknight Champion [Crucible]: INV=4 added

## Rollback Plan

All changes are to JSON config files. Git revert if anything breaks.

## Risks

1. **Conditional FNP approximation**: Some FNP values are conditional (vs psychic, vs mortals). Using them as flat FNP overstates survivability. Acceptable for ranking purposes but should be noted in assumptions.
2. **INV cascading**: Adding INV to many units will significantly change their SURV scores and relative rankings. This is correct behavior — they were undervalued before.
3. **da_units.json removal**: If any external tool references this file, it will break. Verified: no references in codebase.
