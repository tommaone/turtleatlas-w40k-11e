# GK Detachment Mission Analysis

Engine data from `ranking.py` with Force Disposition constraints (11e core rules). Each detachment can only be used in missions matching its disposition.

---

## Assumptions

- opponent unknown (all-comers)
- meta profile: competitive (melee_penalty 0.8)
- no cover factored into saves
- no stratagems or command rerolls
- average dice (no variance band)
- modelled: rerolls, sustained hits, lethal hits, extra AP, invuln, FNP, movement bonus
- NOT modelled: stealth, cover_save, advance_and_charge, fallback_and_shoot, fallback_and_charge, assault, heavy_ignore

---

## Force Disposition Constraints (11e)

| Disposition | Valid GK Detachments | DP |
|---|---|---|
| Purge the Foe | Warpbane Task Force (3), Brotherhood Strike (2), Argent Assault (1) | 3 / 2 / 1 |
| Take and Hold | **Hallowed Conclave** (2) | 2 |
| Priority Assets | Immaterial Interdiction (1), Sanctic Spearhead (2) | 1 / 2 |
| Disruption | Fires of Purgation (1), Banishers (2) | 1 / 2 |
| Reconnaissance | **Augurium Task Force** (2) | 2 |

Note: Take and Hold and Reconnaissance have only ONE valid detachment.

---

## Key GK Units — Raw DPP (no detachment)

| Unit | Pts | GEQ | MEQ | TEQ | Light V | Heavy V | C'tan | Knight | AC_wt |
|------|----:|----:|----:|----:|--------:|--------:|------:|-------:|------:|
| Nemesis Dreadknight | 195 | **0.1667** | **0.1218** | **0.0940** | **0.1081** | **0.0650** | **0.0854** | 0.0616 | **0.1083** |
| Paladin Squad | 215 | 0.1822 | 0.0960 | 0.0750 | 0.0551 | 0.0374 | 0.0573 | 0.0327 | 0.0837 |
| Strike Squad | 120 | 0.1812 | 0.0907 | 0.0728 | 0.0526 | 0.0367 | 0.0532 | 0.0339 | 0.0811 |
| Purifier Squad | 130 | 0.1777 | 0.0905 | 0.0706 | 0.0571 | 0.0358 | 0.0505 | 0.0368 | 0.0810 |
| Brotherhood Terminator Squad | 175 | 0.1722 | 0.0918 | 0.0711 | 0.0526 | 0.0356 | 0.0550 | 0.0305 | 0.0796 |
| Interceptor Squad | 125 | 0.1740 | 0.0870 | 0.0699 | 0.0505 | 0.0352 | 0.0510 | 0.0326 | 0.0779 |
| Purgation Squad | 110 | 0.1412 | 0.0747 | 0.0614 | 0.0531 | 0.0310 | 0.0410 | 0.0370 | 0.0682 |

### 🟡 USE CASES

