# Chaos Knights Detachment Analysis Plan

**Date:** 2026-07-11
**Author:** Leonardo
**Scope:** 8 CK detachments x 3 missions (Purge the Foe, Take and Hold, Priority Assets)

---

## Executive Summary

The DPP/SURV/MOB engine gives us quantitative data for 4 of 8 detachments. The other 4 (Hunting Warpack, Iconoclast Fiefdom, Lords of Dread, Bastions of Tyranny) produce zero or near-zero engine deltas because their core abilities map to **7 inert fields** the engine doesn't compute. This plan designs a hybrid methodology that uses engine data where valid and compensates for blind spots with structured qualitative analysis.

**Critical finding:** Take and Hold is the mission most distorted by engine blind spots. Its MOB weight (30%) and SURV weight (50%) hit exactly the fields where stealth, advance+charge, and board control are inert. Any ranking for Take and Hold that relies purely on engine output will systematically underrate Hunting Warpack, Iconoclast Fiefdom, and Lords of Dread.

---

## 1. Per-Mission Framework

### 1.1 Mission Weight Matrices

The engine's existing mission profiles (from `_base.json`) provide a starting point. We extend them with a **qualitative overlay** for fields the engine can't see.

#### Purge the Foe — "Kill everything"

| Vector | Engine Weight | Qualitative Overlay | Effective Weight |
|--------|:------------:|:-------------------:|:----------------:|
| DPP | 70% | None needed | **70%** |
| SURV | 20% | +5% for stealth (survival through evasion) | **25%** |
| MOB | 10% | -5% (less relevant; you go to them) | **5%** |
| Secondary synergy | — | **+5%** (Secondaries reward kills) | **5%** |
| **Blind spot distortion** | **LOW** — DPP is well-modelled; stealth/adv+charge matter least here |

**What to measure:**
- Raw DPP vs all-comers meta profile (engine-provided)
- DPP delta per detachment choice (engine-provided)
- SURV turns-to-live against heavy AT benchmark (engine-provided)
- Secondary synergy: which secondaries does this detachment naturally score?

**Scoring method:** DPP rank order with SURV as tiebreaker. Engine data is sufficient — minimal qualitative adjustment needed.

#### Take and Hold — "Hold the line"

| Vector | Engine Weight | Qualitative Overlay | Effective Weight |
|--------|:------------:|:-------------------:|:----------------:|
| DPP | 20% | None | **20%** |
| SURV | 50% | +10% for stealth (evasion = durability) | **55%** |
| MOB | 30% | +10% for adv+charge (board reach) | **35%** |
| OC / Board Presence | — | **+10%** (mission-critical, engine-blind) | **10%** |
| Secondary synergy | — | **-20%** (folded into OC/board presence) | **-10%** |
| **Blind spot distortion** | **CRITICAL** — stealth, adv+charge, OC all inert |

**What to measure:**
- SURV effective wounds at AP0/AP2/AP4 (engine-provided)
- SURV delta for detachment invuln/FNP choices (engine-provided for Infernal Lance)
- Stealth adjustment: estimated effective SURV increase from -1 to hit (see Section 3)
- Advance+Charge adjustment: estimated board reach increase (see Section 3)
- OC per point (from compute_mob, partially modelled)
- Board presence: screening value of cheap units (DAMNED allies for Iconoclast)

**Scoring method:** Multi-vector composite. Engine SURV + qualitative stealth bonus + qualitative mobility bonus + OC assessment. This mission requires the most human judgment.

#### Priority Assets — "Protect the objective"

| Vector | Engine Weight | Qualitative Overlay | Effective Weight |
|--------|:------------:|:-------------------:|:----------------:|
| DPP | 50% | -5% (killing protects, but holding wins) | **45%** |
| SURV | 30% | +10% for stealth | **35%** |
| MOB | 20% | +5% for adv+charge (reposition to contest) | **20%** |
| OC / Durability | — | **+10%** (mission is literally about objectives) | **10%** |
| **Blind spot distortion** | **MODERATE** — stealth matters, OC matters, adv+charge moderate |

