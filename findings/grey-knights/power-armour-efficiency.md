# GK Power Armour Efficiency

Engine data from `ranking.py`. 11e rules. All-comers target profiles.

---

## 🟢 FACTS

### DPP (damage per point)

| Unit | Pts | GEQ | MEQ | TEQ | Light V | Heavy V | C'tan | Knight | AC_wt |
|------|----:|----:|----:|----:|--------:|--------:|------:|-------:|------:|
| **Strike Squad** | 120 | **0.1812** | **0.0907** | **0.0728** | 0.0526 | 0.0367 | 0.0532 | 0.0339 | **0.0811** |
| Interceptor Squad | 125 | 0.1740 | 0.0870 | 0.0699 | 0.0505 | 0.0352 | 0.0510 | 0.0326 | 0.0779 |
| Purifier Squad | 130 | 0.1777 | 0.0905 | 0.0706 | **0.0571** | 0.0358 | 0.0505 | **0.0368** | 0.0810 |
| Purgation Squad | 110 | 0.1412 | 0.0747 | 0.0614 | 0.0531 | 0.0310 | 0.0410 | 0.0370 | 0.0682 |

### Survivability (all Power Armour identical)

| Unit | W | T | SV | EffW AP0 | EffW AP2 | EffW AP4 |
|------|---|---|----|---------|---------|---------|
| All GK Power Armour | 2 | 4 | 3+ | 7.5 | 5.0 | 2.5 |

### Mobility

| Unit | M | OC | Fly | Deep Strike | Tier |
|------|---|----|-----|-------------|------|
| Strike Squad | 6" | 2 | N | Y | standard |
| Interceptor Squad | 8" | 2 | N | Y | cavalry |
| Purifier Squad | 6" | 2 | N | Y | standard |
| Purgation Squad | 6" | 2 | N | Y | standard |

### PSYCHIC weapons (weapon keyword, not unit)

| Unit | PSYCHIC weapons |
|------|-----------------|
| Strike Squad | 2× Storm Bolter (NOT Psychic), Nemesis Force Weapon (Psychic) |
| Interceptor Squad | 2× Storm Bolter (NOT Psychic), Nemesis Force Weapon (Psychic) |
| Purifier Squad | Purifying Flame (Psychic), 2× Storm Bolter (NOT Psychic), Nemesis Force Weapon (Psychic) |
| Purgation Squad | Psycannon (Psychic), 2× Storm Bolter (NOT Psychic), Nemesis Force Weapon (Psychic) |

Only attacks made with PSYCHIC weapons ignore BS/WS modifiers per [24.29]. Storm Bolter attacks are affected by Cover, Plunging Fire, etc.

---

## 🟡 USE CASES

### GEQ killer: Strike Squad (0.1812)

Best GEQ DPP among all Power Armour. 120pts, BATTLELINE. The cheapest way to put models on objectives.

### MEQ killer: Strike Squad (0.0907)

Tied with Purifier Squad (0.0905) for MEQ DPP. Strike is 10pts cheaper — better value.

### Light Vehicle hunter: Purifier Squad (0.0571)

Purifying Flame gives Purifiers +1 to wound vs Infantry, but they also have 2× Incinerators. Best Light V DPP among Power Armour.

### Anti-Knight specialist: Purifier Squad (0.0368)

Purifiers beat all other Power Armour vs Knights (0.0368 vs 0.0339 for Strike). Not a good Knight-killing unit, but best of a bad lot.

### Mobile objective holder: Interceptor Squad (8")

Fastest Power Armour unit (8" M). Same DPP as Strike but with better board reach. 5pts more.

### Cheap shooting platform: Purgation Squad (110pts)

Cheapest unit in the codex. Worst DPP across most targets. Ignores Cover is useful in real games but inert in engine.

---

## 🟠 CONSTRAINTS

- No native invuln save on Power Armour — rely on Aegis Eternal stratagem (4+ invuln in Hallowed Ground)
- Grey Knights Terminator Squad has native 4+ invuln (not Brotherhood Terminators or Paladins — BSData data gap?)
- Power Armour is fragile vs AP2+ — 7.5→5.0→2.5 effective wounds
- All units have Deep Strike — can't hold objectives from turn 1
- Purifying Flame is a psychic attack — can't shoot while Battle-shocked
- Interceptor Squad's extra 2" M is marginal — doesn't change melee math

---

## 🔴 STRATEGY

1. **Strike Squad is the best Power Armour unit.** Cheapest (120pts), best GEQ/MEQ DPP, BATTLELINE for objectives. Take 2-3 units.

2. **Purifier Squad over Interceptors in most lists.** 5pts more, better DPP vs MEQ/TEQ/Knight, Purifying Flame is a real bonus. Interceptors only win on mobility.

3. **Purgation Squad is filler.** 110pts for 0.0747 MEQ DPP — the worst shooting profile in the codex. Take only if you need cheap bodies.

4. **Power Armour's job is to hold objectives and screen.** Their DPP is lower than Terminators/Dreadknight, but they're 50-100pts cheaper. They're not the damage dealers — they're the scaffolding.

---

## Key comparisons

### Strike Squad (120pts) vs Interceptor Squad (125pts)

| Target | Strike DPP | Interceptor DPP | Winner |
|--------|:----------:|:---------------:|:------:|
| GEQ | 0.1812 | 0.1740 | Strike +4% |
| MEQ | 0.0907 | 0.0870 | Strike +4% |
| TEQ | 0.0728 | 0.0699 | Strike +4% |
| AC_wt | 0.0811 | 0.0779 | Strike +4% |

Strike wins across the board. Interceptors only win on M (8" vs 6"). If you need mobility, take Interceptors; otherwise Strike.

### Strike Squad (120pts) vs Purifier Squad (130pts)

| Target | Strike DPP | Purifier DPP | Winner |
|--------|:----------:|:------------:|:------:|
| GEQ | 0.1812 | 0.1777 | Strike +2% |
| MEQ | 0.0907 | 0.0905 | Strike +0.2% |
| TEQ | 0.0728 | 0.0706 | Strike +3% |
| Light V | 0.0526 | 0.0571 | **Purifier +9%** |
| Knight | 0.0339 | 0.0368 | **Purifier +9%** |

Strike wins vs infantry. Purifier wins vs vehicles/Knights. Purifying Flame + Incinerators give Purifiers better anti-vehicle punch.
