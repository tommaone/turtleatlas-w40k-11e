# Roadmap — turtleatlas-w40k-11e

Quad-vector (DPP/SURV/OBJ/MOB) Warhammer 40k 11th edition ranking engine.
30 factions, deterministic autobuilder, multi-faceted meta advisor.

**Goal:** LLM that can advise on army list building, evaluate loadouts,
and recommend detachments/units based on mission and meta.

---

## Current State

| Metric | Value |
|--------|-------|
| Factions ranked | 30/30 |
| Units ranked | ~1500 |
| Tests | 3336 passing, 36 skipped |
| HTML findings | 30 factions, mobile-friendly |
| Detachment modifiers | 26 (Grey Knights 9 + Chaos Knights 8 + Daemons 9) |
| Characters | 282 migrated builds format |
| Vehicles | 126 migrated to builds format |
| Reroll abilities auto-detected | 24 datasheets across 15 factions |
| Complex-layer squads | Aeldari, GK, Space Marines, Dark Angels, Space Wolves, Blood Angels |
| Last commit | `27681e9` — merge BA complex squad-composition migration |

---

## Done ✅

### Engine Core
- DPP engine with **quad-vector ranking** (DPP × SURV × OBJ × MOB)
- **OBJ score** = OC × survival_turns — objective holding potential
- **MOB score** = DS + Fly + movement — pure mobility (no OC)
- Weapon loader with faction overlays (Psychic/Torrent keywords)
- Invuln save support (armour vs invuln priority, AP floor)
- BSData parser with sharedProfiles resolution (entryLinks)
- Merge script (BSData + MFM) with `--faction` flag
- Detachment modifier system (WeaponModifier, DetachmentModifier)
- Meta/mission profile weighting
- **Damage reduction** — flat reduction (e.g. DWK -1D), applied in `_shots_to_kill`
- **Multi-model melee damage** — squads sum all melee profiles, characters pick best
- **DS tier upgrade** — slow+DS → fast, standard+DS → very_fast
- **Fake FNP removal** — infantry no longer get fake FNP 6+
- **OC0 fix** — OC0 units (flyers, Thunderhawk) penalized, can't dominate OBJ missions
- **Overkill cap** — damage capped at wounds_per_model in `_shots_to_kill`
- **Dual-profile weapons** — Singing Spear / Chainsabres resolve the correct
  profile per list context (ranged vs melee) via category-aware loader
- **Choice profiles score as max-over-group** — frag/krak, standard/supercharge,
  strike/sweep groups (Cyclone Missile Launcher, Plasma pistol/gun/cannon,
  Reaper chainsword, Vaultswords, Missile Launcher, Astartes grenade launcher)
  now score as max over ALL profiles instead of data-order entries[0]. The
  plain-profile preference no longer collapses distinct choice profiles, and
  the displayed base name is deterministic (prefer 'standard'/plain) so SW/SM
  resolve identically. Fixes the plasma 'standard-only' quirk and the
  under-rated missile slots.
- **Squad composition engine** — complex squad loadouts:
  - Parallel-variant models (Troupe, Windriders, Storm Guardians) — greedy
    budget allocation by damage per variant
  - Per-model weapon slots (bundle choices: e.g. "Flamer & Power Sword")
  - Multi-fixed-weapon models (Warlock: Shuriken Pistol + Destructor)
  - Melee reduction — one non-Extra-Attacks weapon per model [24.11]
  - Mixed squads with alloc minimums (Kabalite Warriors 9+Sybarite)
