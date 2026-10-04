# engine/ — DPP Engine

Damage Per Point engine for 11th Edition Warhammer 40k.

## Files

| File | What it does |
|------|-------------|
| `dpp.py` | Core math — `compute_weapon_dpp()`, `compute_surv()`, `compute_mob()`, `compute_unit_dpp()`, `expected_damage()`, `parse_transport_capacity()` |
| `ranking.py` | `RankingEngine` — loadout resolution + 3-vector ranking. Also re-exports `compute_weapon_dpp` / `compute_surv` / `compute_mob` |
| `weapon_loader.py` | Weapon catalog from merged BSData + MFM data |
| `reroll_detect.py` | Auto-detect conditional reroll abilities (Surge of Wrath class) |
| `damage_boost_detect.py` | Auto-detect pure damage-boost abilities (Rend and Tear class) |
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

- Use `RankingEngine(faction).compute_ranking()` for a whole faction, or
  `RankingEngine(faction).resolve_loadout(name, target)` for one unit. Both sit
  on `compute_weapon_dpp()` — that is the only place DPP is computed.
- For survivability use `compute_surv()` (module-level in `dpp.py`, also
  re-exported by `ranking.py`). `get_unit_info()` is a `RankingEngine` **method**,
  not a module-level function — it will `ImportError` if called bare.
- Never present a number you did not get from the engine
- Violation: the finding is unreliable and will be blocked by Shredder review

## Before Computing DPP for a Squad

1. Load `resources/guardrails.md` — 11e rules reference
2. Load `resources/experts/<faction>.md` — squad limits and gotchas
3. Call `get_unit` for your unit — get the actual weapon profiles
4. Determine realistic loadout based on squad limits
5. **Do NOT sum per-weapon `compute_dpp` results by hand.** Each one is capped
   at the target's wound pool on its own, so adding them can report more wounds
   than the target physically has. Use `compute_unit_dpp` (MCP) or
   `compute_unit_dpp()` (Python) — it shares one points cost and caps the
   **summed** total once. Set `wounds_per_model` / `model_count` from the
   target's real profile; both default to 1 and will understate badly.
   `compute_dpp` / `compute_weapon_dpp()` remain correct for a single-weapon
   question.
6. `attacks`, `bs` and `damage` accept the datasheet value verbatim as a
   string (`"D6"`, `"2D6"`, `"3+"`, `"N/A"`) or as a number. Strings are
   flattened by `weapon_loader._parse_attacks` (`D6` -> 3.5, `2D6` -> 7.0) —
   the same parser the loader uses, so the two can never disagree. `damage_raw`
   is retained for honest damage-reroll math.
7. Add assumption registry to every DPP result

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

There is no `DPPEngine` class and no `compute_dpp(faction=..., unit=...)`. The
entry points are a dataclass pair plus a function, or `RankingEngine` for
anything unit-selection shaped.

### One weapon vs one target

```python
from engine.dpp import compute_weapon_dpp, WeaponProfile, TargetProfile, HitMode

weapon = WeaponProfile(name="Storm Bolter", attacks=2, bs=3, strength=4, ap=-1, damage=2)
target = TargetProfile(toughness=4, save=3)          # defaults: 1 wound/model, 1 model

r = compute_weapon_dpp(weapon, target, unit_points=175, hit_mode=HitMode.NORMAL)
print(r["total_damage"], r["dpp"])
```

### Whole-faction ranking

```python
from engine.ranking import RankingEngine

engine = RankingEngine("grey-knights")
target = engine.resolve_target("MEQ")   # TargetProfile(T4, 3+, 2W, 5 models)
engine.resolve_loadout("Paladin Squad", target)
engine.compute_ranking(target=target)   # add mission=/detachment=/max_points= as needed
```

`resolve_target(name)` maps a preset name to a `TargetProfile`. `"MEQ"` is T4/3+
with **2 wounds × 5 models** — see the warning below.

### Target model matters — `TargetProfile` defaults are 1W × 1 model

`wounds_per_model` and `model_count` both default to `1`, and total damage is
capped at `wounds_per_model × model_count`. A 2W × 5 unit therefore reports far
less damage than the same weapon against the default target. Set both from the
unit's real profile — via `get_unit` on the MCP server — or quote the number
against the 1W × 1 default *and say so*.
