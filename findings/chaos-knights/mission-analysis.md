# CK Detachment Mission Analysis

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

| Disposition | Valid CK Detachments | DP |
|---|---|---|
| Purge the Foe | Infernal Lance (3), Traitoris Lance (2) | 3 / 2 |
| Take and Hold | **Iconoclast Fiefdom** (1) | 1 |
| Priority Assets | **Lords of Dread** (2) | 2 |
| Disruption | Bastions of Tyranny (1), Helhunt Lance (2) | 1 / 2 |
| Reconnaissance | Hunting Warpack (1), Houndpack Lance (2) | 1 / 2 |

Note: Some dispositions have only ONE valid detachment — "take it or leave it."

---

## Purge the Foe — Infernal Lance vs Traitoris Lance

Two options: Infernal Lance (3DP, SH1+Lethal) and Traitoris Lance (2DP, SH1 OR Lethal).

### 🟢 FACTS (Tyrant vs MEQ, DPP)

| Detachment | Choice | DPP | vs Baseline | DP |
|---|---|---|---|---|
| *(none)* | — | 0.1358 | — | — |
| Infernal Lance | [1] Diabolic Power (SH1+Lethal) | **0.1690** | **+24.4%** | 3 |
| Traitoris Lance | [0] Kill Focus (SH1) | **0.1634** | +20.3% | 2 |
| Traitoris Lance | [1] Precision Strikes (Lethal) | 0.1502 | +10.6% | 2 |

### 🟢 FACTS (Tyrant vs Heavy V, DPP with Infernal Lance)

| Target | No detachment | Infernal Lance | Gain |
|--------|:------------:|:--------------:|:----:|
| MEQ | 0.1358 | 0.1690 | +24.4% |
| Heavy V | 0.0608 | 0.0843 | +38.7% |
| Knight | 0.0522 | 0.0782 | +49.8% |

### 🟡 USE CASES

**Infernal Lance** — max damage output. SH1 + Lethal on all attacks gives the biggest raw DPP boost in the codex (+24%). Scales with target toughness (Lethal auto-wounds matter more vs T12+). 3DP leaves room for only 1 enhancement.

**Traitoris Lance (Kill Focus)** — budget Infernal. Only 3.4% less DPP at 2DP (save 1 enhancement). Good for competitive play where enhancements win games. Must pick between SH1 and Lethal; can't have both.

**Traitoris Lance (Precision Strikes)** — Lethal-only is weaker than SH1. Skip this choice.

### 🟠 CONSTRAINTS

- Infernal Lance's Diabolic Power gives SH1 + Lethal on **all** attacks (ranged + melee) — see war-dog-efficiency.md for War Dog impact
- Infernal Lance's Hazardous self-damage (3MW per hit roll of 1) is NOT modelled by the engine — add ~2 MW/turn to the Despoiler
- Traitoris Lance cannot stack SH1 + Lethal; picks only one

### 🔴 STRATEGY

1. **Infernal Lance for raw power, Traitoris Lance for flexibility.** 3.4% DPP difference is small. If you need 3 enhancements (character-heavy list), take Traitoris Lance and save 1DP.

2. **Kill Focus (SH1) > Precision Strikes (Lethal).** SH1 gives more overall DPP (+20.3% vs +10.6%). Lethal only helps vs T12+ targets.

3. **Infernal Lance Lethal matters most vs vehicles.** The +49.8% gain vs Knights is from auto-wounding on 6s — bypassing the Tyrant's "only S9+" wound problem.

