# Project Roadmap — turtleatlas-w40k-11e

Three-vector (DPS/SURV/MOB) 40k unit ranking engine with MCP server.
Multi-faction, data-driven, test-verified.

---

## Phase 0: Foundation ✅

### Data pipeline
- [x] BSData XML parser (`adapter/bsdata_parser.py`)
- [x] BSData + MFM point merge (`adapter/merge.py`)
- [x] Core Rules PDF parser (`adapter/core_rules_parser.py`)
- [x] Faction Pack PDF parser (`adapter/faction_pack_parser.py`)
- [x] GK merged JSON output (92 units, 26 with MFM points)
- [x] 9/9 GK detachments in data (4 FP + 5 codex)

### DPP Engine (`engine/dpp.py`)
- [x] `compute_weapon_dpp` — DPP vs target profile (11e rules: Cover=BS mod, Psychic ignores all hit modifiers)
- [x] `UnitDefense` + `compute_surv` — effective wounds with multi-model, invuln, FNP
- [x] `compute_mob` — mobility score with M, FLY, Deep Strike, OC, Gate of Infinity
- [x] `WeaponProfile` + `TargetProfile` + `HitMode` types
- [x] Anti-Keyword support (Anti-Infantry 2+ changes wound threshold)
- [x] Torrent auto-hit handling
- [x] Psychic keyword → always `HitMode.NORMAL` (ignores Cover, Plunging Fire)

### Data-Driven Weapon Loader (`engine/weapon_loader.py`)
- [x] `WeaponCatalog` reads BSData merged JSON — single source of truth
- [x] Variant grouping (same stat sig → one profile)
- [x] Most-common default values per weapon
- [x] Unit-context-aware filtering (e.g. "Nemesis force weapon" per unit may differ)

### GK Three-Vector Ranking (`engine/gk_ranking.py`)
- [x] GK-only ranking with per-unit optimal loadout enumeration
- [x] Percentile bars (DPS/SURV/MOB each 0–100%)
- [x] Target-aware optimisation (`--target/-t` flag)
- [x] Mission-weighted sorting (`--mission/-m` flag)
- [x] Cross-target DPP matrix (`--matrix` flag)
- [x] Meta profile weighted optimization (`--meta` flag)
- [x] MFM v1.0 points via `pricing` field (first-unit cost tier)

### Knowledge Base
- [x] `resources/guardrails.md` — 11e rules reference (faction-agnostic)
- [x] `resources/experts/grey-knights.md` — GK domain expert
- [x] `AGENTS.md` — project-level system prompt

### Git
- [x] Initial commits (9da874c → 86bc33f)
- [x] Remote GitHub repo configured
- [x] PR workflow established

---

## Phase 1: Multi-Faction Architecture

### 1a. Faction Configs → JSON Data Files
Move all GK-specific hardcoded configs from Python to JSON:

- [ ] `data/config/` directory with `<faction>/` subdirectories
- [ ] `squads.json` — squad configs (unit name, model count, default weapons, special limits, NFW→CCW rules)
- [ ] `characters.json` — character loadouts (fixed weapons per character)
- [ ] `vehicles.json` — vehicle loadouts (fixed weapon sets per vehicle)
- [ ] `supported.json` — supported unit names list (`known` set)
- [ ] `weapon_options.json` — character weapon swap options (Librarian Vortex of Doom)
- [ ] `detachment_modifiers.json` — detachment-level DPP/MOB buffs

### 1b. Generic Ranking Engine (`engine/ranking.py`)
- [ ] `FactionRanking` class that loads faction config JSON
- [ ] `SquadConfig`, `VehicleConfig`, `CharacterConfig` data models
- [ ] Plugin-based squad variant enumeration (per-faction rules)
- [ ] Multi-faction CLI: `python engine/ranking.py grey-knights --target MEQ`
- [ ] Retire `engine/gk_ranking.py` once GK works through generic engine
- [ ] Detachment-aware ranking: apply detachment buffs to DPP/MOB

### 1c. Test Suite
- [ ] `tests/` dir with pytest structure
- [ ] `tests/test_dpp.py` — DPP computation invariants
- [ ] `tests/test_weapon_loader.py` — catalog loading + weapon lookup
- [ ] `tests/test_surv.py` — survival computation edge cases
- [ ] `tests/test_mob.py` — mobility computation edge cases
- [ ] `tests/test_ranking_gk.py` — GK ranking integration (snapshot)
- [ ] `tests/conftest.py` — shared fixtures (GK merged JSON, weapon catalog)
- [ ] CI config (GitHub Actions: pytest on push)

---

## Phase 2: Second Faction — Chaos Knights

