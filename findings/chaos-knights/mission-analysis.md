# CK Detachment Mission Analysis

Engine-backed detachment recommendations for Chaos Knights across competitive missions.

---

## Assumptions

- opponent unknown (all-comers)
- meta profile: competitive (melee_penalty 0.8)
- no cover factored into saves
- no stratagems or command rerolls
- average dice (no variance band)
- all detachments at 2dp cost unless noted
- modelled: rerolls, sustained hits, lethal hits, extra AP, invuln, FNP, movement bonus
- NOT modelled: stealth, cover_save, advance_and_charge, fallback_and_shoot, fallback_and_charge, assault, heavy_ignore

---

## Per-Mission Recommendations

### Purge the Foe — Infernal Lance [1] (Diabolic Power)

**Why:** DPP +30% with no single-point-of-failure. Helhunt Lance [0] gives +34% but depends on the big knight surviving — if it dies T3, the aura dies with it. Infernal's SH1 + Lethal Hits applies army-wide regardless.

| Detachment | DPP delta | Risk |
|-----------|-----------|------|
| Infernal Lance [1] | +30% | None |
| Helhunt Lance [0] | +34% | Big knight = single point of failure |

### Take and Hold — Infernal Lance [2] (Unnatural Fortitude)

**Why:** Only detachment that boosts SURV at all. 4++/5+++ pushes effective wounds (ap4) from 33 → 43 (+28%). Staying on objectives is the win condition — this is the only pick that helps you do that.

### Priority Assets — Infernal Lance [2] (Unnatural Fortitude)

**Why:** Same logic as Take and Hold. Assets missions reward durability over raw kill. Infernal [2] is the only survivability boost in the CK pool.

---

## Inert Fields Impact

7 modifier fields are not yet applied by the engine. This affects several detachments:

| Detachment | Affects | Relies on | Real-game value |
|-----------|---------|-----------|-----------------|
| Hunting Warpack [1] | mob | advance_and_charge | Medium — board reach |
| Iconoclast Fiefdom [0] | surv | stealth | Low — cover is ubiquitous in 11e |
| Iconoclast Fiefdom [1] | surv | stealth | Low |
| Helhunt Lance [1] | mob | advance_and_charge, fallback_and_charge | Medium |
| Lords of Dread [0] | surv | stealth | Low |
| Lords of Dread [1] | dpp | None (OC-only — not modelled) | N/A |

When these fields are implemented, Iconoclast Fiefdom and Lords of Dread will gain real SURV/MOB boosts.

---

## Hunting Warpack Caveat

Hunting Warpack forces **War Dogs only** — no big knights. War Dogs have T9, W14, no invuln. In Purge the Foe they get mulched. Engine cannot model army composition restrictions from `unit_filter` alone.

---

## Raw Engine Data

| Detachment | Choice | DPP | SURV(ap4) | MOB |
|-----------|--------|-----|-----------|-----|
| *(no detachment)* | — | 0.0645 | 33 | 2.21 |
| Infernal Lance | [2] Unnatural Fortitude | 0.0645 | **43** | 2.21 |
| Infernal Lance | [1] Diabolic Power | **0.0838** | 33 | 2.21 |
| Helhunt Lance | [0] Synergized Assault | **0.0863** | 33 | 2.21 |
| Traitoris Lance | [0] Kill Focus | 0.0776 | 33 | 2.21 |
| Traitoris Lance | [1] Precision Strikes | 0.0707 | 33 | 2.21 |
| Hunting Warpack | [0] Pack Hunters | 0.0702 | 33 | 2.21 |

---

## Shredder Review

- ✅ FACTS: engine output, modelled explicitly
- ✅ USE CASES: mission context applied
- ✅ CONSTRAINTS: inert fields listed, Hunting Warpack caveat noted
- ✅ STRATEGY: labeled as recommendation
- ✅ Assumption registry present
- ✅ No re-computation
- ✅ No "best" without context