- **Reroll-vs-MONSTER/VEHICLE auto-detection**:
  - `engine/reroll_detect.py` — parses ability text for reroll hit/wound/damage,
    phase (melee/ranged/both), and target keywords; context-aware scanning
    (friendly/excluding/within-of ranges don't fake a target class)
  - `engine/dpp.py` — damage-reroll mean (D6 all = 4.25), applies per-target
    toughness-qualified rerolls per phase; single source of computation
  - 24 datasheets across 15 factions auto-detected; GMNDK Surge of Wrath
    configured and verified (hammer + Psycannon + Sublimator best build)

### Mission Profiles (Quad-Vector)
| Mission | DPP | SURV | OBJ | MOB |
|---------|-----|------|-----|-----|
| Take and Hold | 0% | 25% | 55% | 20% |
| Purge the Foe | 70% | 15% | 5% | 10% |
| Reconnaissance | 10% | 10% | 20% | 60% |
| Priority Assets | 40% | 20% | 30% | 10% |
| Disruption | 25% | 15% | 25% | 35% |

### Factions
- **Grey Knights** — full setup, 9 detachments, 5 dispositions ranked
- **Chaos Knights** — full setup, 8 detachments
- **Chaos Daemons** — full setup, 9 detachments
- **Space Marines** — full setup, 22 detachments (10 with modifiers), expert file, findings
  - 84 units ranked (auto-generated configs)
- **Dark Angels** — 103 units ranked, all datasheets present
  - 34 squads, 38 vehicles, 31 characters
  - DWK damage_reduction=1 configured
  - Lion El'Jonson weapon fix (Fealty=melee, Arma Luminis=ranged)
- **Blood Angels** — 33 squads migrated to the complex layer (Wave 1)
  - Sanguinary Guard per-model slots (Encarmine Blade/Spear + Inferno
    Pistol/Angelus Boltgun, target-dependent), Death Company alloc pools
  - 13 structure-only pins added; Invader ATV kept curated (no top-level
    composition entry)
- **Space Wolves** — 36 squads migrated to the complex layer (first full
  SW config; characters/vehicles already in builds format)
  - Alloc pools: Wolf Guard Terminators (storm bolter / assault cannon /
    storm shield), Wulfen (auto-launcher / Death Totem), Thunderwolf
    Cavalry (plasma / boltgun / storm shield / bolt pistol), Intercessor
    grenade launchers
  - Per-model slots: Blood Claws / Grey Hunters / Wolf Guard Terminator
    Pack Leaders, Intercessor Sergeant
  - **SW plasma quirk FIXED (2026-08-10)**: SW/SM/DA/BA plasma now resolves
    identically — choice profiles score max-over (standard/supercharge), so
    SW Intercessor Sergeant and Grey Hunter Pack Leaders take Plasma pistol
    (supercharge-scored), and the deterministic base rule displays
    'Plasma pistol - standard' everywhere.
  - Data gap: Long Fangs / Wolf Guard absent from SW merged BSData (not
    even [Legends]) — documented, not asserted
  - 7 structure-only pins added (full suite 3323 passing)
- **Aeldari** — 71 datasheets ranked; squad composition engine driven from this faction
  - Complex units modeled: Warlocks (singing spear melee), Corsairs (Voidscarred
    weapon pool), Troupe (5× fusion), Storm Guardians (n=11, platform), Kabalite
    9-alloc, Windriders parallel variants
  - 30 vehicles/characters migrated to builds format
  - Findings regenerated after every config change

### Tests
- 3336 passing, 36 skipped
- Complex-unit pins (`test_aeldari_complex_units.py`, `test_space_marines_complex_units.py`,
  `test_dark_angels_complex_units.py`, `test_space_wolves_complex_units.py`,
  `test_blood_angels_complex_units.py`) — structure asserted, no duplicated
  damage truth (engine is the single source of computation)
- Parser dual-profile assertions, generator payload tests, findings validation

### Documentation
- GK/CK/Daemons/SM/DA expert files
- Guardrails (11e rules reference)
- Non-DPP value framework

---

## In Progress 🔄

- **Squad-composition migration for ALL remaining factions** — until every
  army runs the slot setup (weapon_options/builds, slots, alloc pools), the
  engine's damage calculations are NOT determined by real gear — they use
  generic configs. Detachment modifiers are BLOCKED on this: a detachment
  bonus over an imaginary loadout is a lie. Migration is the gate.

---

## Backlog 📋

### Factions (priority order)
- [ ] Squad composition migration to remaining factions — done: Aeldari (pilot),
  GK, Space Marines, Dark Angels, Space Wolves, Blood Angels; next:
  **Black Templars / Deathwatch** (Wave 1, remaining big-marine codexes),
  then the rest of the 30 factions
- [ ] Detachment modifiers: Space Marines (Gladius, Ironstorm, Firestorm...),
  Dark Angels (Inner Circle Task Force...), all others — **BLOCKED** until
  all armies are on the slot setup (calculations must be determined by real
  gear first)

### Engine Improvements
- [x] **Reroll abilities vs target class** — auto-detected MONSTER/VEHICLE rerolls
  (24 datasheets) + generalized to CHARACTER/INFANTRY/TITANIC/WALKER/MOUNTED
  (33 datasheets): weakest-wins mode resolution (1s under-claims upgrades),
  aura-subject skip ("that X model" attacks never attach to the bearer),
  keyword/roll noun boundary fix ([DEVASTATING WOUNDS] is not a rerollable roll)
- [ ] **Army-wide (unconditional) rerolls + other army rules** — 150+ abilities
  grant rerolls with no target class ("re-roll a Hit roll of 1" unconditionally,
  auras, leading-unit buffs). Requires `targets: ALL` semantics + conditional
  exclusion (positional triggers like "within range of an objective marker").
  Flat rankings mislead without these.
- [ ] **Pistol/two-handed restriction** — pistol can't shoot with non-pistol
- [ ] **Concentrated fire** — vehicles ranked vs single attacker; expected
  incoming-fire model needed
- [ ] **Mortal wound abilities** — psychic mortals, grenade stratagems
- [ ] **Detachment points budget** — DP cost (1-3 DP), detachment recommendation
- [ ] **Disposition matching** — map detachments to Force Dispositions
- [ ] **Requisition thresholds** — 3rd+ copies cost more (11e)
- [ ] **Transport support** — model unit delivery (Rhino, Impulsor, Land Raider)
- [ ] **Multi-unit synergies** — character auras, buff stacking
- [ ] **Unit role tags** — objective holder, support, damage dealer
- [ ] **Variance bands** — ±1σ range instead of average dice
- [ ] **Points efficiency frontier** — Pareto front of DPP vs SURV vs cost

### Findings & Analysis
- [ ] Cross-faction comparison dashboard
- [ ] Meta analysis — which factions dominate which dispositions
- [ ] Points efficiency ranking across all factions

### Infrastructure
- [ ] MCP server integration for live queries
- [ ] CI/CD pipeline (automated tests on push)
- [ ] Web dashboard for rankings (nice-to-have)

---

## Known Issues 🐛

1. **Primary metric for T3** — T3 units (Aeldari, Tyranids, Guard, Orks) measured
   vs storm_bolter (D1), the weakest benchmark. Inflates T3 survivability.
   Path: weighted benchmark average or plasma for T3.
2. **`ranged_a` type** — config expects float but can get dict `{}`. Needs validation.
3. **Weapon name normalization** — mixed apostrophes (U+0027 vs U+2019) between
   config and catalog keys.

---

## Key Design Decisions

1. **Data-driven** — BSData JSON is single source of truth; MFM for points
2. **Quad-vector** — DPP + SURV + OBJ + MOB shown separately
3. **Mission weighting is post-hoc** — percentiles per vector, then weighted
4. **MOB is absolute** — 0-100 scale, not percentile
5. **OBJ includes wounds_per_model** — W1 penalized, W3 rewarded (capped at 3)
6. **Cost penalty is quadratic** — 100 × (1 - pts/2000)²
7. **SURV benchmarks bracketed by toughness** — T3→storm_bolter, T4→plasma, etc.
8. **Build resolver** — engine picks optimal loadout per unit
9. **One source of computation** — tests call the engine, never re-implement math
10. **No GW IP** — mechanics-only config, no copyrighted text
11. **Wahapedia** — cross-check source, not primary data source
12. **Main branch only** — no feature branches

---

*Last updated: 2026-08-09*
