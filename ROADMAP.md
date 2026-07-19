# Project Roadmap — turtleatlas-w40k-11e

Quad-vector (DPP/SURV/OBJ/MOB) 40k unit ranking engine.
Multi-faction, data-driven, test-verified, mobile-friendly HTML findings.

---

## Phase 0: Foundation ✅

### Data pipeline
- [x] BSData XML parser (`adapter/bsdata_parser.py`)
- [x] BSData + MFM point merge (`adapter/merge.py`) — with Unicode apostrophe normalization
- [x] GK merged JSON output (92 units, 26 with MFM points)
- [x] CK merged JSON (83 units)
- [x] Daemons merged JSON (84 units, 53 with MFM pricing)
- [x] SM/DA merged JSON

### DPP Engine (`engine/dpp.py`)
- [x] `compute_weapon_dpp` — DPP vs target profile (11e rules)
- [x] Anti-Keyword, Torrent, Psychic, Lance, Extra Attacks
- [x] Rapid Fire, Blast, Melta, Heavy, Plunging Fire
- [x] Sustained Hits D3/D6, Rapid Fire D3/D6 averaging
- [x] Psychic ignores all hit modifiers (Cover, Plunging, Heavy)

### SURV + MOB + OBJ
- [x] `compute_surv` — effective wounds + toughness-aware benchmark weapons
- [x] `compute_mob` — mobility score (M, FLY, DS, OC, Gate of Infinity)
- [x] `obj_score` — objective holding: (OC + banner_boost) × models × survival_turns
- [x] SURV benchmarks bracketed by toughness (storm_bolter → plasma → heavy_plasma → melta → lascannon → heavy)
- [x] SURV bars = expected turns to die

### Multi-Faction Architecture
- [x] `FactionConfig` + `RankingEngine` — generic, faction-agnostic
- [x] `data/config/<faction>/` JSON structure (squads, characters, vehicles, notes, supported)
- [x] Config inheritance via `_extends: "_base"` — shared target/mission/meta profiles
- [x] 5 factions: GK, CK, Daemons, DA, SM

### Test Suite
- [x] 110 tests (DPP invariants, pricing, weapon_slots, ranking, detachment validation)
- [x] Ranking test: quad-vector scoring verified

### Knowledge Base
- [x] `resources/guardrails.md`, `resources/experts/*.md` (GK, CK, Daemons)
- [x] `AGENTS.md` — project-level system prompt + IP guardrails

---

## Phase 1: Data & Engine Stability ✅

### Weapon Slots System
- [x] `_resolve_slots()` — auto-iterates all loadout combos for variable-loadout vehicles
- [x] Supports: ranged, melee, fixed, max_duplicates, per-choice pts
- [x] Applied to: Knight Despoiler (3 slots), Knight Tyrant (arm set + 3 carapace + fixed)
- [x] Backward compatible with old flat `ranged`/`melee` lists

### Melee Penalty
- [x] `melee_penalty: 0.8` for competitive/infantry/vehicle/elite metas
- [x] `melee_penalty: 1.0` for all-comers (theoryhammer)
- [x] Applied per-faction via dict format in `meta_profiles`

### IP Cleanup
- [x] All PDFs, faction-pack JSONs, core-rules JSON removed from git history
- [x] Detachment modifiers migrated to `data/config/<faction>/detachment_modifiers.json`
- [x] `.gitignore` blocks `*.pdf`, `*faction-pack*.json`, `core-rules-11e.json`
- [x] Repo: 88 MB → 267 KB
- [x] Filter-branch with backup + verification

### Git Workflow
- [x] Main branch only — no feature branches, no PRs
- [x] Direct commits to main
- [x] Changelog auto-generated from commits

---

## Phase 2: Detachment Modifiers ✅

