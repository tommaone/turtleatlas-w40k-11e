# turtleatlas-w40k-11e — Guardrails

General 11th Edition rules reference for LLM agents using the MCP server.
Read this BEFORE calling MCP tools to avoid common DPP calculation errors.

---

## 1. MCP Tools

| Tool | Purpose |
|------|---------|
| `get_core_rules` | Core rules (abilities, phases, stratagems, cover) |
| `get_ability` | Specific ability description |
| `get_detachment` | Detachment rules, enhancements, stratagems |
| `get_unit` | Unit profile (stats, weapons, abilities, keywords) |
| `list_units` | Browse units with points costs |
| `compute_dpp` | Expected damage per point calculation |
| `get_stratagem` | Stratagem lookup |

---

## 2. How 11e DPP Differs from 10e

These are the non-obvious rule changes that affect damage calculations.

### Cover modifies BS, not saves
In 11e, Cover DOES NOT modify the saving throw. Instead, it worsens the attacker's BS by 1.
- BS 3+ shooting through cover → hits on 4+
- Save is unchanged regardless of cover
- The engine handles this via `hit_mode`: "normal" = no modifier, "cover" = +1BS, "plunging_fire" = -1BS

### PSYCHIC ignores Cover
**This is the most commonly missed rule.**
```
PSYCHIC [24.29]: Each time an attack is made with a [PSYCHIC] weapon, you can
ignore any or all modifiers to that attack's BS or WS characteristic and any
or all modifiers to the hit roll.
```
- Cover = BS modifier → Psychic weapons ignore it
- Plunging Fire = BS modifier → Psychic weapons can ignore it (optional)
- When computing DPP for Psychic weapons, use `hit_mode: "normal"` even if the target would normally be in cover
- Check a unit's weapons for the `Psychic` keyword in their abilities list

### Plunging Fire
Units with TOWERING keyword or on terrain 3"+ high get +1 BS when shooting at ground-level targets. This is an improvement (lower BS number).

---

## 3. Ability Reference for DPP Calculations

When you see these keywords on a weapon profile, here's how they affect damage.