### 2a. Data Pipeline
- [ ] Run merge for CK: `python3 adapter/merge.py --faction chaos-knights`
- [ ] Verify MFM points for CK units
- [ ] Create `data/config/chaos-knights/` with squad/character/vehicle JSON
- [ ] Write `resources/experts/chaos-knights.md` — CK domain expert

### 2b. Ranking
- [ ] Verify CK units load through generic ranking engine
- [ ] Add CK-specific rules: Daemonic Surge (SURV modifier), Harbingers, Dread abilities
- [ ] Add CK detachment modifiers (Iconoclast, Infernal)
- [ ] Validate ranking output vs known CK meta (War Dog spam, Abominant profiles)

### 2c. CK-Specific Engine Rules
- [ ] Daemonic Surge: no FNP for CK (unlike Daemons)
- [ ] Titanic units: Plunging Fire interaction (TOWERING for CK Titans)
- [ ] Harbinger of Dread: battle-shock-based mechanics
- [ ] Bondsmans: War Dog character upgrades

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

### 3f. Chaos Daemons
- [ ] Daemonic Invulnerable saves (base INV 4+ or 5+)
- [ ] Daemonic FNP (5+ vs mortals, 6+ vs normal)
- [ ] Deep Strike generic for all daemons
- [ ] Shadow of Chaos battle-shock mechanics

### 3g. Remaining Factions
- [ ] Aeldari, Drukhari, Necrons, Orks, T'au, etc.
- [ ] Per-faction data pipeline + expert knowledge files

---

## Phase 4: Advanced Engine

### Detachment Modifier System
- [ ] Warpbane Task Force: re-roll hits vs re-roll 1s in Hallowed Ground
- [ ] Argent Assault: +1 to wound vs higher-T targets
- [ ] Banishers: Leadership test → Sustained Hits or Lethal Hits on melee
- [ ] Brotherhood Strike: Deep Strike turn buffs (re-roll 1s to hit/wound)
- [ ] Hallowed Conclave: Terminator Fall Back + shoot/charge
- [ ] Sanctic Spearhead: Vehicle Advance 6"+ Assault
- [ ] Augurium Task Force: Gate of Infinity extension
- [ ] Fires of Purgation: Purgation battle-shock pinning
- [ ] Immaterial Interdiction: Interceptor surge move

### Core Rules Refinements
- [ ] No T1 Reinforcements (11e rule — affects DS mobility value)
- [ ] Rapid Fire keyword processing (remove pre-doubled `ranged_a` hack)
- [ ] Blast keyword processing (min attacks based on squad size)
- [ ] Melta half-range bonus
- [ ] Heavy penalty on movement
- [ ] Plunging Fire for TOWERING

### Output & Visualization
- [ ] Radar/triangle charts (DPS/SURV/MOB axes)
- [ ] Unit comparison tool (side-by-side two units)
- [ ] "What If" mode: add detachment buff, see DPP delta
- [ ] Army builder: given 2000pts + detachment, suggest units

---

## Phase 5: MCP Server & Operations

### MCP Tools
- [ ] `rank_units` — ranking output per faction/target/mission
- [ ] `evaluate_loadout` — custom loadout DPP
- [ ] `compare_units` — side-by-side comparison
- [ ] `army_suggest` — army building suggestion
- [ ] `cross_faction` — compare units across factions

### CI/Operations
- [ ] GitHub Actions: pytest on push
- [ ] GitHub Actions: merge + auto-rank generation
- [ ] Snapshot regression tests
- [ ] MCP server auto-deploy

---

## Known Issues

| Issue | Status |
|-------|--------|
| Purifying Flame lacks Torrent in BSData | Monitoring — 11e FP may differ |
| Heavy Psycannon: BSData shows only Psychic, not Sustained Hits 1 | Monitoring |
| NDK Greathammer WS=3+ while other NDK melee WS=2+ | Likely data artifact |
| Engine uses pre-doubled Storm Bolter A=4 | Tech debt — needs Rapid Fire rule |
| Python hardcoded squad configs → JSON | Phase 1a |
| No test suite → regressions possible | Phase 1c (this sprint) |
| GK Faction Pack PDF has multi-column issues | Fixed via PyMuPDF re-extract |
| All 4 FP detachments now have clean rules text | ✅ |
| 5 codex detachments added (Wahapedia + MFM) | ✅ |

## Key Design Decisions

1. **Data-driven weapon loader** — single source from BSData JSON
2. **No composite score** — three vectors shown separately
3. **Mission weighting is post-hoc** — percentiles per target, then weighted by mission
4. **First-unit MFM cost** — ranking uses lowest pricing tier (1st copy)
5. **Gate of Infinity strategic mobility** — GoI units get base 75 + modifiers
6. **Faction configs in JSON** — Python is the engine, data is the knowledge
7. **Shredder gate** — every data output self-verified before delivery
8. **No backtick fences inside JS template literals** — use 4-space indent
