# Project Roadmap — turtleatlas-w40k-11e

Three-vector (DPS/SURV/MOB) 40k unit ranking engine.
Multi-faction, data-driven, test-verified.

---

## Phase 0: Foundation ✅

### Data pipeline
- [x] BSData XML parser (`adapter/bsdata_parser.py`)
- [x] BSData + MFM point merge (`adapter/merge.py`) — with Unicode apostrophe normalization
- [x] GK merged JSON output (92 units, 26 with MFM points)
- [x] CK merged JSON (83 units)
- [x] Daemons merged JSON (84 units, 53 with MFM pricing)

### DPP Engine (`engine/dpp.py`)
- [x] `compute_weapon_dpp` — DPP vs target profile (11e rules)
- [x] Anti-Keyword, Torrent, Psychic, Lance, Extra Attacks
- [x] Rapid Fire, Blast, Melta, Heavy, Plunging Fire
- [x] Sustained Hits D3/D6, Rapid Fire D3/D6 averaging
- [x] Psychic ignores all hit modifiers (Cover, Plunging, Heavy)

### SURV + MOB
- [x] `compute_surv` — effective wounds + toughness-aware benchmark weapons
- [x] `compute_mob` — mobility score (M, FLY, DS, OC, Gate of Infinity)
- [x] 5 benchmark attackers: bolter, plasma, lascannon, melta, heavy (S14 AP-4 D6+1)
- [x] SURV bars = expected turns to die (5 heavy AT shots/turn, 100% = 5+ turns)

### Multi-Faction Architecture
- [x] `FactionConfig` + `RankingEngine` — generic, faction-agnostic
- [x] `data/config/<faction>/` JSON structure (squads, characters, vehicles, notes, supported)
- [x] Config inheritance via `_extends: "_base"` — shared target/mission/meta profiles
- [x] 3 factions: Grey Knights, Chaos Knights, Chaos Daemons
- [x] Generic CLI (archived — scripts removed, use MCP server instead)

### Test Suite
- [x] 54 tests (DPP invariants, pricing 1:1 MFM, weapon_slots)
- [x] Pricing verified per datasheet: GK 26/26, CK 19/19, Daemons 53/53

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
- [ ] Inert fields NOT applied by engine (known limitation):
  - SURV: `stealth`, `cover_save`
  - MOB: `advance_and_charge`, `fallback_and_shoot`, `fallback_and_charge`
  - DPP: `assault`, `heavy_ignore`
- [ ] Daemons data quality: `WARPTIDE/Daemonic Infestation` FNP=6 was default value (no effect) — fixed to FNP=5
- [ ] Zero-weapon fortifications (Skull Altar, Feculent Gnarlmaw) correctly show no DPP change under keyword-filtered modifiers

---

## Phase 3: More Factions 📋

In priority order:

### 3a. World Eaters
- [ ] BSData merge + MFM points
- [ ] Blessings of Khorne (random buffs — stochastic DPP)
- [ ] Berzerker squad limits
- [ ] MOB: no DS (except Eight Bound)

### 3b. Space Marines (+ Dark Angels)
- [ ] BSData merge + MFM points
- [ ] Oaths of Moment (re-roll system)
- [ ] Doctrines (Devastator → Tactical → Assault) — phased DPP

### 3c. Chaos Space Marines
- [ ] BSData merge + MFM points
- [ ] Dark Pacts (Lethal/Sustained per activation)
- [ ] Marks of Chaos

### 3d. Imperial Knights
- [ ] Towering/Plunging Fire interaction
- [ ] Bondsman abilities
- [ ] Freeblade customization

### 3e. Rest (Aeldari, Necrons, Orks, T'au, etc.)
- [ ] Per-faction data pipeline + expert files

---

## Phase 4: Output & Visualization

- [ ] Turns-based SURV bar (DONE — live)
- [ ] Cross-faction merged ranking (DONE — 50/50 DPP+SURV)
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

## Key Design Decisions

1. **Data-driven** — BSData JSON is single source of truth
2. **No composite score** — three vectors shown separately
3. **Mission weighting is post-hoc** — percentiles per target, then weighted
4. **First-unit MFM cost** — default; `--tier 3rd` for progressive
5. **Single SURV benchmark** — "heavy" (S14 AP-4 D6+1) for all units
6. **SURV bar = turns to die** — 5 heavy AT shots/turn, 100% = 5+ turns
7. **Weapon slots** — auto-resolve best loadout per target
8. **Main branch only** — no feature branches, no PRs
9. **No GW IP in repo** — mechanics-only config, no copyrighted text

---

## Current Stats

| Metric | Value |
|--------|-------|
| Factions | 3 (GK, CK, Daemons) |
| Units ranked | 101 (29 GK + 19 CK + 53 Daemons) |
| Tests | 78/80 passing (2 intentionally skipped: `test_duplicate_filters`, `test_identify_inert_fields`) |
| Detachment modifiers | 26/26 populated (9 GK + 8 CK + 9 Daemons) |
| Detachment validation tests | 19 (Tier 1 structural + Tier 2 integration) |
| Engine features | Blast, Melta, Heavy, Psychic, Torrent, Lance, Anti-Keyword, Extra Attacks, Rapid Fire, Sustained Hits, Lethal Hits, Devastating Wounds, weapon_slots, melee_penalty, _base config inheritance |
| Known inert fields | 7 (`stealth`, `cover_save`, `advance_and_charge`, `fallback_and_shoot`, `fallback_and_charge`, `assault`, `heavy_ignore`) |
