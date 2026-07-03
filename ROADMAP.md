# Project Roadmap — turtleatlas-w40k-11e

Three-vector (DPS/SURV/MOB) 40k unit ranking engine with MCP server.

---

## ✅ Done

### Data pipeline
- [x] BSData XML parser (`adapter/bsdata_parser.py`)
- [x] BSData + MFM point merge (`adapter/merge.py`)
- [x] Core Rules PDF parser (`adapter/core_rules_parser.py`)
- [x] Faction Pack PDF parser (`adapter/faction_pack_parser.py`)
- [x] GK merged JSON output (92 units, 26 with MFM points)

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
- [x] Variant grouping (same stat sig → one profile, e.g. SB has 1 variant via default count)
- [x] Most-common default values per weapon
- [x] Unit-context-aware filtering (e.g. "Nemesis force weapon" per unit may differ)

### Three-Vector Ranking (`engine/gk_ranking.py`)
- [x] GK-only ranking with per-unit optimal loadout enumeration
- [x] Percentile bars (DPS/SURV/MOB each 0–100%)
- [x] Target-aware optimisation (`--target/-t` flag: GEQ/MEQ/TEQ/Light V/Heavy V/C'tan/Knight)
- [x] Mission-weighted sorting (`--mission/-m` flag: Purge the Foe, Take and Hold, Reconnaissance, etc.)
- [x] Cross-target DPP matrix output (`--matrix` flag)
- [x] Loadout resolution: squads optimised per target, vehicles/characters fixed
- [x] Data-driven weapon profiles from BSData (all factory functions deleted)
- [x] Squad configs in structured dicts (special max, NFW→CCW rules, innate weapons)

### Knowledge Base
- [x] `resources/guardrails.md` — 11e rules reference & DPP pitfalls (faction-agnostic)
- [x] `resources/experts/grey-knights.md` — GK domain expert (squad limits, 9 detachments, weapon gotchas)
- [x] `AGENTS.md` — project-level system prompt for AI agents

### Git
- [x] Initial commit `9da874c` — working state with data-driven weapon loader, 28 files

---

## 🔄 Done This Session (commit #2)

- [x] Refactor `compute_ranking()` to accept `target` and `mission` parameters
- [x] Add `--target` / `--mission` CLI flags to `main()`
- [x] Print cross-target DPP matrix via `--matrix`
- [x] Mission-weighted percentile ranking (DPS/SURV/MOB weighted per mission profile)
- [x] `ROADMAP.md` — project feature tracking file
- [x] `gate_of_infinity` parameter in `compute_mob` — GK army rule modeled
- [x] MOB score overhaul: GoI units get strategic mobility base 75 + M/FLY/OC modifiers; non-GoI units use physical mobility
- [x] Min-max normalized display bars (0% = worst in faction, 100% = best) — no more misleading percentile
- [x] Fixed `get_unit_info` for STATIC_LOADOUTS: only Dreadnoughts/NDKs get WALKER+DEEP STRIKE keywords
- [x] Fixed non-GoI MOB tier to include `skyborne` mapping

---

## 📋 Planned (no order)

### Engine
- [ ] Detachment modifier system — apply detachment buffs to DPP (Warpbane rerolls, Argent Assault, etc.) and MOB (Force Wave through walls, Celerity Advance+Charge, etc.)
- [ ] No T1 Reinforcements rule — 11e rule: no Deep Strike/Reserves arrive turn 1. Affects DS mobility value.
- [ ] Add Rapid Fire keyword processing (remove pre-doubled `ranged_a` hack)
- [ ] Add Blast keyword processing (min attacks based on squad size)
- [ ] Add Melta half-range bonus
- [ ] Squad re-optimisation per mission (not just per target)
- [ ] FNP support for target profiles
- [ ] Variance/confidence bands (not just average dice)
- [ ] Plunging Fire handling for TOWERING units

### Ranking
- [ ] Refactor squad configs from Python dicts into JSON data file
- [ ] Generalise `gk_ranking.py` → `ranking.py` for multi-faction support
- [ ] Radar/triangle chart visualisation (DPS/SURV/MOB as 3 axes)
- [ ] Web UI or CLI dashboard with interactive filtering

### Testing
- [ ] Write tests for `engine/dpp.py` (DPP + SURV + MOB)
- [ ] Write tests for `engine/weapon_loader.py`
- [ ] Write tests for `engine/gk_ranking.py`
- [ ] Snapshot tests for ranking output (catch regressions)

### Data
- [ ] Re-parse GK Faction Pack PDF with better column-detection (11e weapon profiles may differ from BSData)
- [ ] Add more factions (start with Imperial Agents, then one more)
- [ ] Validate all weapon profiles against 11e rules (not 10e BSData)
- [ ] Add terrain data for cover calculations

### MCP Server (`mcp-server/index.js`)
- [ ] Add faction filtering to `get_unit` tool
- [ ] Add `rank_units` tool returning the ranking output
- [ ] Add `evaluate_loadout` tool for custom loadout DPP
- [ ] Add cross-target comparison tool

### Operations
- [ ] CI pipeline (run tests on push)
- [ ] Automated merge + ranking generation
- [ ] Auto-deploy MCP server

---

## Known Issues

| Issue | Status |
|-------|--------|
| Purifying Flame lacks Torrent in BSData (10e? 11e? unclear) | Monitoring — 11e Faction Pack may differ |
| Heavy Psycannon: BSData shows only Psychic, not Sustained Hits 1 | Monitoring — Faction Pack may update |
| Heavy Incinerator A=7.0 vs 10e A=5.5 in BSData | Accepted — data-driven |
| NDK Greathammer shows WS=3+ while other NDK melee WS=2+ | Likely data artifact |
| Engine uses pre-doubled Storm Bolter A=4 (no Rapid Fire keyword) | Tech debt — needs Rapid Fire rule |
| Squad stats hardcoded in Python dicts (T, SV, W, OC) | Should be JSON data file |

## Key Design Decisions

1. **Data-driven weapon loader** over factory functions — one source of truth from BSData merged JSON
2. **Purifying Flame without Torrent** — BSData shows only Anti-Infantry 2+, Ignores Cover, Psychic; respecting data
3. **Psycannon without Sustained Hits 1** — BSData shows only Psychic; changes ranking vs 10e
4. **Loadouts re-optimised per target** — `best_squad_variant(name, target)` recomputes optimal combo each time
5. **Mission weighting is post-hoc** — DPS/SURV/MOB percentiles computed per target, then weighted by mission; no re-optimisation for mission
6. **No composite score** — three vectors shown separately; agent/reader interprets all three
7. **No backtick fences inside JS template literals** — use 4-space indent to avoid SyntaxError