### Grey Knights (9/9 done)
- [x] Warpbane Task Force (re-roll hits in Hallowed Ground)
- [x] Argent Assault (+1 to wound, FNP 4+ vs mortals)
- [x] Immaterial Interdiction (Interceptor surge + Stealth)
- [x] Banishers (Sustained Hits or Lethal Hits on melee)
- [x] Brotherhood Strike (re-roll 1s hit/wound after DS)
- [x] Hallowed Conclave (Terminator Fall Back + shoot/charge)
- [x] Sanctic Spearhead (Vehicle Advance 6" + Assault)
- [x] Fires of Purgation (Purgation SH1 + move/shoot)
- [x] Augurium Task Force (Gate of Infinity extension)

### Chaos Knights (8/8 done)
- [x] Bastions of Tyranny (+1 hit Tyrant vs battle-shocked)
- [x] Hunting Warpack (+1 wound + Adv/charge for War Dogs)
- [x] Iconoclast Fiefdom (board control + Stealth)
- [x] Helhunt Lance (re-roll 1s + charge FB/Adv)
- [x] Houndpack Lance (SH1 near packmates +2" M)
- [x] Lords Of Dread (Stealth + OC pressure)
- [x] Traitoris Lance (SH1 or Lethal Hits)
- [x] Infernal Lance (Malefic Surge: +3"M, SH1+Lethal, 5++/6+++)

### Chaos Daemons (9/9 done)
- [x] Daemonic Incursion (Warp Rifts DS >6")
- [x] Shadow Legion (god-specific buffs: Khorne LH, Tzeentch Stealth, etc.)
- [x] Cavalcade of Chaos (Mounted FB/shoot/charge)
- [x] Lords of the Warp (Character +1 LD/OC)
- [x] Warptide (Battleline Advance+Assault+charge)
- [x] Blood Legion (Khorne: surge move, SH1, FNP 5+)
- [x] Scintillating Legion (Tzeentch: Flux re-rolls + AP + invuln)
- [x] Plague Legion (Nurgle: SoC extension, SH1, FNP 5+)
- [x] Legion of Excess (Slaanesh: FB+charge, re-rolls, +1 wound)

### Data Fixes
- [x] Lancer INV: 5++ → 4++ (ion shield, per datasheet)
- [x] WARPTIDE/Daemonic Infestation FNP: 6 → 5 (was same as infantry default)
- [x] OC0 units → OBJ=0 (hard floor, Thunderhawk/bunkers can't score)
- [x] CK Deep Strike removed (vehicles with invuln don't get DS)
- [x] Inceptor/Suppressor OC=0 → OC=2 (data correction)
- [x] Conditional FNP support (Karanak vs Psychic)
- [x] OC boost (banner/Astartes Banner) + Legends support

### Enhancement Pricing
- CK: characters.json empty (correct — CK chars are in vehicles.json)
- GK: characters have MFM pricing (existing, verified by tests)
- Daemons: characters have MFM pricing (existing, verified by tests)

### Detachment Validation
- [x] Tier 1 structural tests (JSON schema, field types, dp_cost, uniqueness)
- [x] Tier 2 integration tests (modifier loads, applies, changes output)
- [x] Inert field detection — modifiers using only engine-ignored fields are identified
- [x] `movement_bonus` correctly changes MOB tier/score
- [x] `lethal_hits` bug fixed: was multiplying auto-wounds by p_wound (bypass wound roll entirely per 11e core)
- [x] Unit filter scoping tested against name + keyword match
- [ ] 9 test failures — pre-existing, see Known Issues below

---

## Phase 3: Quad-Vector Ranking ✅

### Scoring System
- [x] DPP — Damage per Point (percentile within faction)
- [x] SURV — Survivability turns vs toughness-bracketed benchmark weapon
- [x] OBJ — Objective holding: (OC + banner_boost) × models × survival_turns
- [x] MOB — Absolute mobility score (0-100): movement inches + DS + Fly + Gate of Infinity
- [x] OC0 → OBJ=0 (hard floor)
- [x] Cost penalty for Reconnaissance/Disruption: cost_eff = 10000/pts

### Mission Profiles
- [x] Take and Hold (DPP 0%, SURV 25%, OBJ 55%, MOB 20%)
- [x] Purge the Foe (DPP 60%, SURV 15%, OBJ 5%, MOB 20%)
- [x] Reconnaissance (DPP 10%, SURV 10%, OBJ 20%, MOB 60%)
- [x] Priority Assets (DPP 40%, SURV 20%, OBJ 30%, MOB 10%)
- [x] Disruption (DPP 25%, SURV 15%, OBJ 25%, MOB 35%)

### HTML Findings
- [x] 5 faction HTMLs with interactive tables
- [x] Search bars per mission
- [x] Top 20 summary (avg score across missions)
- [x] Weighted contribution display
- [x] Tag system (DS, FLY, INV, FNP, CFNP, OC+banner, COST)
- [x] Mission factor descriptions (playstyle + context bullets)
- [x] Mobile-friendly (verified via GitHub preview URL)
- [x] `scripts/gen_findings_html.py` for reproducible generation
- [x] `findings.json` per faction for programmatic access

---

## Phase 4: Output & Visualization

- [x] Turns-based SURV bar (DONE — live)
- [x] Cross-faction merged ranking (DONE — 50/50 DPP+SURV)
- [ ] Unit comparison tool (side-by-side)
- [ ] "What If" mode (detachment buff → DPP delta)
- [ ] Army builder (2000pts + detachment → suggestion)

---

## Phase 5: MCP Server & Ops

### MCP Tools
- [x] `list_factions`, `get_core_rules`, `get_ability`, `get_detachment`
- [x] `compute_dpp`, `list_units`, `get_unit`, `get_stratagem`
- [x] `compute_surv`, `compute_mob`
- [ ] `rank_units` — ranking per faction/target/tier/mission
- [ ] `evaluate_loadout` — custom loadout DPP
- [ ] `compare_units` — side-by-side
- [ ] `army_suggest` — army builder
- [ ] `cross_faction` — compare across factions

### CI
- [ ] GitHub Actions: pytest on push
- [ ] Snapshot regression tests
- [ ] Changelog auto-generation

---

## Known Issues 🐛

### CRITICAL: Hardcoded Deep Strike for SM/DA
**Impact:** 46 SM + 57 DA non-fly units incorrectly have Deep Strike.
**Root cause:** `get_unit_info()` in `ranking.py` hardcodes `["INFANTRY", "DEEP STRIKE"]` for all squads and `["INFANTRY", "CHARACTER", "DEEP STRIKE"]` for all characters.
**Effect:** Units like Tactical Squad, Intercessors, Devastators get MOB bonus from DS (+10 pts) when they shouldn't.
**Fix:** Add `deep_strike: true/false` to config info blocks. Check that field instead of hardcoding.
**Scope:** ~100 unit configs need `deep_strike` added. GK units mostly correct (GK infantry has DS). SM/DA need per-unit verification.
**Priority:** HIGH — inflates MOB scores for SM/DA in Reconnaissance/Disruption.

### Pre-existing Test Failures (9)
1. **`test_no_unknown_fields`** (3 factions) — `_source` and `_engine_note` not in the known field set. Fix: add them to the test's `known` set.
2. **`test_field_values_valid`** (GK) — AUGURIUM TASK FORCE has no `choices` array. Fix: add empty choices or skip detachments without choices.
3. **`test_each_modifier_has_effect`** (3 factions) — 5 daemon modifiers use only inert fields (Stealth, cover_save, etc.). These are real rules but the engine doesn't model them yet. Fix: either model the inert fields or add `_engine_note` explaining the limitation.

### Known Inert Fields (7)
The engine ignores these detachment modifier fields:
- **SURV:** `stealth`, `cover_save`
- **MOB:** `advance_and_charge`, `fallback_and_shoot`, `fallback_and_charge`
- **DPP:** `assault`, `heavy_ignore`

### Data Quality Notes
- **Nurglings OC=0** — correct per datasheet (Swarm unit)
- **SM/DA share units** — Tactical Squad, Devastators, etc. appear in both. Expected (DA is SM supplement) but inflates DA unit count.
- **Daemons 50/53 have DS** — correct (Daemonic Incursion army-wide DS)
- **GK 20/29 have DS** — correct (GK faction trait)

---

## Key Design Decisions

1. **Data-driven** — BSData JSON is single source of truth
2. **Quad-vector** — DPP + SURV + OBJ + MOB shown separately, mission weighting is post-hoc
3. **Mission weighting is post-hoc** — percentiles per vector, then weighted by mission profile
4. **MOB is absolute** — 0-100 scale based on movement inches, not percentile (same baseline across factions)
5. **OBJ = (OC + banner) × models × survival_turns** — normalised to 0-100, OC0 = hard floor
6. **Cost penalty** — Reconnaissance/Disruption penalise expensive units (cheap = more actions)
7. **First-unit MFM cost** — default; `--tier 3rd` for progressive
8. **SURV benchmarks bracketed by toughness** — T3→storm_bolter, T4→plasma, T5-6→heavy_plasma, T7-8→melta, T9-10→lascannon, T12+→heavy
9. **Weapon slots** — auto-resolve best loadout per target
10. **Main branch only** — no feature branches, no PRs
11. **No GW IP in repo** — mechanics-only config, no copyrighted text

---

## Current Stats

| Metric | Value |
|--------|-------|
| Factions | 5 (GK, CK, Daemons, DA, SM) |
| Units ranked | 381 (27 GK + 19 CK + 53 Daemons + 105 DA + 100 SM) |
| Tests | 108/117 passing (9 pre-existing detachment validation failures, 2 skipped) |
| Detachment modifiers | 26/26 populated (9 GK + 8 CK + 9 Daemons) |
| Engine features | Blast, Melta, Heavy, Psychic, Torrent, Lance, Anti-Keyword, Extra Attacks, Rapid Fire, Sustained Hits, Lethal Hits, Devastating Wounds, weapon_slots, melee_penalty, _base config inheritance, conditional FNP, OC boost, Legends support, cost penalty |
| HTML findings | 5 factions, mobile-friendly, mission factors, search, top 20 |