**What to measure:**
- DPP vs all-comers (engine-provided) — still important for clearing threats off objectives
- SURV with stealth overlay — units that survive on objectives win this mission
- OC assessment — which detachment gives best objective control?
- Risk: what happens when your anchor unit dies? (recovery speed)

**Scoring method:** Balanced composite with durability emphasis. Engine provides ~65% of the picture; qualitative overlays cover the rest.

---

### 1.2 Composite Scoring Formula

For each detachment × mission, compute:

```
SCORE = (w_dpp × ENGINE_DPP_RANK) +
        (w_surv × (ENGINE_SURV_RANK + STEALTH_ADJ)) +
        (w_mob × (ENGINE_MOB_RANK + ADV_CHARGE_ADJ)) +
        (w_board × BOARD_PRESENCE_SCORE)
```

Where:
- `ENGINE_*_Rank` = percentile rank from engine output (0-100)
- `STEALTH_ADJ` = qualitative bonus for detachments with stealth (see Section 3)
- `ADV_CHARGE_ADJ` = qualitative bonus for detachments with advance+charge (see Section 3)
- `BOARD_PRESENCE_SCORE` = 0-100 rating for OC/screening value (see Section 3)
- `w_*` = mission weights from tables above

**Calibration rule:** If the engine provides a delta (e.g., Helhunt Lance DPP +34%), use the delta percentage as a confidence multiplier. If the engine provides no delta (blind spot field), confidence = 0.3 (low confidence in engine ranking for that vector).

---

## 2. Per-Detachment Analysis Checklist

For each of the 8 detachments, the analyst evaluates:

### 2.1 Engine Data Audit

| Question | Source | Notes |
|----------|--------|-------|
| What is the DPP delta? (unit-level) | Engine | Run `compute_ranking` with detachment choice |
| What is the SURV delta? | Engine | Only if `invulnerable_save` or `feel_no_pain` is set |
| What is the MOB delta? | Engine | Only if `movement_bonus` > 0 |
| Which unit filter applies? | `detachment_modifiers.json` | Some abilities are War Dog-only, some Tyrant-only |
| What is the DP cost? | `detachment_modifiers.json` | 1, 2, or 3 — affects army construction |

### 2.2 Blind Spot Audit

For each inert field that this detachment uses:

| Inert Field | Detachment | Impact Assessment |
|-------------|------------|-------------------|
| `stealth` | Iconoclast Fiefdom, Lords of Dread | How much SURV delta is missing? (see Section 3) |
| `cover_save` | (none currently use this) | N/A for CK |
| `advance_and_charge` | Hunting Warpack, Helhunt Lance | How much MOB delta is missing? (see Section 3) |
| `fallback_and_shoot` | Helhunt Lance | Tactical flexibility; hard to quantify |
| `fallback_and_charge` | Helhunt Lance | Engagement recovery; hard to quantify |
| `assault` | (none currently use this) | N/A for CK |
| `heavy_ignore` | (none currently use this) | N/A for CK |

### 2.3 Unit Composition Analysis

For each detachment, answer:

1. **Which units benefit most?** (from unit_filter + ability synergy)
2. **What is the optimal army build?** (which units, how many, point budget)
3. **War Dog vs Big Knight split?** (CK has two distinct chassis classes)
4. **Loadout preferences?** (detachment may favor specific weapon types)
5. **Ally interaction?** (DAMNED allies for Iconoclast, Daemon allies for all)

### 2.4 Mission Synergy

For each detachment × mission:

1. **Primary objective synergy** — does the detachment ability directly help score primaries?
2. **Secondary synergy** — does the detachment naturally score secondaries? (e.g., kill-based secondaries favor DPP-heavy detachments; action secondaries favor cheap screening units)
3. **Turn-by-turn arc** — when does this detachment peak? (early pressure vs late-game durability)
4. **Opponent interaction** — does this detachment force the opponent to respond?

### 2.5 Risk Factors

For each detachment × mission:

1. **Terrain dependency** — does this detachment need specific terrain layouts?
2. **Matchup vulnerability** — what army comps counter this?
3. **Consistency** — how much variance in outcomes? (binary abilities vs reliable bonuses)
4. **Execution difficulty** — how hard is this to pilot? (positioning-dependent vs simple)
5. **Blind spot severity** — how wrong could the engine be? (0-10 scale)