| Ability | Effect | DPP impact |
|---------|--------|------------|
| **Torrent** | Auto-hit. No hit roll needed | Attacks = hits directly. BS irrelevant. `compute_dpp` still needs BS param but Torrent overrides it |
| **Sustained Hits 1** | Critical hit (unmodified 6) scores 1 extra hit | ~+17% hits vs normal, more with rerolls |
| **Sustained Hits 2** | Critical hit scores 2 extra hits | ~+33% hits |
| **Lethal Hits** | Critical hit auto-wounds (no wound roll) | Critical hits bypass wound roll entirely |
| **Devastating Wounds** | Critical wound (unmodified 6) deals mortal wounds | Mortal wounds ignore saving throws |
| **Twin-Linked** | Reroll the wound roll | ~+30% wound conversion |
| **Ignores Cover** | Ignores the cover penalty | Redundant if weapon already has Psychic |
| **Anti-X Y+** | Against X keyword targets, critical wounds on Y+. Normal wound still uses S vs T table | Dramatic boost vs X targets |
| **Lance** | If S < T, +1 to wound | Conditional +1 wound |
| **Heavy** | +1 to hit if attacker didn't move | Not modeled by default |
| **Rapid Fire X** | Double attacks at close range (≤12") | Model as attacks×2 if assuming close range |
| **Melta X** | +X damage at half range | Not modeled by default |
| **Blast** | Min 3 attacks vs 6+ model units | Not modeled by default |
| **Precision** | Can target Characters in unit | Tactical, not DPP-relevant |
| **Hazardous** | Risk of mortal wound on attacker | Must be modeled separately |
| **ONE SHOT** | Single use weapon | Divide damage by game length expectation |

---

## 4. Squad Modeling — General Principles

When computing DPP for a squad unit (multiple models), you must account for its actual weapon composition.

### Key rules
1. **Not every model carries the same weapon.** Squads have fixed limits on special/heavy weapons per X models.
2. **A model that takes a special weapon loses its default weapon** (usually a bolt weapon).
3. **Some units have innate weapons** that every model carries in addition to their chosen loadout (e.g. Purifying Flame on Purifiers).
4. **Character/single-model units** have their full weapon loadout — no limits to track.

### How to model correctly
For a 5-model squad with "max 2 special weapons":
```
- 2 models with special weapon (e.g. Incinerator): attacks × 2
- 3 models with default weapon (e.g. Bolt weapon): attacks × 3
- Add any innate weapons (e.g. 5× Purifying Flame): attacks × 5
```
Call `compute_dpp` separately for each weapon type, then sum the damage.

### Get unit data from `get_unit`
Always call `get_unit` for the specific unit to see its weapon options. The profile shows all available weapons. You must determine which loadout is realistic based on squad limits.

---

## 5. `compute_dpp` — Parameter Guide

| Parameter | Notes |
|-----------|-------|
| `weapon_name` | Label only, does not affect calculation |
| `attacks` | Total attacks for THIS weapon type across the squad |
| `bs` | Ballistic Skill (3 for 3+). For melee, use Weapon Skill. For Torrent weapons, value is irrelevant (auto-hit) |
| `strength` | Strength value |
| `ap` | Armor Penetration (e.g. -1, -2). Negative values worsen the save. Formula: save target = save - ap (e.g. SV3+ AP-2 → save on 5+) |
| `damage` | Damage per successful wound |
| `abilities` | Comma-separated list from weapon profile |
| `target_toughness` | Target's Toughness |
| `target_save` | Target's Save characteristic (3 for 3+) |
| `target_invuln` | Optional. Target's invulnerable save (4 for 4++) |
| `hit_mode` | "normal" (default), "cover" (+1BS), "plunging_fire" (-1BS). Psychic weapons always use "normal" |
| `unit_points` | Points cost of the ENTIRE unit (not per model) |

### AP formula verification
The engine uses: `modified_save = save - ap` (since ap is negative, this correctly worsens the save).
Example: SV3+ AP-2 → modified_save = 3 - (-2) = 5, need 5+ to save → 2/6 unsaved. ✓

---

## 6. What DPP Does NOT Model

- Detachment buffs (e.g. hit rerolls, wound rerolls)
- Stratagems
- Command rerolls
- Feel No Pain (FNP) on the target
- Cover modifiers on saves (11e: cover modifies BS, not saves)
- Melta half-range bonus
- Blast minimum attacks
- Heavy movement penalty/bonus
- Charge bonuses for melee
- Defensive durability (wounds, toughness, saves)

Always note these limitations when presenting DPP results.

---

## 7. Output Format

Use the 4-tier system:

```
🟢 FACTS — raw MCP tool output (numbers, rule text)
🟡 USE CASES — what the data implies (anti-horde, anti-elite, anti-vehicle)
🟠 CONSTRAINTS — what the data does NOT capture (see section 6)
🔴 STRATEGY — recommendations with explicit context and limitations
```

Include an assumption registry with every recommendation:
```
Assumptions:
- opponent unknown (all-comers)
- no detachment buffs or stratagems factored
- no cover on defender saves
- average dice (no variance band)
- [any other assumptions you made]
```

---

## 8. Common Pitfalls

- ❌ Using `hit_mode: "cover"` for Psychic weapons — Psychic [24.29] ignores BS modifiers
- ❌ Computing DPP for one squad model but using full squad `unit_points` — multiply attacks by model count
- ❌ Assuming all squad models carry special weapons — check squad limits per datasheet
- ❌ Confusing 10e vs 11e cover — 11e cover modifies BS, not saves
- ❌ Forgetting Torrent weapons auto-hit — Torrent + BS value is ignored by the engine
- ❌ Not checking what abilities a weapon has — e.g. a weapon with "Psychic" and "Sustained Hits 1" has both
