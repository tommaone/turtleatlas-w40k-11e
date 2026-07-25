# Project Roadmap — turtleatlas-w40k-11e

Quad-vector (DPP/SURV/OBJ/MOB) Warhammer 40k 11th edition ranking engine.
28 factions, deterministic autobuilder, multi-faceted meta advisor.

**Goal:** LLM that can advise on army list building, evaluate loadouts,
and recommend detachments/units based on mission and meta.

---

## Current State (July 2026)

| Metric | Value |
|--------|-------|
| Factions ranked | 28/30 (titan-only edge cases excluded) |
| Units ranked | ~1500 |
| Tests | 641 passing, 33 skipped |
| HTML findings | 28 factions, mobile-friendly |
| Detachment modifiers | 26 (GK 9 + CK 8 + Daemons 9) |
| Characters | 282 migrated to builds format |
| Vehicles | 126 migrated to builds format |
| Last commit | `18d5eaf` — Take and Hold rebalance |

---

## Phase 0: Foundation ✅

### Data pipeline
- [x] BSData 11e JSON parser (`adapter/bsdata_parser_11e.py`)
- [x] BSData + MFM point merge (`adapter/merge.py`)
- [x] Cross-validate merged data against MFM source of truth
- [x] Strict deduplication by name+stats signature
- [x] Fuzzy name matching for unit alignment

### DPP Engine (`engine/dpp.py`)
- [x] `compute_weapon_dpp` — DPP vs target profile (11e rules)
- [x] Anti-Keyword, Torrent, Psychic, Lance, Extra Attacks
- [x] Rapid Fire, Blast, Melta, Heavy, Plunging Fire
- [x] Sustained Hits D3/D6, Rapid Fire D3/D6 averaging
- [x] Psychic ignores all hit modifiers (Cover, Plunging, Heavy)
- [x] `expected_wounds` — full wound calculation pipeline
- [x] `compute_surv` — toughness-bracketed benchmark weapons
- [x] `compute_mob` — absolute mobility score (0-100)

### Multi-Faction Architecture
- [x] `FactionConfig` + `RankingEngine` — generic, faction-agnostic
- [x] `data/config/<faction>/` JSON structure
- [x] Config inheritance via `_extends: "_base"`
- [x] Cross-faction keyword filtering in ranking.py

---

## Phase 1: Data & Engine Stability ✅

### Weapon Slots System
- [x] `_resolve_slots()` — auto-iterates all loadout combos
- [x] Character builds: `max_ranged`/`max_melee` constraints
- [x] Vehicle builds: `builds` array with ranged/melee/choices
- [x] 282 characters migrated to builds format
- [x] 25 characters with BSData wargear constraints applied
- [x] 126 vehicles migrated to builds format

