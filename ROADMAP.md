# Project Roadmap — turtleatlas-w40k-11e

Three-vector (DPS/SURV/MOB) 40k unit ranking engine with MCP server.
Multi-faction, data-driven, test-verified.

---

## Phase 0: Foundation ✅

### Data pipeline
- [x] BSData XML parser (`adapter/bsdata_parser.py`)
- [x] BSData + MFM point merge (`adapter/merge.py`) — with Unicode apostrophe normalization
- [x] Core Rules PDF parser (`adapter/core_rules_parser.py`)
- [x] Faction Pack PDF parser (`adapter/faction_pack_parser.py`)
- [x] GK merged JSON output (92 units, 26 with MFM points)
- [x] CK merged JSON (83 units)
- [x] Daemons merged JSON (84 units, 53 with MFM pricing)
- [x] Merge re-run: Be'lakor, Syll'Esske, Daemon Prince Of Chaos With Wings matched correctly

### DPP Engine (`engine/dpp.py`)
- [x] `compute_weapon_dpp` — DPP vs target profile (11e rules: Cover=BS mod, Psychic ignores all hit modifiers)
- [x] `UnitDefense` + `compute_surv` — effective wounds with multi-model, invuln, FNP
- [x] `compute_mob` — mobility score with M, FLY, Deep Strike, OC, Gate of Infinity
- [x] `WeaponProfile` + `TargetProfile` + `HitMode` types
- [x] Anti-Keyword support (Anti-Infantry 2+ changes wound threshold)
- [x] Torrent auto-hit handling
- [x] Psychic keyword → always `HitMode.NORMAL` (ignores Cover, Plunging Fire)
- [x] Extra Attacks: EA weapons always sum + best non-EA melee chosen
- [x] Rapid Fire: parsed as effective_attacks = base + rf_extra (assumes ≤12")
- [x] Rapid Fire D3/D6 now averaged (D3=2, D6=3) — same as Sustained Hits
- [x] Wound table: S == 0.5×T → 6+
- [x] Blast modelling: 11e [24.05] +X attacks per 5 models (model_count on all target profiles)
- [x] Melta X modelling: +X damage at half range (--melta flag)
- [x] Heavy modelling: +1 to hit if stationary (--heavy flag)
- [x] Psychic ignores Heavy bonus (per [24.29])

### Engine Bug Fixes
- [x] Null profile guard — weapons/units without stat profiles don't crash
- [x] Faction keyword check after known_units — Soul Grinder ordering fix
- [x] Pricing test apostrophe normalization (Be'lakor, Syll'Esske)
- [x] GK squad `ranged_a` double-counting — config had RF-buffed A=4, engine added RF2 again → 6 effective
- [x] Rapid Fire D3/D6 averaging (D3→+2, D6→+3 instead of fallback to +1)
- [x] Sustained Hits D3/D6 averaging (same pattern)
- [x] Anti-CHARACTER/Anti-FLY toughness ranges widened

### Data Quality Fixes
- [x] Daemon price corrections: 15 units fixed from estimates to exact MFM values
- [x] Daemon name alignment: capitalized "Of"/"On"/"The"; curly apostrophe fixes
- [x] 7 weapon name fixes: "Fire of Tzeentch" → "Fires of Tzeentch", "Attendants' hellblades" → "Attendant's hellblades", removed "Warpsword" from Soul Grinder, cleared "Daemonic claws" from Furies
- [x] 9 unit name fixes: Be'lakor, Syll'Esske apostrophe alignment; title casing
- [x] 3 config data fixes: removed Furies from Daemon config, fix Seekers duplicate "Lashing tongue", fix Hellflayers "Lashes of torment" double-count
- [x] Furies removed from Daemon config (unit not in BSData — possibly removed in 11e)

### Data-Driven Weapon Loader (`engine/weapon_loader.py`)
- [x] `WeaponCatalog` reads BSData merged JSON — single source of truth
- [x] Variant grouping (same stat sig → one profile)
- [x] Most-common default values per weapon
- [x] Unit-context-aware filtering (e.g. "Nemesis force weapon" per unit may differ)
- [x] Faction overlays for chaos-knights

### GK Three-Vector Ranking (`engine/gk_ranking.py`)
- [x] GK-only ranking with per-unit optimal loadout enumeration
- [x] Percentile bars (DPS/SURV/MOB each 0–100%)
- [x] Target-aware optimisation (`--target/-t` flag)
- [x] Mission-weighted sorting (`--mission/-m` flag)
- [x] Cross-target DPP matrix (`--matrix` flag)
- [x] Meta profile weighted optimization (`--meta` flag)
- [x] Progressive pricing: `--tier 1st|3rd` flag (1st unit vs 3rd+ unit costs)

### Knowledge Base
- [x] `resources/guardrails.md` — 11e rules reference (faction-agnostic)
- [x] `resources/experts/grey-knights.md` — GK domain expert
- [x] `resources/experts/chaos-knights.md` — CK domain expert
- [x] `resources/experts/chaos-daemons.md` — Daemon domain expert
- [x] `resources/meta-bias.md` — Mordian Glory mission bias (Purge the Foe / Take and Hold only)
- [x] `AGENTS.md` — project-level system prompt

### Git
- [x] Initial commits
- [x] Remote GitHub repo configured
- [x] PR workflow established
- [x] PR #1, #2, #3, #4 merged
- [x] PR #5 ready (engine fixy + MCP multi-faction + CK FP JSON)

---

## Phase 1: Multi-Faction Architecture ✅

### 1a. Faction Configs → JSON Data Files
- [x] `data/config/<faction>/` directory structure with JSON files
- [x] `squads.json` — squad configs (unit name, model count, default weapons, special limits)
- [x] `characters.json` — character loadouts (fixed weapons per character)
- [x] `vehicles.json` — vehicle loadouts (fixed weapon sets per vehicle)
- [x] `supported.json` — supported unit names list + target/mission/meta profiles
- [x] `weapon_options.json` — character weapon swap options
- [x] `notes.json` — per-unit notes and gotchas
- [x] GK configs (6 JSON files)
- [x] CK configs (6 JSON files) — with ally rules section
- [x] Daemon configs (6 JSON files) — all prices verified against MFM

### 1b. Generic Ranking Engine (`engine/ranking.py`)
- [x] `FactionConfig` class that loads faction config JSON at runtime
- [x] `RankingEngine` class — generic, faction-agnostic
- [x] Multi-faction support: GK, CK, Daemons all run through same engine
- [x] Mission-weighted percentile scoring
- [x] Meta profile weighted optimization
- [x] Progressive pricing: `pts_3rd` field + `_resolve_pts()` helper
- [x] `gk_ranking.py` as thin CLI wrapper (not yet retired — backward compat)

### 1c. Test Suite
- [x] `tests/` dir with pytest structure
- [x] `tests/conftest.py` — shared fixtures
- [x] `tests/test_dpp.py` — DPP computation invariants (18 tests)
- [x] `tests/test_pricing.py` — pricing 1:1 with MFM per datasheet (15 tests, 3 factions, all 3 factions: GK/CK/Daemons)
- [x] **33/33 tests passing** (maintained across all engine changes)

---

## Phase 2: Chaos Knights ✅

### 2a. Data Pipeline
- [x] Run merge for CK
- [x] Verify MFM points for CK units
- [x] Create `data/config/chaos-knights/` with squad/character/vehicle JSON
- [x] Write `resources/experts/chaos-knights.md` — CK domain expert
- [x] CK faction pack JSON (4 FP detachments + 4 codex stubs)
- [x] CK ally rules documented (Daemon allies, Dark Pacts gating)

### 2b. Ranking
- [x] Verify CK units load through generic ranking engine
- [x] CK-specific: Harbingers of Dread (Darkness = Stealth), Super-heavy Walker
- [x] CK FP detachments with DP costs: 1DP (3), 2DP (4), 3DP (1)
- [x] Progressive pricing: pts_3rd for 5 CK units

### 2c. CK-Specific Engine Rules
- [x] Daemonic Surge: no FNP for CK (unlike Daemons) — config handles via fnp_val
- [ ] Titanic units: Plunging Fire interaction (TOWERING for CK Titans)
- [ ] Harbinger of Dread: battle-shock-based mechanics
- [ ] Bondsmans: War Dog character upgrades
- [ ] Infernal Lance: Malefic Surge Empowered system (modifier choices defined)

---

## Phase 3: Additional Factions

In priority order:

### 3a. World Eaters
- [ ] BSData merge + MFM points
- [ ] Blessings of Khorne (random buffs each turn — stochastic DPP)
- [ ] Berzerker squad limits (chainaxe/plasma pistol, Eviscerator)
- [ ] MOB: no Deep Strike (except Eight Bound) — different mobility model

### 3b. Space Marines (+ Dark Angels)
- [ ] Generic SM: chapter-agnostic core (Intercessors, Hellblasters, etc.)
- [ ] Dark Angels: Deathwing + Ravenwing specific units
- [ ] Oaths of Moment (re-roll system)
- [ ] Doctrines (Devastator → Tactical → Assault) — phased DPP

### 3c. Chaos Space Marines
- [ ] BSData merge + MFM points
- [ ] Dark Pacts (Lethal Hits or Sustained Hits per activation)
- [ ] Marks of Chaos (affects weapon keywords)
- [ ] Accursed Cultists, Possessed, Chosen loadout rules

### 3d. Emperor's Children
- [ ] Noise Marines (Sonic weapons — new profile type?)
- [ ] Faction rule: always fights first / combat supremacy

### 3e. Imperial Knights
- [ ] Titanic unit MOB model (slow, no Deep Strike)
- [ ] Bondsman abilities
- [ ] Freeblade loadout customization
- [ ] Towering/Plunging Fire interaction

### 3f. Chaos Daemons ✅
- [x] BSData merge + MFM points (53 units with pricing)
- [x] Daemon faction pack JSON (9 detachments fully detailed)
- [x] Domain expert file (`resources/experts/chaos-daemons.md`)
- [x] Config JSONs (characters, squads, vehicles, weapon_options, supported, notes)
- [x] All prices verified 1:1 with MFM (53 units, Furies removed)
- [x] Progressive pricing: pts_3rd for 6 Daemon units
- [x] 9 detachments with DP costs: 1DP (4), 2DP (5)
- [x] Army rules: Shadow of Chaos, Daemonic Manifestation, Daemonic Terror
- [x] MCP server Daemon registration
- [x] Daemon allies pricing in CK merge (52 Daemon ally units with MFM prices)
- [x] **53/53 Daemon units ranked** (100% coverage minus removed Furies)

### 3g. Remaining Factions
- [ ] Aeldari, Drukhari, Necrons, Orks, T'au, etc.
- [ ] Per-faction data pipeline + expert knowledge files

---

## Phase 4: Advanced Engine

### Detachment Modifier System
- [x] DetachmentModifier dataclass + JSON-based loading from faction pack
- [x] unit_filter (name + keyword match) for per-unit modifier application
- [x] GK: Warpbane Task Force (re-roll hits), Argent Assault (+1 to wound), Immaterial Interdiction (Deep Strike buff)
- [x] CK: Infernal Lance (Malefic Surge), Bastions of Tyranny (Stealth aura)
- [ ] Daemon detachment modifiers (8/9 Daemon detachments have modifiers defined)
- [ ] Banishers: Leadership test → Sustained Hits or Lethal Hits on melee
- [ ] Brotherhood Strike: Deep Strike turn buffs (re-roll 1s to hit/wound)
- [ ] Hallowed Conclave: Terminator Fall Back + shoot/charge
- [ ] Sanctic Spearhead: Vehicle Advance 6"+ Assault
- [ ] Augurium Task Force: Gate of Infinity extension
- [ ] Fires of Purgation: Purgation battle-shock pinning
- [ ] Hunting Warpack, Helhunt Lance, Iconoclast Fiefdom, Houndpack/Lords/Traitoris Lance (CK)

### Core Rules Refinements
- [x] No T1 Reinforcements (11e rule — reduces DS mobility bonus 10→5)
- [x] GK squad `ranged_a` double-counting bug fixed (Storm bolter A=4→2 base, RF2 applied by engine)
- [x] Blast modelling (11e [24.05]: +X attacks per 5 models)
- [x] Melta half-range bonus (--melta flag)
- [x] Heavy stationary bonus (--heavy flag)
- [x] Sustained Hits D3/D6 averaging (D3=2, D6=3)
- [x] Plunging Fire for TOWERING (auto-applied, --no-plunging to disable)

### Output & Visualization
- [ ] Radar/triangle charts (DPS/SURV/MOB axes)
- [ ] Unit comparison tool (side-by-side two units)
- [ ] "What If" mode: add detachment buff, see DPP delta
- [ ] Army builder: given 2000pts + detachment, suggest units

---

## Phase 5: MCP Server & Operations

### MCP Tools
- [x] `list_factions` — list loaded factions
- [x] `get_core_rules` — core rules query
- [x] `get_ability` — ability lookup
- [x] `get_detachment` — detachment rules (with faction param)
- [x] `compute_dpp` — DPP calculation
- [x] `list_units` — list faction units (with faction param)
- [x] `get_unit` — unit profile + weapons (with faction param)
- [x] `get_stratagem` — stratagem lookup (with faction param)
- [x] `compute_surv` — survival computation
- [x] `compute_mob` — mobility computation
- [ ] `rank_units` — ranking output per faction/target/tier/mission
- [ ] `evaluate_loadout` — custom loadout DPP
- [ ] `compare_units` — side-by-side comparison
- [ ] `army_suggest` — army building suggestion
- [ ] `cross_faction` — compare units across factions
- [ ] Daemon faction registration in MCP server
- [ ] Multi-faction data loading for CK allies (Daemon cross-ref)

### CI/Operations
- [ ] GitHub Actions: pytest on push
- [ ] GitHub Actions: merge + auto-rank generation
- [ ] Snapshot regression tests
- [ ] MCP server auto-deploy

---

## Key Design Decisions

1. **Data-driven weapon loader** — single source from BSData JSON
2. **No composite score** — three vectors shown separately
3. **Mission weighting is post-hoc** — percentiles per target, then weighted by mission
4. **First-unit MFM cost** — default pricing tier; `--tier 3rd` for progressive
5. **Gate of Infinity strategic mobility** — GoI units get base 75 + modifiers
6. **Faction configs in JSON** — Python is the engine, data is the knowledge
7. **Shredder gate** — every data output self-verified before delivery
8. **Progressive pricing 1:1 with MFM** — `pts` + optional `pts_3rd` in every datasheet
9. **No estimates** — every config price sourced from MFM, verified by test
10. **No backtick fences inside JS template literals** — use 4-space indent
11. **Blast scales with target model_count** — no flag needed, automatically computed from target profile
12. **Melta/Heavy opt-in by flag** — default OFF, `--melta`/`--heavy` to activate (range/position dependent)
13. **Plunging Fire auto-applied for TOWERING** — RAW rule, `--no-plunging` to disable for edge cases
14. **GK `ranged_a` is base attacks** — config stores A=2 for Storm bolter, NOT A=4 (engine adds Rapid Fire)

---

## Current Ranking Stats

| Metric | Value |
|--------|-------|
| Total factions | 3 (Grey Knights, Chaos Knights, Chaos Daemons) |
| Total units ranked | 101 (29 GK + 19 CK + 53 Daemons) |
| Units with progressive pricing | 21 (10 GK + 5 CK + 6 Daemons) |
| Detachments with modifiers | 15 (3 GK + 2 CK + 10 Daemon) |
| Tests passing | 33/33 |
| Engine features | Blast, Melta, Heavy, Psychic, Torrent, Lance, Anti-Keyword, Extra Attacks, Rapid Fire, Sustained Hits, Lethal Hits, Devastating Wounds