---

## 3. Blind Spot Compensation Methodology

### 3.1 Stealth → SURV Adjustment

**How stealth works in 11e:** -1 to hit the unit. Against BS3+ attackers, this reduces hit rate from 2/3 to 1/2 (25% reduction). Against BS4+, reduction is 16.7%.

**Quantitative estimate:** Stealth is approximately equivalent to +1 save (not invuln). For a T11/26W/3+ save Big Knight:
- Base effective wounds (AP0): ~39
- With stealth equivalent (+1 save → 2+): ~52
- **Delta: +33% effective wounds**

For a T9/14W/3+ save War Dog:
- Base effective wounds (AP0): ~21
- With stealth equivalent: ~28
- **Delta: +33% effective wounds**

**Confidence:** MEDIUM. Stealth is probabilistic — it helps more against volume fire than single-shot weapons. The +33% is an upper bound; against low-BS attackers, the benefit is smaller.

**Application:** For detachments with stealth (Iconoclast Fiefdom, Lords of Dread), add +25% SURV confidence bonus. This is applied as a qualitative overlay, NOT as a SURV multiplier.

### 3.2 Advance+Charge → MOB Adjustment

**How advance+charge works:** Units can advance and still charge in the same turn. For a War Dog with M12:
- Without adv+charge: moves 12" + d6" advance = 12-18" on the advance, then cannot charge
- With adv+charge: moves 12" + d6" advance = 12-18" AND charges d6" = **total threat range 18-24"**

**Quantitative estimate:** Advance+charge approximately doubles the effective threat range for melee-focused units. For a Karnivore (M14, pure melee):
- Without: 14" move, must be within 14" to charge (after charge move)
- With: 14" + d6" advance + d6" charge = 14-26" threat range
- **Delta: ~40-85% increase in threat range**

For shooting-focused units (Brigand, Executioner): less relevant since they don't need to charge.

**Confidence:** HIGH for melee units (Karnivore, Rampager). LOW for shooting units.

**Application:** For Hunting Warpack (War Dog advance+charge), add +30% MOB confidence bonus for melee-heavy builds, +10% for shooting-heavy builds.

### 3.3 Board Presence → OC Assessment

**How board presence works in CK:** War Dogs have OC6, Big Knights have OC10. With 6-8 War Dogs + 1-2 Big Knights, a CK army typically has 46-98 OC total.

**Detachment-specific OC effects:**
- **Iconoclast Fiefdom:** DAMNED allies (Cultists at ~5pts/model, OC2) can add ~40-100 OC for ~200pts. Board control +2" move for allies. Battleshock immunity near objectives.
- **Lords of Dread:** OC bonus from battleshock pressure (enemies near you become battle-shocked, losing OC).
- **Hunting Warpack:** No direct OC effect, but advance+charge means War Dogs can reach objectives faster.