**Nemesis Dreadknight** — best DPP across all targets. Fast (M8"), durable (T8, 13W), shoots and melee. The datasheet that carries GK.

**Paladin Squad** — best GEQ DPP (0.1822). Expensive (215pts) but T5, 2+, 3W makes them durable. Melee-heavy build.

**Strike Squad** — cheapest battleline (120pts). Excellent GEQ/MEQ DPP for the price. Objective holders.

**Purifier Squad** — unique: Purifying Flame gives them Anti-Infantry 2+ psychic attacks. Good MEQ efficiency at 130pts.

---

## Purge the Foe — Warpbane vs Brotherhood vs Argent Assault

Three options: Warpbane (3DP, full re-rolls), Brotherhood Strike (2DP, re-roll 1s), Argent Assault (1DP, conditional).

### 🟢 FACTS (Terminator Squad vs MEQ, DPP)

| Detachment | Choice | DPP | vs Baseline | DP |
|---|---|---|---|---|
| *(none)* | — | 0.0918 | — | — |
| **Warpbane Task Force** | [1] Purifier Zeal (full re-roll) | **0.1224** | **+33.3%** | 3 |
| Warpbane Task Force | [0] Hallowed Re-rolls (re-roll 1s) | 0.1073 | +16.8% | 3 |
| Brotherhood Strike | [0] Fury of Titan (re-roll 1s) | 0.1073 | +16.8% | 2 |
| Argent Assault | [0] Dauntless Champions | 0.0918 | 0.0% | 1 |

### 🟡 USE CASES

**Warpbane Task Force (Purifier Zeal)** — massive +33.3% DPP from full re-rolls. Requires Purifiers + Hallowed Ground positioning. Best single-detachment damage in the codex.

**Warpbane Task Force (Hallowed Re-rolls)** — re-roll 1s for all GK units. +16.8% DPP. More consistent than Purifier Zeal but lower ceiling.

**Brotherhood Strike** — same +16.8% as Warpbane's Hallowed Re-rolls, but only 2DP. Triggered after Deep Strike. Good for aggressive lists.

**Argent Assault** — 0% DPP impact from the engine. Dauntless Champions gives +1 to wound when S < T — conditional and not modelled.

### 🟠 CONSTRAINTS

- Warpbane at 3DP leaves no room for a secondary detachment
- Purifier Zeal requires units wholly within Halled Ground — positioning-dependent
- Brotherhood Strike's re-rolls only apply the turn the unit arrives from Deep Strike
- Argent Assault's Dauntless Champions is conditional (S < T) — useless vs T4 targets
- None of these give Sustained Hits or Lethal Hits — raw re-rolls only

### 🔴 STRATEGY

1. **Warpbane Task Force for max damage, Brotherhood Strike for value.** 33.3% vs 16.8% — but Warpbane costs 1DP more and locks you out of a second detachment.

2. **Brotherhood Strike + Argent Assault (2+1, Purge)** is the best general-purpose combo. Re-roll 1s after Deep Strike + Paladin wound buff. Two rules, Purge disposition.

3. **Argent Assault alone is weak.** Take it as a 1DP add-on to Brotherhood Strike, not as your primary detachment.

---

## Take and Hold — Hallowed Conclave (sole option)

Only one detachment valid: Hallowed Conclave (2DP).

### 🟢 FACTS

| Choice | Affects | Engine impact | Real-game value |
|--------|---------|:-------------:|:---------------:|
| [0] Duty Before All | dpp | **inert** (not modelled) | Medium (Terminator Fallback+shoot/charge) |
| [1] Heroic Intervention | surv | **inert** (not modelled) | Low-medium |

The engine ranks this detachment as baseline — no DPP, SURV, or MOB modifier.

### 🟡 USE CASES

**Duty Before All** — TERMINATOR units can shoot and charge after Falling Back. Valuable for Terminators stuck in combat — they can Fall Back, shoot, then charge back in. Not modelled by engine.

**Heroic Intervention** — -1 CP cost for Heroic Intervention on GK models. Utility play, not a damage buff.

### 🟠 CONSTRAINTS

- No DPP modifier available
- Both abilities are inert in the engine
- Hallowed Conclave is widely considered a weak detachment
- Take and Hold missions require objective control, not damage — Hallowed Conclave doesn't help there either

### 🔴 STRATEGY

1. **Hallowed Conclave is the weakest GK detachment.** Take it only if you must play Take and Hold and have no other choice.

2. **If you play Take and Hold frequently, build around raw datasheet efficiency** (Terminators, Dreadknight) without relying on detachment rules.

---

## Priority Assets — Immaterial Interdiction vs Sanctic Spearhead

Two options: Immaterial Interdiction (1DP, Interceptor surge) and Sanctic Spearhead (2DP, Vehicle Advance).

### 🟢 FACTS (Terminator Squad vs MEQ, DPP)

| Detachment | Choice | DPP | vs Baseline | DP |
|---|---|---|---|---|
| *(none)* | — | 0.0918 | — | — |
| Immaterial Interdiction | [0] Echojump Surge | 0.0918 | 0.0% | 1 |
| Immaterial Interdiction | [1] Astral Overlap | 0.0918 | 0.0% | 1 |
| Sanctic Spearhead | [0] Mailed Fist | 0.0918 | 0.0% | 2 |

### 🟡 USE CASES

**Immaterial Interdiction** — Echojump Surge gives Interceptors D6+1" surge move after shooting. Mobility play, not damage. 1DP budget option.

**Sanctic Spearhead** — Mailed Fist gives VEHICLE units +6" M and Assault on ranged weapons when they Advance. Good for Dreadknight lists. 2DP.

### 🟠 CONSTRAINTS

- Neither detachment gives a DPP modifier
- Echojump Surge only affects Interceptors — limited unit pool
- Mailed Fist only affects VEHICLE units — Dreadknight + transports
- Sanctic Spearhead at 2DP vs Immaterial Interdiction at 1DP — double the cost for a different utility

### 🔴 STRATEGY

1. **Immaterial Interdiction for Interceptor-heavy lists.** 1DP, surge move after shooting gives Interceptors board reach.

2. **Sanctic Spearhead for Dreadknight lists.** +6" M and Assault means Dreadknights can Advance and still shoot. Good for aggressive plays.

3. **Neither is a strong damage detachment.** Priority Assets is a weak mission for GK — take it for utility, not firepower.

---

## Disruption — Fires of Purgation vs Banishers

Two options: Fires of Purgation (1DP, Purgation buff) and Banishers (2DP, Sustained/Lethal for melee).

### 🟢 FACTS (Terminator Squad vs MEQ, DPP)

| Detachment | Choice | DPP | vs Baseline | DP |
|---|---|---|---|---|
| *(none)* | — | 0.0918 | — | — |
| Banishers | [1] Lethal Hatred | **0.1027** | **+11.8%** | 2 |
| Fires of Purgation | [0] Searing Soulflame | 0.0918 | 0.0% | 1 |
| Fires of Purgation | [1] Soul-Locked Advance | 0.0918 | 0.0% | 1 |
| Banishers | [0] Sustained Hatred | 0.0918 | 0.0% | 2 |

### 🟡 USE CASES

**Banishers (Lethal Hatred)** — +11.8% DPP from Lethal Hits on melee Psychic weapons. Good for melee-focused lists. Requires LD test to activate.

**Fires of Purgation** — Searing Soulflame gives Purgation Squad buffs. Inert in engine. Real value: Purgation Squad (115pts) as cheap Deep Strike shooting platform with Ignores Cover.

**Banishers (Sustained Hatred)** — 0% DPP. Sustained Hits on melee weapons — less valuable than Lethal for most targets.

### 🟠 CONSTRAINTS

- Banishers requires Leadership tests to activate — not always-on
- Fires of Purgation only affects Purgation Squad — limited unit pool
- Sustained Hatred is weaker than Lethal Hatred for most targets
- Disruption is a low-priority mission for GK

### 🔴 STRATEGY

1. **Banishers (Lethal Hatred) for damage, Fires of Purgation for utility.** +11.8% DPP vs free utility play.

2. **Fires of Purgation is best paired with Brotherhood Strike (2+1, Purge).** Not for Disruption — for the Purgation Squad's shooting profile.

3. **If you must play Disruption, take Banishers.** Lethal Hatred gives real DPP. Fires of Purgation gives nothing the engine can see.

---

## Reconnaissance — Augurium Task Force (sole option)

Only one detachment valid: Augurium Task Force (2DP).

### 🟢 FACTS

| Choice | Affects | Engine impact | Real-game value |
|--------|---------|:-------------:|:---------------:|
| [0] Prescient Redeployment | mob | **inert** (not modelled) | Medium (Strategic Reserves placement) |
| [1] Gate Extension | dpp | **inert** (not modelled) | Low (Gate of Infinity range increase) |

The engine ranks this detachment as baseline — no DPP, SURV, or MOB modifier.

### 🟡 USE CASES

**Prescient Redeployment** — from round 2, put a GK unit into Strategic Reserves if you didn't use max Gate of Infinity. Redeployment play, not damage.

**Gate Extension** — extends Gate of Infinity range. Mobility utility.

### 🟠 CONSTRAINTS

- No DPP modifier
- Both abilities are inert in the engine
- Reconnaissance is 60% MOB weighted — inert fields hurt here most
- Augurium Task Force is widely considered the weakest GK detachment

### 🔴 STRATEGY

1. **Augurium Task Force is the worst GK detachment.** Take it only if you must play Reconnaissance.

2. **Reconnaissance is a bad mission for GK.** 60% MOB weighting, and GK's key advantages (Psychic ignores Cover, re-rolls) are DPP-focused, not mobility-focused.

---

## Summary

| Disposition | Recommended Detachment | DP | Key | Runner-up |
|---|---|---|---|---|
| Purge the Foe | Warpbane Task Force [1] Purifier Zeal | 3 | +33.3% DPP, full re-rolls | Brotherhood Strike (2DP, +16.8%) |
| Take and Hold | Hallowed Conclave [0] Duty Before All | 2 | Fallback+shoot/charge (inert) | (sole option) |
| Priority Assets | Sanctic Spearhead [0] Mailed Fist | 2 | +6" M, Assault for vehicles | Immaterial Interdiction (1DP, surge) |
| Disruption | Banishers [1] Lethal Hatred | 2 | +11.8% DPP, lethal melee | Fires of Purgation (1DP, utility) |
| Reconnaissance | Augurium Task Force [0] Prescient Redeployment | 2 | Redeployment (inert) | (sole option) |

### Key takeaways

- **Warpbane Task Force is the strongest GK detachment** (+33.3% DPP) but costs 3DP
- **Brotherhood Strike is the best value** (+16.8% DPP for 2DP)
- **Argent Assault, Hallowed Conclave, and Augurium Task Force are inert in the engine** — they give abilities the engine cannot model
- **GK have a hole at Take and Hold and Reconnaissance** — both dispositions have only one detachment, and both are weak
- **Purge the Foe is the only competitive mission for GK** — Warpbane or Brotherhood Strike + a 1DP add-on

---

## Conclusion

### The GK detachment picture is simpler than CK

CK has 8 detachments with real DPP modifiers across all 5 dispositions. GK has 9 detachments but **only 3 give meaningful DPP boosts** (Warpbane, Brotherhood Strike, Banishers). The rest are inert in the engine.

### Purge the Foe is the only competitive mission

GK are built to kill things in melee. Their PSYCHIC keyword ignores Cover, their units hit hard, and their detachment rules amplify damage. Take and Hold, Priority Assets, Disruption, and Reconnaissance all lack meaningful DPP modifiers.

### The combo to build around

**Brotherhood Strike (2DP) + Argent Assault (1DP) = 3DP, Purge the Foe**

- Brotherhood Strike: re-roll 1s to hit/wound after Deep Strike (+16.8% DPP)
- Argent Assault: Dauntless Champions for Paladins (+1 to wound when S < T)
- Two rules, one disposition, maximum flexibility

This is the best general-purpose GK list. Warpbane Task Force is stronger (+33.3%) but locks you out of a second detachment.

### What the engine cannot see

- **Hallowed Conclave's Fallback+shoot/charge** — valuable for Terminators stuck in combat, but inert
- **Argent Assault's +1 to wound** — conditional (S < T), useless vs T4 targets
- **Augurium Task Force's redeployment** — mobility play, not damage
- **Sanctic Spearhead's +6" M** — good for Dreadknight lists, but not DPP

These abilities have real game value but the engine cannot score them. A player who frequently draws Take and Hold or Reconnaissance missions may find these detachments more useful than the numbers suggest.

### Key corrections from previous analysis

- **Warpbane Task Force does NOT "win all missions"** — it only plays Purge the Foe
- **Argent Assault is weak on its own** — take it as a 1DP add-on, not a primary detachment
- **GK have fewer competitive detachments than CK** — 3 with DPP vs CK's 5+
- **The codex has a hole at Take and Hold and Reconnaissance** — only one detachment each, both inert
