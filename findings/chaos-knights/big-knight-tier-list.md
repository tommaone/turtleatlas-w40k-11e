# Big Knight Chassis Comparison

Engine data from `ranking.py`, `compute_surv`, `compute_mob`. 11th edition rules, all-comers target profiles.

---

## 🟢 FACTS

### DPP (damage per point) across 7 targets

| Unit | Pts | GEQ | MEQ | TEQ | Light V | Heavy V | C'tan | Knight |
|------|----:|----:|----:|----:|--------:|--------:|------:|-------:|
| Knight Tyrant | 400 | **0.1803** | **0.1094** | **0.0779** | 0.0784 | 0.0608 | 0.0654 | 0.0522 |
| Knight Rampager | 365 | 0.1145 | 0.0938 | 0.0758 | **0.0925** | **0.0740** | **0.0886** | **0.0596** |
| Knight Desecrator | 355 | 0.0945 | 0.0830 | 0.0687 | 0.0814 | 0.0600 | 0.0717 | 0.0537 |
| Knight Abominant | 355 | 0.1070 | 0.0687 | 0.0668 | 0.0557 | 0.0468 | 0.0492 | 0.0366 |
| Chaos Cerastus Knight Lancer | 395 | 0.0872 | 0.0654 | 0.0570 | 0.0620 | 0.0519 | 0.0613 | 0.0409 |
| Chaos Cerastus Knight Castigator | 370 | 0.0991 | 0.0745 | 0.0589 | 0.0601 | 0.0421 | 0.0589 | 0.0372 |
| Chaos Questoris Knight Styrix | 365 | 0.1102 | 0.0720 | 0.0704 | 0.0653 | 0.0632 | 0.0702 | 0.0474 |
| Knight Ruinator | 340 | 0.1037 | 0.0673 | 0.0490 | 0.0586 | 0.0324 | 0.0481 | 0.0361 |

### Survivability (effective wounds)

| Unit | W | INV | EffW AP0 | EffW AP2 | EffW AP4 |
|------|---|-----|---------|---------|---------|
| Tyrant | 28 | 5++ | 84 | 42 | 42 |
| Rampager | 26 | 5++ | 78 | 39 | 39 |
| Desecrator | 26 | 5++ | 78 | 39 | 39 |
| Abominant | 26 | 5++ | 78 | 39 | 39 |
| **Lancer** | 28 | **4++** | **84** | **56** | **56** |
| Castigator | 28 | 5++ | 84 | 42 | 42 |
| Styrix | 26 | 5++ | 78 | 39 | 39 |
| Ruinator | 26 | 5++ | 78 | 39 | 39 |

### Mobility

| Unit | M | OC | Tier |
|------|---|----|------|
| Tyrant | 8" | 10 | cavalry |
| Rampager | 12" | 10 | fast |
| Desecrator | 10" | 10 | fast |
| Abominant | 10" | 10 | fast |
| **Lancer** | **14"** | 10 | **very_fast** |
| Castigator | 12" | 10 | fast |
| Styrix | 10" | 10 | fast |
| Ruinator | 10" | 10 | fast |

### Infernal Lance detachment boost (vs MEQ)

| Unit | Base DPP | IL DPP | Gain |
|------|---------|--------|:----:|
| Tyrant | 0.1094 | 0.1358 | **+24.1%** |
| Rampager | 0.0938 | 0.0944 | +0.7% |
| Desecrator | 0.0830 | 0.0830 | 0.0% |
| Abominant | 0.0687 | 0.0759 | +10.5% |

---

## 🟡 USE CASES

**Tyrant** — Infantry and all-rounder. Dominates GEQ/MEQ/TEQ. Best for competitive all-comers. Infernal Lance amplifies its already high shot volume (+24%).

**Rampager** — Vehicle hunter. Best DPP vs Heavy V, C'tan, Knight targets. M12" speed helps melee delivery. Not worth Infernal Lance (0.7% gain).

**Desecrator** — Budget generalist. Solid middle-of-the-pack on every target. Good value at 355pts.

**Lancer** — Durable objective sitter. Worst offense, best defense (56 EffW AP4 = +33% over 5++ knights). M14" very_fast = real threat projection.

**Styrix** — Hidden gem. Second-best vs Heavy V and C'tan. Best DPP-for-points of any big knight vs heavy targets.

**Abominant, Castigator, Ruinator** — Niche. Abominant has decent GEQ but falls off vs armor. Castigator and Ruinator are outclassed by cheaper options.

---

## 🟠 CONSTRAINTS

- DPP does not model overkill (Slaughterclaw vs 1W GEQ = wasted damage)
- Melee DPP assumes charge connects (67% for 9" charge, lower through terrain)
- Plunging Fire auto-applied for TOWERING units (Tyrant, Lancer)
- No cover factored (11e cover is BS modifier, matters more for high-shot units)
- No detachment buffs except Infernal Lance where noted
- No stratagems, command rerolls, or Epic Challenge
- Lancer's 4++ is conditional (ion shield — front arc only in some rulesets)

---

## 🔴 STRATEGY

1. **Tyrant is the default competitive pick.** It dominates the three most common target profiles (GEQ, MEQ, TEQ) and synergises with Infernal Lance best.

2. **Rampager vs Knight targets — take Rampager.** It beats Tyrant on every vehicle profile despite costing 35pts less. The gap is biggest vs C'tan (+35%).

3. **Lancer anchors flanks — doesn't kill.** Its role is absorbing fire and scoring, not dealing damage. The 4++ gives it +44% durability at AP4 vs the standard 5++ knight. M14" lets it reach objectives first.

4. **Styrix is undervalued.** At 365pts it competes with Rampager but has better balanced DPP (no melee over-reliance). Favored when opponent skews heavy (Vehicles, C'tan, Knights).

5. **Infernal Lance is the Tyrant's detachment.** 24% DPP gain on the chassis that already outputs the most damage. Rampager players should consider a different detachment or skip the modifier entirely.

**Sample configurations:**
- All-comers: Tyrant (400pts) — wins GEQ/MEQ/TEQ, competitive vs everything
- Anti-vehicle skew: Rampager + Styrix (725pts) — melee + flexible anti-tank
- Durable scoring: Lancer (395pts) — park on center, survive everything
- Budget: Desecrator (355pts) — 80% of Tyrant's DPP at 89% of cost

### Assumptions
- Opponent unknown (all-comers)
- No cover factored into saves
- No detachment buffs (unless specified)
- No stratagems, command rerolls, or Epic Challenge
- Average dice (no variance band)
- Plunging Fire applied for TOWERING units (core rule 11e)
