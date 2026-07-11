# Despoiler Loadout Optimisation

Engine data from `resolve_loadout('Knight Despoiler', target)` with weapon_slots optimization.

---

## 🟢 FACTS

### Weapon options

The Knight Despoiler has:

| Slot | Options | Choose |
|------|---------|:------:|
| Arms (×2) | Gatling cannon (+25pts), Battle cannon (+15pts), Thermal cannon (+20pts), Chainsword strike+sweep (+10pts), Warpstrike claw strike+sweep (+10pts) | 2 |
| Carapace | Hellstorm autocannons (0pts), Havoc missile pod (0pts), Ruinspear rocket pod (+5pts) | 1 |
| Pintle | Diabolus heavy stubber (0pts), Daemonbreath meltagun (0pts) | 1 |

Chassis base: 330pts. Total range: 350-385pts. Optimal loadouts ~370pts.

### Optimised loadouts per target

| Target | Arm weapons | Carapace | Pintle | Total pts | DPP |
|--------|------------|----------|--------|:---------:|:---:|
| GEQ | 2× Gatling cannon | Ruinspear | Meltagun | 385 | **0.1313** |
| MEQ | Gatling + Warpstrike claw | Ruinspear | Meltagun | 370 | **0.0846** |
| TEQ | Gatling + Warpstrike claw | Ruinspear | Meltagun | 370 | **0.0635** |
| Light V | Thermal cannon + Warpstrike claw | Ruinspear | Meltagun | 370 | **0.0704** |
| Heavy V | Thermal cannon + Warpstrike claw | Ruinspear | Meltagun | 370 | **0.0517** |
| C'tan | Gatling + Warpstrike claw | Ruinspear | Meltagun | 370 | **0.0638** |
| Knight | Battle cannon + Warpstrike claw | Ruinspear | Meltagun | 370 | **0.0417** |

Warpstrike claw is always picked over Reaper chainsword. Strike profile selected by max() over sweep for all these targets.

### Despoiler vs Tyrant at same price (~370pts)

| Target | Despoiler DPP | Tyrant DPP | Tyrant advantage |
|--------|:------------:|:----------:|:----------------:|
| GEQ | 0.1313 | 0.1803 | **+37%** |
| MEQ | 0.0846 | 0.1094 | +29% |
| TEQ | 0.0635 | 0.0779 | +23% |
| Light V | 0.0704 | 0.0784 | +11% |
| Heavy V | 0.0517 | 0.0608 | +18% |
| C'tan | 0.0638 | 0.0654 | +3% |
| Knight | 0.0417 | 0.0522 | +25% |

---

## 🟡 USE CASES

**Double gatling (GEQ)** — 24 shots S6 AP-1 D2, Sustained Hits 1. Anti-horde and anti-MEQ. Favoured when opponent skews light infantry.

**Gatling + claw (MEQ/TEQ/C'tan)** — Generalist. Gatling handles screens and light infantry, claw kills elites and characters. Best all-comers loadout.

**Thermal + claw (Light V/Heavy V)** — Anti-tank specialist. Thermal cannon S12 AP-3 D6+1 melta + claw S20 AP-3 D8 handle vehicles at every range.

**Battle cannon + claw (Knight)** — Battle cannon S10 AP-2 D3 (frag) or S12 AP-2 D6+1 (shell). The shell profile deals with high-T armour. Favoured when the meta is Titanic-heavy.

---

## 🟠 CONSTRAINTS

- Thermal cannon DPP assumes melta half-range
- Warpstrike claw DPP assumes strike profile (sweep is lower output for all targets shown)
- Ruinspear rocket pod has Anti-Vehicle 3+ and Anti-Monster 3+ — pure bonus vs those profiles
- Despoiler vs Tyrant comparison doesn't account for durability (Tyrant 28W 5++ vs Despoiler 26W 5++) or OC difference (10 vs 10)
- Engine optimises per target in isolation; real games need one fixed loadout for unknown opponents
- No detachment buffs modelled

---

## 🔴 STRATEGY

1. **Despoiler is flexible but outclassed.** It can fill any role depending on loadout, but Tyrant beats it on every target at every role. The Despoiler's only advantage is flexibility (swap arms per matchup).

2. **Don't take the chainsword.** Warpstrike claw outperforms it on every target — higher S (20 vs 14) and AP (-3 vs -4) and damage (8 vs 6). The chainsword's sweep profile doesn't compensate.

3. **Thermal cannon for anti-tank, gatling for anti-infantry, battle cannon for anti-knight.** The loadout picks are sensible.

4. **Always take Ruinspear + Meltagun.** Ruinspear ruins heavy infantry and vehicles. Meltagun provides a free anti-tank shot. The 5pts for Ruinspear is the best value in the list.

5. **Despoiler is a 2nd-string pick.** Take it only for fluff, model availability, or when Tyrant+s cannot fit in the list. For competitive play: Tyrant or Rampager.

### Assumptions
- Opponent unknown (all-comers)
- No cover factored into saves
- No detachment buffs
- No stratagems, command rerolls
- Melta half-range assumed active
- Average dice
