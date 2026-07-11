# War Dog Efficiency

Engine data from `ranking.py`, `compute_surv`. 11e rules. All-comers target profiles.

---

## 🟢 FACTS

### DPP (damage per point)

| Unit | Pts | GEQ | MEQ | TEQ | Light V | Heavy V | C'tan | Knight |
|------|----:|----:|----:|----:|--------:|--------:|------:|-------:|
| War Dog Moirax | 150 | **0.1740** | 0.0955 | 0.0839 | 0.0781 | 0.0612 | 0.0829 | 0.0415 |
| War Dog Karnivore | 155 | 0.1622 | **0.1290** | **0.1050** | **0.1014** | **0.0810** | **0.1204** | **0.0423** |
| War Dog Stalker | 140 | 0.1429 | 0.1069 | 0.0885 | 0.0836 | 0.0674 | 0.0944 | 0.0357 |
| War Dog Brigand | 140 | 0.0939 | 0.0574 | 0.0557 | 0.0370 | 0.0335 | 0.0404 | 0.0209 |
| War Dog Huntsman | 140 | 0.0774 | 0.0599 | 0.0481 | 0.0460 | 0.0261 | 0.0270 | 0.0205 |
| War Dog Executioner | 130 | 0.0712 | 0.0370 | 0.0351 | 0.0262 | 0.0162 | 0.0196 | 0.0194 |

### Survivability (all War Dogs identical)

| Unit | W | T | SV | INV | EffW AP0 | EffW AP2 | EffW AP4 |
|------|---|---|----|-----|---------|---------|---------|
| All War Dogs | 14 | 9 | 3+ | none | 42 | 21 | **14** |

### Mobility

| Unit | M | OC | Tier |
|------|---|----|------|
| Brigand, Executioner, Huntsman, Moirax, Stalker | 12" | 6 | fast |
| **Karnivore** | **14"** | 6 | **very_fast** |

### Karnivore loadout picks per target

| Target | Pintle | Melee arm | Notes |
|--------|--------|-----------|-------|
| GEQ | Havoc launcher (blast) | Slaughterclaw | Launcher blast profile good vs massed infantry |
| MEQ+ | Stubber | Slaughterclaw | Stubber Sustained Hits more reliable vs smaller units |

Slaughterclaw is picked over Reaper chaintalon for ALL targets (higher S/AP/D).

### Big Knight vs War Dogs: 1× Desecrator (355pts) vs 2× Stalker (280pts)

| Target | Desecrator DPP | 2× Stalker DPP | Winner |
|--------|:-------------:|:--------------:|:------:|
| GEQ | 0.0945 | **0.1429** | Stalkers +51% |
| MEQ | 0.0830 | **0.1069** | Stalkers +29% |
| Knight | **0.0537** | 0.0357 | Desecrator +50% |

Note: 2× Stalkers costs 280pts vs Desecrator 355pts. Difference of 75pts = almost a Karnivore (155pts).

---

## 🟡 USE CASES

**Karnivore (#1 overall)** — Best DPP vs MEQ/ TEQ/ Light V/ Heavy V/ C'tan. Slaughterclaw's S12 AP-3 damages everything. M14" = very_fast, closes into melee faster than any other War Dog.

**Moirax (#1 vs hordes)** — Best GEQ DPP. Dual arm weapons (choose 2 from 5) pick Graviton pulsar ×2 vs infantry. Note: Moirax is Forge World, may not be tournament-legal in all circuits.

**Stalker (best all-rounder)** — Solid DPP on every profile. 3 weapon slots (ranged arm, melee arm, pintle) let it flex per target. Spear for MEQ+, chaincannon for hordes.

**Brigand (overrated)** — Chaincannon + spear + pintle. Decent volume but low AP/ D output. At 140pts, same as Stalker but Stalker has 2× the DPP.

**Huntsman (filler)** — Spear + meltagun + chaintalon. No high-volume anti-horde. Single-target only.

**Executioner (weakest)** — 2× autocannon only + pintle. No melee punch (armoured feet). Save 10pts, lose 50% DPP vs Stalker.

---

## 🟠 CONSTRAINTS

- Melee DPP assumes charge connects (Karnivore at 67% for 9")
- War Dogs have **no invuln save** — high-AP weapons (melta, lascannon, thermal) strip wounds fast. EffW AP4 = 14 (vs 42+ for big knights with 5++).
- Moirax dual arm weapons assume both fire at the same target (correct for single-target DPP, but real games may need to split fire)
- No detachment buffs modeled (Hunting Warpack would boost War Dogs specifically)
- Karnivore's Slaughterclaw chosen over Chaintalon for every target — engine picks correctly but model doesn't account for tactical flexibility

---

## 🔴 STRATEGY

1. **Karnivore is the competitive default.** 155pts, best DPP across 6/7 targets, M14" speed. Take 3.

2. **Moirax for horde metas.** If opponents bring 30-model infantry blobs, dual graviton Moirax out-DPPs everything.

3. **Stalker is the Brigand replacement.** Same price (140pts), 50% more DPP on every target. Never take Brigand.

4. **Don't take Executioner or Huntsman.** They fill the 130-140pt slot but deliver half the value of Stalker or Karnivore.

5. **War Dogs over Big Knights for raw damage.** 2× Stalkers (280pts) out-DPP a Desecrator (355pts) on every target except Knight-level. The 75pts savings fund a Karnivore. The trade-off: War Dogs die fast without invuln saves.

6. **When to take Desecrator over 2× Stalkers:** only when the meta is Knight-heavy and you need the durability (26W 5++ vs 14W no invuln).

**Sample War Dog packs (500pt increments):**
- 3× Karnivore (465pts, save 35pts for enhancements) — aggressive melee rush
- 2× Stalker + 1× Karnivore (435pts) — balanced all-comers
- 3× Moirax (450pts) — anti-horde skew
- 6× Karnivore (930pts) — all-in melee

### Assumptions
- Opponent unknown (all-comers)
- No cover factored into saves
- No detachment buffs
- No stratagems, command rerolls
- Average dice
- War Dog weapon options per datasheet correct (confirmed with faction expert)