4. **Diabolic Power + Unnatural Fortitude is your combo.** Infernal Lance gets 3 choices. Pick Diabolic Power for DPP and Unnatural Fortitude for SURV (5++/6+++). Skip Unholy Hunger (+3" move) unless you're running War Dogs that need board reach.

---

## Take and Hold — Iconoclast Fiefdom (sole option)

Only one detachment valid: Iconoclast Fiefdom (DP1). Two choices but one is inert in the engine.

### 🟢 FACTS

| Choice | Affects | Engine impact | Real-game value |
|--------|---------|:-------------:|:---------------:|
| [0] Board Control (+2" move) | mob | +2" on M value | Medium |
| [1] Darkness Cloak (Stealth) | surv | **inert** (not modelled) | Medium-low (cover is common in 11e) |

The engine ranks this detachment as baseline (no DPP boost, only +2" MOB from Board Control).

### 🟡 USE CASES

**Board Control** — +2" movement helps War Dogs reach objectives faster. Iconoclast Fiefdom also grants access to DAMNED allies (Cultists, Traitor Guard) for cheap objective play.

**Darkness Cloak** — Stealth gives -1 to hit vs ranged. Inert in the engine, but worth ~17% damage reduction in reality. Combine with cover for -2 to hit.

### 🟠 CONSTRAINTS

- No DPP modifier available (unlike Infernal Lance / Helhunt Lance)
- Stealth field is inert — engine cannot score surivivability from it
- DAMNED allies do NOT benefit from CK detachment rules or Harbingers of Dread
- DP1 = budget option, can take multiple detachments

### 🔴 STRATEGY

1. **Iconoclast Fiefdom is your only Take and Hold option.** Take it or don't play Take and Hold.

2. **Board Control for War Dog spams.** +2" movement matters most for M12" War Dogs reaching objectives T1.

3. **DAMNED allies stretch your board presence.** 50pt Cultist units screen and hold home objectives while Knights push forward.

4. **Without an engine-visible DPP boost, the Knights themselves don't hit harder.** Your damage is whatever the datasheets provide.

---

## Priority Assets — Lords of Dread (sole option)

Only one detachment valid: Lords of Dread (DP2). Two choices, both partially inert.

### 🟢 FACTS

| Choice | Affects | Engine impact | Real-game value |
|--------|---------|:-------------:|:---------------:|
| [0] Dread Aura (Stealth) | surv | **inert** (not modelled) | Low (cover in 11e) |
| [1] Terror Tactics (+2" move) | mob | +2" on M value | Medium |

### 🟡 USE CASES

**Dread Aura** — Stealth aura from Harbingers of Dread Darkness (6 on D6 roll). Gives -1 to hit within 9" of a Dread-active Knight. Unreliable (D6 roll) and redundant with cover.

**Terror Tactics** — +2" movement from battleshock pressure. Boosts MOB but required enemy battleshock to activate.

### 🟠 CONSTRAINTS

- No DPP modifier
- Dread Aura is RNG-gated (D6 roll for Darkness)
- Terror Tactics depends on enemy battleshock
- Lords of Dread is widely considered the weakest CK detachment

### 🔴 STRATEGY

1. **Lords of Dread is the weakest option in the codex.** Take it only if you must play Priority Assets and have no other choice.

2. **If you play Priority Assets frequently, consider which other factions' detachments might offer better CK-aligned cards.** Or build around raw datasheet efficiency (Tyrant + Karnivores) without relying on detachment rules.

---

## Disruption — Bastions of Tyranny vs Helhunt Lance

Two options: Bastions (DP1, +1 to hit vs battle-shocked) and Helhunt Lance (DP2, re-roll 1s to hit and wound).

### 🟢 FACTS (Tyrant vs MEQ, DPP)

| Detachment | Choice | DPP | vs Baseline | DP |
|---|---|---|---|---|
| *(none)* | — | 0.1358 | — | — |
| Bastions of Tyranny | [0] Annihilate the Unworthy | 0.1372 | +1.0% | 1 |
| **Helhunt Lance** | [0] Synergized Assault | **0.1814** | **+33.6%** | 2 |

### 🟡 USE CASES

**Helhunt Lance** — massive DPP boost from re-roll 1s to hit AND wound. Requires mixed force (War Dog + BIG KNIGHT) on the battlefield. Tyrant benefits the most (most shots = most re-roll value).

**Bastions of Tyranny** — +1 to hit vs battle-shocked only. Near-zero impact if opponent isn't battleshocked. The Tyrant-specific restriction further limits it.

### 🟠 CONSTRAINTS

- Helhunt requires mixed War Dog + Titanic units both alive — if one dies, the modifer stops
- Bastions' condition is hard to control (opponent must fail battleshock)
- Helhunt at DP2 vs Bastions at DP1 — 1 DP difference matters for list building

### 🔴 STRATEGY

1. **Helhunt Lance is the strongest DPP boost in the CK codex (+33.6%).** But it's locked to Disruption missions only.

2. **Bastions is nearly worthless.** +1.0% conditional DPP. Skip it unless you need a DP1 detachment.

3. **If you play Disruption, take Helhunt Lance without question.**

---

## Reconnaissance — Hunting Warpack vs Houndpack Lance

Two options: Hunting Warpack (DP1, +1 to wound on charge for War Dogs) and Houndpack Lance (DP2, +1 SH + +2" move for War Dogs).

### 🟢 FACTS

| Detachment | Choice | Engine rank | DP |
|---|---|---|---|
| Hunting Warpack | [0] Pack Hunters (+1 to wound on charge) | baseline (War Dog only) | 1 |
| Hunting Warpack | [1] Relentless Pursuit (A&C) | inert (not modelled) | — |
| Houndpack Lance | [0] Pack Alpha (+1 SH near packmates) | baseline + small DPP | 2 |
| Houndpack Lance | [1] Swift Predators (+2" move) | +2" MOB | — |

### 🟡 USE CASES

**Hunting Warpack** — cheap (DP1). War Dogs only (no big knights). Pack Hunters gives +1 to wound on charge — significant for S8 claw vs T12 targets (5+ → 4+). Relentless Pursuit (A&C) is inert but valuable for board reach.

**Houndpack Lance** — more expensive (DP2). Pack Alpha gives +1 Sustained Hits for War Dogs near each other. Swift Predators +2" move. Better for War Dog spam.

### 🟠 CONSTRAINTS

- Hunting Warpack is War Dogs ONLY — engine can't model the unit restriction
- War Dogs have no invuln (EffW AP4 = 14 vs 42 for big knights)
- Relentless Pursuit (A&C) is inert — engine gives it no MOB credit
- Reconnaissance is 60% MOB weighted — inert fields hurt here most

### 🔴 STRATEGY

1. **Hunting Warpack is the better value** (DP1). Pack Hunters gives +1 to wound on charge which matters vs armour. Relentless Pursuit gives A&C but is unscored by the engine.

2. **Houndpack Lance is stronger on paper** but costs double the DP. Only take if you have spare DP and need the +2" move.

3. **Reconnaissance is a bad mission for CK.** 60% MOB weighting, and CK's inert A&C/Stealth fields mean the engine cannot see your advantages. Real-game value may be higher than the numbers show.

---

## Summary

| Disposition | Recommended Detachment | DP | Key | Runner-up |
|---|---|---|---|---|
| Purge the Foe | Infernal Lance [1] Diabolic Power | 3 | +24.4% DPP, SH1+Lethal | Traitoris Lance (3.4% less, 1DP cheaper) |
| Take and Hold | Iconoclast Fiefdom [0] Board Control | 1 | +2" move, DAMNED allies | (sole option) |
| Priority Assets | Lords of Dread [1] Terror Tactics | 2 | +2" move (conditional) | (sole option) |
| Disruption | Helhunt Lance [0] Synergized Assault | 2 | +33.6% DPP, re-roll 1s | Bastions of Tyranny (skip) |
| Reconnaissance | Hunting Warpack [0] Pack Hunters | 1 | +1 to wound on charge | Houndpack Lance (DP2, +1 SH) |

### Key corrections from previous analysis

- **Infernal Lance does NOT "win all 3 missions"** — it only plays Purge the Foe
- **Helhunt Lance is the strongest DPP detachment in the codex** (+33.6%) but locked to Disruption
- **Some dispositions have only one detachment** — there is no competition for Take and Hold or Priority Assets
- **No detachment gives both DPP + SURV boosts** (unlike what the old analysis claimed)
- **The codex has a hole at Reconnaissance** — both options are War Dog-focused and the key advantages (A&C, advance mechanics) are inert in the engine
