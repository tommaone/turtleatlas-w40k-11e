# engine/ — DPP Engine

Damage Per Point engine for 11th Edition Warhammer 40k.

## Files

| File | What it does |
|------|-------------|
| `dpp.py` | Core DPP engine — `compute_dpp()`, `resolve_loadout()`, `_ld_dmg()` |
| `ranking.py` | Generic 3-vector ranking engine — `compute_ranking()` |
| `weapon_loader.py` | Weapon catalog from merged BSData + MFM data |
| `gk_demo.py` | Grey Knights demo script |
| `gk_ranking.py` | GK-specific ranking script |

## Key 11e Rule Changes (critical for DPP)

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
- Torrent weapons bypass hit rolls entirely — handled automatically.

## Hard Rule — No Fabricated Numbers

Agents MUST use the engine for ALL numerical output. Do NOT fabricate, estimate, approximate, or re-compute DPP/SURV/MOB values.

- Call `compute_ranking()` or `resolve_loadout()` + `_ld_dmg()` for all DPP comparisons
- Call `get_unit_info()` + `compute_surv()` for survivability
- Never present a number you did not get from the engine
- Violation: the finding is unreliable and will be blocked by Shredder review

## Before Computing DPP for a Squad

1. Load `resources/guardrails.md` — 11e rules reference
2. Load `resources/experts/<faction>.md` — squad limits and gotchas
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

## Critical Gotchas

1. **Squad weapon limits**: Not every model carries the best gun. Each squad type has fixed max special weapons per X models. Check the faction's expert file or datasheet.
2. **Psychic != Ignore Cover**: Psychic weapons ignore *all* BS/hit roll modifiers, which includes Cover. This is [24.29] in the Core Rules.
3. **AP formula**: `modified_save = save - ap` (ap is negative, so SV3+ AP-2 → save on 5+).
4. **Purifying Flame** is an ADDITIONAL weapon on Purifiers — every model carries it in addition to their Storm Bolter.
5. **Special weapon replaces Storm Bolter** — a model that takes a Psycannon loses its Storm Bolter but keeps its Nemesis force weapon.

## How to Use

```python
from engine.dpp import DPPEngine
engine = DPPEngine()
result = engine.compute_dpp(faction="grey-knights", unit="Paladin Squad")
print(result)
```