### BSData Parser Fixes
- [x] Apostrophes (T'au), word order (Agents of the Imperium)
- [x] Unicode arrows (➤), Library-linked factions
- [x] Root catalogue iteration for linked factions
- [x] Cross-contamination fix (melee in ranged_choices)

### Data Quality
- [x] `damage_reduction` field in UnitDefense (14 units across 9 factions)
- [x] Overkill waste fix in `_shots_to_kill` (caps damage at wounds_per_model)
- [x] 28 invalid combined weapon entries cleaned
- [x] Knight Despoiler 6 builds (4 independent wargear slots)
- [x] Bullgryn Squad melee fix (Bullgryn maul, not Close combat weapon)

---

## Phase 2: Detachment Modifiers ✅ (partial)

### Done
- [x] Grey Knights 9/9 detachments verified
- [x] Chaos Knights 8/8 detachments verified
- [x] Chaos Daemons 9/9 detachments verified
- [x] Detachment validation test suite

### Remaining Factions (20+)
- [ ] Space Marines — need Gladius, Ironstorm, Firestorm, etc.
- [ ] Dark Angels — need Inner Circle Task Force, etc.
- [ ] All other factions — detachment modifiers not yet modeled

---

## Phase 3: Quad-Vector Ranking ✅

### Scoring System
- [x] DPP — percentile within faction
- [x] SURV — toughness-bracketed benchmark turns
- [x] OBJ — `effective_oc × survival_turns` (includes wounds_per_model, capped at 3)
- [x] MOB — absolute 0-100 scale
- [x] OC0 → OBJ=0 (hard floor)
- [x] Cost penalty — quadratic `100 × (1 - pts/2000)²`
- [x] OC0 action-capability penalty (Reconnaissance ×0.5, Disruption ×0.8)

### Mission Profiles (6)
- [x] Take and Hold: DPS 0%, SURV 35%, OBJ 55%, MOB 10%
- [x] Purge the Foe: DPS 60%, SURV 15%, OBJ 5%, MOB 20%
- [x] Reconnaissance: DPS 10%, SURV 10%, OBJ 20%, MOB 60%
- [x] Priority Assets: DPS 40%, SURV 20%, OBJ 30%, MOB 10%
- [x] Disruption: DPS 25%, SURV 15%, OBJ 25%, MOB 35%
- [x] Purge (general): DPS 60%, SURV 20%, OBJ 5%, MOB 15%

### HTML Findings
- [x] 28 faction HTMLs, mobile-friendly
- [x] Search, Top 20 summary, weighted contributions
- [x] Tag system (DS, FLY, INV, FNP, CFNP, OC+banner, COST)
- [x] Reproducible generation via `scripts/gen_findings_html.py`

---

## Phase 4: Gaps & Known Issues

### CRITICAL GAPS

#### 1. No Army Rules Modeling
**Impact:** Rankings are flat — no detachment buffs, no army-wide abilities.
**What's missing:**
- Reroll 1s to hit (common across many factions)
- +1 to wound (Argent Assault, Blood Legion)
- Sustained Hits / Lethal Hits army-wide
- FNP army-wide (Plague Legion 5+)
- Advance and charge (Hunting Warpack)
- Deep Strike army-wide (Daemonic Incursion)

**Why it matters:** Chaos Daemons look #1 in flat rankings because they have
high-OC cheap infantry + durable characters. But Thousand Sons with Psychic
army rule + rerolls would likely overtake them. Army rules change everything.

**Path forward:** Need a per-faction "army rule impact" score. See Phase 5.

#### 2. Primary Metric Problem (T3)
**Impact:** T3 units (Aeldari, Tyranids, Guard, Orks) measured vs storm_bolter
(D1). This is the weakest weapon in the game — inflates T3 survivability.
**Evidence:** Aquilons (T3 W1) had SURV=98% vs storm_bolter. In reality they
die to plasma/melta.
**Path forward:** Weighted average across benchmarks, or change T3→plasma.

#### 3. Pistol/Two-Handed Restriction Not Modeled
**Impact:** Characters can equip pistol + non-pistol simultaneously.
In 11e, pistol cannot be shot with non-pistol weapons.
**Scope:** ~50 characters with bolt pistol in loadout.
**Path forward:** Add weapon type separation to build resolver.

#### 4. Concentrated Fire Not Modeled
**Impact:** Vehicles ranked too high — engine measures SURV vs single attacker.
In practice, Redemptor draws fire from 2-3 units.
**Evidence:** Redemptor was #1 Take and Hold before quadratic cost penalty.
Still #1 in BA/DW after.
**Path forward:** Vehicle SURV penalty or "expected incoming fire" model.

#### 5. Squad Config Limitation
**Impact:** Squads support only ONE melee weapon string.
Multi-weapon squads (e.g., mixed melee) can't be modeled.
**Path forward:** Extend squad config to support melee choices like characters.

#### 6. Mortal Wound Abilities Not Modeled
**Impact:** Many units have mortal wound output that's not captured.
**Scope:** Psychic mortal wounds, Grenade stratagem, etc.

### MODERATE GAPS

#### 7. Detachment Points Budget Not Modeled
**Impact:** Can't evaluate which detachment is optimal for a given army.
In 11th, detachments cost DP (1-3 DP). Budget scales with battle size.
**Path forward:** DP budget system + detachment recommendation engine.

#### 8. Disposition Matching Not Modeled
**Impact:** Can't recommend which mission disposition to play.
Each detachment has a Force Disposition (Purge, Take Hold, etc.).
**Path forward:** Map detachments to dispositions, recommend optimal pairing.

#### 9. Requisition Thresholds Not Modeled
**Impact:** Can't evaluate whether spamming a unit is points-efficient.
3rd+ copies cost more in 11th edition.
**Path forward:** Unit count tracking + cost scaling.

#### 10. Transport Capacity Not Modeled
**Impact:** Can't evaluate which units ride in which transports.
**Path forward:** Transport capacity tracking + unit-transport pairing.

### MINOR GAPS

#### 11. Pre-existing Test Failures (detachment validation)
- 6 failures in `test_detachment_validation.py` (grey-knights/chaos-knights/chaos-daemons)
- `_source`/`_engine_note` fields not in known field set
- Pre-existing, not blocking

#### 12. test_mfm_coverage.py
- 70 pre-existing failures
- MFM coverage gaps, not blocking

---

## Phase 5: Multi-Faceted Ranking (NEXT)

### Goal
Build a composite "faction power score" that combines:
1. **Unit rankings** (current quad-vector) — what can the faction field?
2. **Army rule impact** — how much does the faction rule boost units?
3. **Detachment quality** — how good are the available detachments?
4. **Disposition coverage** — which missions can the faction play well?
5. **Meta relevance** — how does it match current tournament trends?

### Step 5.1: Army Rule Impact Score
For each faction, evaluate the impact of its army-wide rule on DPP/SURV:
- Reroll 1s to hit → +12% DPP (from p_hit improvement)
- +1 to wound → +20% DPP (from p_wound improvement)
- FNP 5+ → +33% SURV (from damage reduction)
- Sustained Hits 1 → +17% DPP (from extra hits)

This gives a "faction power multiplier" on top of flat unit rankings.

### Step 5.2: Detachment Quality Score
For each faction's detachments, evaluate:
- DP cost (1DP = cheap, 3DP = expensive)
- Modifier strength (how much DPP/SURV/MOB boost)
- Unit compatibility (which units benefit most)
- Flexibility (how many viable builds)

### Step 5.3: Disposition Coverage Matrix
For each faction × mission, compute:
- How many units rank in top 20% for that mission
- What's the average score for top units
- Coverage gaps (missions where faction is weak)

### Step 5.4: Composite Faction Score
```
Faction Score = Σ(mission_weight × unit_score × army_rule_multiplier × detachment_modifier)
```

### Step 5.5: Meta Advisor Output
For a given faction + points limit:
1. Recommend optimal disposition
2. Recommend detachment (within DP budget)
3. Recommend unit selection (top units for that mission)
4. Flag anti-synergies (units that don't benefit from detachment)

### Data Sources
- **Primary:** BSData 11e JSON (points, profiles, keywords, abilities)
- **Cross-check:** Wahapedia (validation, not primary source)
- **Meta stats:** SpikeyBits, Stat Check, WarpFriends, Tabletop Battles (tournament win rates)
- **Points:** Munitorum Field Manual (MFM) — official GW points
- **11e format:** BSData is JSON (not XML). Catalogue names differ from filenames.

---

## Phase 6: Deterministic Autobuilder

### Goal
Given a faction + mission + points, generate an optimal army list.

### Steps
1. Select disposition (best mission coverage)
2. Select detachment (within DP budget)
3. Select units (greedy: highest score/point ratio)
4. Optimize loadouts (build resolver per unit)
5. Validate constraints (detachment restrictions, points limit)

### Output
- Army list with unit names, loadouts, points
- Score breakdown per unit
- Mission-specific notes
- "Why this list" explanation

---

## Phase 7: LLM Integration

### Goal
Make the engine available as an MCP server for LLM advice.

### Tools
- `rank_faction` — ranking for a faction/mission
- `suggest_list` — army builder
- `evaluate_list` — score an existing list
- `compare_units` — side-by-side comparison
- `meta_check` — how does this faction perform in current meta?

---

## Key Design Decisions

1. **Data-driven** — BSData JSON is single source of truth
2. **Quad-vector** — DPP + SURV + OBJ + MOB shown separately
3. **Mission weighting is post-hoc** — percentiles per vector, then weighted
4. **MOB is absolute** — 0-100 scale, not percentile
5. **OBJ includes wounds_per_model** — W1 penalized, W3 rewarded (capped at 3)
6. **Cost penalty is quadratic** — 100 × (1 - pts/2000)² — expensive units properly penalized
7. **SURV benchmarks bracketed by toughness** — T3→storm_bolter, T4→plasma, etc.
8. **Build resolver** — engine picks optimal loadout per unit
9. **No GW IP** — mechanics-only config, no copyrighted text
10. **Wahapedia** — cross-check source, not primary data source
11. **Main branch only** — no feature branches

---

## Commit History (Recent)

| Hash | Description |
|------|-------------|
| `18d5eaf` | Take and Hold rebalance — MOB weight, OBJ wpm, quadratic cost_eff |
| `4773723` | Overkill waste fix — cap damage at wounds_per_model |
| `ec0d835` | damage_reduction=1 for -1D units + Bullgryn maul fix |
| `2b3841a` | Cross-contamination fix + build resolution tests |
| `5e70ff8` | All characters use builds format + validation tests |
| `3e5bafd` | Unit count accuracy + findings validation tests |
| `b199679` | Knight Despoiler loadout + vehicle builds migration |
