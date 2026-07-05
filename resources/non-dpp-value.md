# Non-DPP Unit Value Framework

This document describes five non-damage value vectors that affect a unit's overall
effectiveness but are not captured by DPP (Damage Per Point).

**This is a documentation and guardrails framework only.** These vectors are not yet
part of the DPP engine's scoring pipeline.

---

## 1. OC (Objective Control)

**What it is:** The OC characteristic determines how many objective markers a unit
can control during the Command phase. Units with higher OC can contest and hold
objectives against enemy units.

**Why DPP misses it:** A unit with OC=0 cannot hold objectives even if it kills every
enemy model within range. DPP measures only damage output, not scoring potential.

**Heuristic:** Point-efficient OC = OC / pts. "Action monkeys" are cheap units whose
primary function is holding or performing actions on objectives — they don't need to
kill anything to provide value.

**Current status:** OC is included in the MOB score (`compute_mob` in `engine/dpp.py`
returns `objective_control`) but is not surfaced as an independent value. The MOB
score blends movement, deep strike, and OC into a single number.

---

## 2. Screening / Board Control

**What it is:** Units that deny deep strike (within 9" of any model), block movement
corridors, cover firing lanes, or prevent enemy board access. Typically cheap,
expendable units used to create safe zones.

**Why DPP misses it:** Pure damage math does not capture board presence. A unit that
never shoots but prevents the enemy from deep striking 500pts of key units is providing
value that DPP cannot see.

**Heuristic:** Points per inch of board coverage. Cheap infantry squads provide more
screening coverage per point than expensive elite units. The value is measured by the
area denied to the opponent, not by models killed.

**Current status:** Not modelled anywhere in the engine. Entirely qualitative.

---

## 3. Durability (SURV)

**What it is:** How much punishment a unit can absorb before dying — effective wounds
at different AP levels, factoring saves, invulnerable saves, FNP, and wound count.

**Why DPP misses it:** DPP measures damage *dealt*, not damage *taken*. A durable
unit that sits on an objective and survives multiple shooting phases provides value
independent of its damage output.

**Heuristic:** Effective wounds per point (eW/pts). Compare eW at AP0, AP2, AP4 to
understand where a unit is most vulnerable.

**Current status:** Already implemented as `compute_surv` in `engine/dpp.py`. Returns
effective wounds at AP0, AP2, AP4 plus points per effective wound. Use SURV alongside
DPP for a complete picture:

- DPP tells you how much damage a unit deals per point
- SURV tells you how much damage it absorbs per point
- Together they inform trading efficiency (DPP × SURV as a crude trade metric)

**Do not use SURV as a DPP modifier** — it's a separate vector.

---

## 4. Mobility (MOB)

**What it is:** A unit's ability to move across the board — movement characteristic,
Fly, Deep Strike, Gate of Infinity, and other repositioning abilities.

**Why DPP misses it:** Damage per point is calculated at a fixed range assumption.
Mobility allows a unit to get its damage where it needs to be — a slow gunboat with
high DPP may underperform compared to a mobile unit with lower DPP that can always
be in range.

**Heuristic:** Mobility tier (skyborne > very_fast > fast > cavalry > standard > slow),
weighted by deep strike availability. A slow unit with high DPP may need a transport
to deliver its damage.

**Current status:** Already implemented as `compute_mob` in `engine/dpp.py`. Returns
a structured mobility profile with tier, flags (Fly, Deep Strike, Gate of Infinity),
OC, and keyword context. MOB is a separate vector, not a DPP modifier.

---

## 5. Action Monkey Efficiency

**What it is:** Cheap units whose primary job is to perform secondary mission
objectives (actions). Actions require a unit to forego shooting or charging, so
action monkeys are typically units with low-damage weapons that lose little by not
shooting.

**Why DPP misses it:** Actions do not deal damage. A unit's value in this role is
inversely correlated with its DPP (the best action monkeys are the ones you least
mind not shooting with).

**Heuristic:** Cheapest model count per action. Units that can action without
shooting penalty (e.g. units with no ranged weapons, or those with special rules)
have higher action efficiency.

**Current status:** Not modelled anywhere in the engine (except the "By Thought Alone"
stratagem in the GK faction pack mentions action efficiency). Entirely qualitative.

---

## Summary

| Vector | Modelled? | Where | Use |
|--------|-----------|-------|-----|
| OC | Partial | `compute_mob` (blended into MOB score) | OC/pts heuristic |
| Screening | No | — | Qualitative only |
| SURV | Yes | `compute_surv` | Effective wounds at AP0/AP2/AP4 |
| MOB | Yes | `compute_mob` | Mobility tier + flags |
| Action Monkey | No | — | Qualitative only |

All five vectors are candidates for a future combined value score, but for now DPP
remains the only quantitatively modelled metric. Always cite at least one non-DPP
consideration when evaluating a unit.