**Confidence:** MEDIUM for Iconoclast (DAMNED allies are quantifiable but engine doesn't model them). LOW for Lords of Dread (battleshock pressure is highly contextual).

### 3.4 Fallback+Shoot/Charge → Tactical Flexibility

**How fallback abilities work:** Units can Fall Back and still Shoot/Charge. This is a recovery mechanic — if a unit gets tied up in melee, it can disengage and still contribute.

**Quantitative estimate:** Hard to quantify without game simulation. Approximately +10-15% effective value for units that expect to be tagged in melee (Big Knights with Titanic can already shoot in melee via Titanic Feet, so this matters less for them).

**Confidence:** LOW. This is a situational ability that ranges from "never relevant" to "game-saving."

**Application:** Note but don't weight heavily. Flag as a differentiator when two detachments are otherwise equal.

---

## 4. Unit-Level Analysis Structure

### 4.1 CK Unit Taxonomy

```
WAR DOGS (130-155pts) — the pack
├── Shooting: Brigand (chaincannon), Executioner (autocannon), Moirax (flex)
├── Melee: Karnivore (chaintalon+claw, M14)
├── Hybrid: Huntsman (spear+chaintalon), Stalker (chaincannon+claw)
└── Characteristics: T9, SV3+, 14W, OC6, M12 (M14 Karnivore)

BIG KNIGHTS (330-400pts) — the anchors
├── Shooting: Tyrant (volcano lance, T12, 28W), Desecrator (laser destructor)
├── Melee: Rampager (chainsword+claw), Abominant (balemace+electroscourge)
├── Hybrid: Despoiler (any 2 arm weapons), Ruinator (darkflame+fellbore)
└── Characteristics: T11, SV3+, 26W, OC10, 5++ invuln, M10-12

FORGE WORLD (340-785pts) — specialists
├── Heavy: Asterius (T13, 30W, 785pts), Porphyrion (T13, 30W, 725pts)
├── Fast: Lancer (M14, shock lance, 395pts)
├── Anti-vehicle: Atrapos (lascutter+graviton, 395pts)
├── Anti-horde: Acheron (flame cannon, 370pts)
├── Elite killer: Castigator (bolt cannon 18A, 370pts)
└── Versatile: Styrix (rad+volkite+grav+claw, 365pts)
```

### 4.2 Per-Detachment Unit Synergy Matrix

| Detachment | Best War Dog | Best Big Knight | Why |
|------------|-------------|-----------------|-----|
| **Bastions of Tyranny** | Any (conditional) | Tyrant (+1 hit vs shocked) | Only Tyrant has engine filter; conditionally powerful |
| **Hunting Warpack** | Karnivore (melee + adv/charge) | Any (no filter) | Karnivore's M14 + adv+charge = 20-26" threat range |
| **Iconoclast Fiefdom** | Any (stealth aura) | Any (battleshock immunity) | Board control + DAMNED allies; stealth applies to all |
| **Helhunt LANCE** | Brigand (reroll 1s) | Desecrator (reroll 1s) | Best engine data; reroll 1s + reroll wounds 1s is +34% DPP |
| **Houndpack Lance** | Brigand (SH1 near pack) | N/A (War Dog filter) | Pack tactics; 6" aura; needs dense War Dog concentration |
| **Lords of Dread** | Any (stealth aura) | Any (OC pressure) | Stealth for all + battleshock pressure on enemies |
| **Traitoris Lance** | Brigand (SH1) | Rampager (Lethal Hits) | Flexible choice; SH1 for volume, Lethal for quality |
| **Infernal Lance** | Any (+3"M, SH1/Lethal) | Any (5++/6+++) | Most versatile; all three choices affect all units |

### 4.3 Optimal Army Builds per Detachment

For each detachment, the analyst should propose 2-3 army builds:

1. **Meta build** — optimized for competitive play (all-comers meta profile)
2. **Mission-specific build** — optimized for one of the three missions
3. **Budget build** — minimum viable force (if detachment allows lean builds)

For each build, document:
- Unit composition (names + quantities + loadouts)
- Total points
- War Dog : Big Knight ratio
- Ally inclusion (if applicable)
- DP cost of detachment choices

---

## 5. Risk Assessment Template

### Per-Detachment Risk Profile

```markdown
### [DETACHMENT NAME] — Risk Assessment

**Terrain dependency:** [LOW/MEDIUM/HIGH]
- Explanation: [does this detachment need specific terrain?]

**Matchup vulnerability:** [LOW/MEDIUM/HIGH]
- Worst matchups: [which army comps counter this?]
- Why: [mechanical reason]

**Consistency:** [LOW/MEDIUM/HIGH]
- Explanation: [how much variance? binary abilities vs reliable bonuses?]
- Variance sources: [charge rolls, battleshock tests, positioning]

**Execution difficulty:** [EASY/MEDIUM/HARD]
- Explanation: [positioning-dependent vs simple?]
- Key decisions: [what must the player get right?]

**Blind spot severity:** [0-10]
- 0 = engine captures this detachment perfectly
- 5 = engine captures ~50% of the picture
- 10 = engine is blind to the detachment's core identity
- Score: ___
- Justification: [which inert fields matter most for this detachment?]
```

### Risk Severity by Mission

| Risk Factor | Purge the Foe | Take and Hold | Priority Assets |
|-------------|:-------------:|:-------------:|:---------------:|
| Terrain dependency | Low impact | High impact | Medium impact |
| Matchup vulnerability | Medium (can always kill) | High (must hold) | High (must survive) |
| Consistency | Low (DPP is reliable) | High (board state matters) | Medium |
| Execution difficulty | Low (kill what's closest) | High (positioning critical) | Medium |
| Blind spot severity | LOW (3/10) | CRITICAL (8/10) | MODERATE (5/10) |

---

## 6. Final Recommendation Format

### Per-Mission Recommendation Block

```markdown
## [MISSION NAME] — Detachment Rankings

### Tier 1: Best fit
1. **[Detachment]** — [score]/100
   - Engine DPP rank: [X]% | Engine SURV rank: [X]% | Engine MOB rank: [X]%
   - Blind spot adjustment: [±X] (stealth: +X, adv+charge: +X, board: +X)
   - Optimal build: [brief description]
   - Why: [1-2 sentence rationale]
   - Risk: [key risk factor]

### Tier 2: Strong fit
2. ...

### Tier 3: Viable but suboptimal
...

### Blind Spot Warning
[Which detachments are most underrated by the engine for this mission?]
[What would change if we could quantify stealth/adv+charge/OC?]
```

### Cross-Mission Summary

```markdown
## Cross-Mission Detachment Assessment

| Detachment | Purge | Take&Hold | Priority | Best Mission | Engine Confidence |
|------------|:-----:|:---------:|:--------:|:------------:|:-----------------:|
| Helhunt Lance | X/100 | X/100 | X/100 | [mission] | HIGH (85%) |
| Infernal Lance | X/100 | X/100 | X/100 | [mission] | HIGH (90%) |
| ... | ... | ... | ... | ... | ... |

**Engine Confidence** = how well the engine captures this detachment's value
- HIGH (80%+): Most abilities are modelled (Helhunt, Infernal, Traitoris, Houndpack)
- MEDIUM (50-79%): Some abilities are blind (Bastions)
- LOW (<50%): Core identity is in blind spots (Hunting Warpack, Iconoclast, Lords of Dread)
```

---

## 7. Analyst Assignment

### Turtle Roles

| Turtle | Assignment | Focus |
|--------|-----------|-------|
| **Raphael** | Engine data collection | Run `compute_ranking` for all 8 detachments × 3 mission profiles × meta profile. Produce raw data tables. |
| **Donatello** | Engine enhancement (if scope permits) | Evaluate: can we add stealth/adv+charge to the engine? What's the effort? If >2hrs, skip and use qualitative overlays. |
| **Michelangelo** | Creative analysis | Army build proposals. Unexpected synergies. "What if" scenarios. Cross-detachment DP budget analysis. |
| **Leonardo** | Synthesis & recommendations | Combine engine data + qualitative overlays. Produce final rankings. Write the companion change doc. |

### Data Collection Checklist (for Raphael)

For each detachment × choice:
1. Run `python3 run_dpp.py --faction chaos-knights --detachment "<name>" --choice <N> --meta competitive`
2. Capture: DPP, SURV (effective wounds), MOB score, mission score
3. Run with all three mission profiles
4. Produce a comparison table: base vs each detachment choice
5. Flag any detachment where the engine shows zero delta (blind spot confirmation)

### Expected Engine Output Gaps

| Detachment | Choice | Expected Engine Delta | Blind Spot |
|------------|--------|:---------------------:|:----------:|
| Bastions of Tyranny | Annihilate the Unworthy | DPP: small (+1 hit, conditional, Tyrant only) | Condition rarely met |
| Hunting Warpack | Pack Hunters | DPP: moderate (+1 wound, charging) | +1 wound IS modelled |
| Hunting Warpack | Relentless Pursuit | MOB: ZERO | advance_and_charge INERT |
| Iconoclast Fiefdom | Board Control | MOB: small (+2" move) | +2" IS modelled; battleshock immunity INERT |
| Iconoclast Fiefdom | Darkness Cloak | SURV: ZERO | stealth INERT |
| Helhunt Lance | Synergized Assault | DPP: +34% (0.0863 vs 0.0645) | Fully modelled |
| Helhunt Lance | Unstoppable Advance | MOB: ZERO | advance_and_charge + fallback INERT |
| Houndpack Lance | Pack Alpha | DPP: moderate (SH1, War Dogs only) | Fully modelled |
| Houndpack Lance | Swift Predators | MOB: small (+2" M) | Fully modelled |
| Lords of Dread | Dread Aura | SURV: ZERO | stealth INERT |
| Lords of Dread | Terror Tactics | MOB: small (+2" M) | OC bonus from battleshock INERT |
| Traitoris Lance | Kill Focus | DPP: +20% (SH1) | Fully modelled |
| Traitoris Lance | Precision Strikes | DPP: moderate (Lethal Hits) | Fully modelled |
| Infernal Lance | Diabolic Power | DPP: +30% (SH1+Lethal) | Fully modelled |
| Infernal Lance | Unnatural Fortitude | SURV: +27% (42 vs 33) | Fully modelled |
| Infernal Lance | Unholy Hunger | MOB: moderate (+3" M) | Fully modelled |

---

## 8. Execution Timeline

| Step | Owner | Time Est | Output |
|------|-------|----------|--------|
| 1. Engine data collection | Raphael | 30 min | Raw ranking tables for all detachments |
| 2. Blind spot compensation estimates | Leonardo | 20 min | Section 3 refinement with actual numbers |
| 3. Army build proposals | Michelangelo | 45 min | 2-3 builds per detachment |
| 4. Risk assessment per detachment | Leonardo | 20 min | Completed risk templates |
| 5. Cross-mission synthesis | Leonardo | 30 min | Final ranking tables |
| 6. Companion change doc | Leonardo | 15 min | BA/PO-facing document |
| **Total** | | **~2.5 hrs** | Complete detachment analysis |

---

## 9. Open Questions

1. **DP budget constraint:** Can a CK army take 2-3 detachment choices? (DP cost varies: 1, 2, or 3). How does DP budget affect which combinations are legal?
2. **Forge World inclusion:** Should we analyze Forgeworld units (Asterius, Porphyrion, Lancer, etc.) or focus on plastic range? FW units are less commonly seen in competitive play.
3. **Ally integration:** Should we model DAMNED allies for Iconoclast Fiefdom quantitatively, or keep it qualitative?
4. **Harbingers of Dread:** This is a CK army-wide rule (Darkness aura → Stealth for all CK units within 6"). It's NOT a detachment rule — it's universal. Does this change our stealth analysis? (Answer: partially — it means ALL CK detachments get SOME stealth, but Iconoclast/Lords extend it or make it more impactful.)
5. **Malefic Surge:** Infernal Lance has a mortal wound risk from Empowered abilities. Should we factor this into SURV? (Answer: yes, as a risk factor, not as a SURV modifier.)

---

## Appendix A: Engine Command Reference

```bash
# Run all detachments for CK
python3 run_dpp.py --faction chaos-knights --meta competitive

# Run specific detachment
python3 run_dpp.py --faction chaos-knights --detachment "HELHUNT LANCE" --choice 0 --meta competitive

# Run with mission weighting
python3 run_dpp.py --faction chaos-knights --mission "Purge the Foe" --meta competitive

# Run for specific target
python3 run_dpp.py --faction chaos-knights --target MEQ --detachment "INFERNAL LANCE" --choice 1
```

## Appendix B: Inert Fields Quick Reference

| Field | Category | Detachments Affected | Impact |
|-------|----------|---------------------|--------|
| `stealth` | SURV | Iconoclast Fiefdom, Lords of Dread | -1 to hit = ~33% SURV increase |
| `cover_save` | SURV | (none) | N/A |
| `advance_and_charge` | MOB | Hunting Warpack, Helhunt Lance | ~40-85% threat range increase (melee) |
| `fallback_and_shoot` | MOB | Helhunt Lance | Situational recovery |
| `fallback_and_charge` | MOB | Helhunt Lance | Situational recovery |
| `assault` | DPP | (none) | N/A — advance & shoot |
| `heavy_ignore` | DPP | (none) | N/A — ignore Heavy penalty |
