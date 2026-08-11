# Reference — Tools, Commands, Data Sources (turtleatlas-w40k-11e)

## Repo map

| Path | What |
|------|------|
| `adapter/` | BSData/MFM parsers — `bsdata_parser_11e.py`, `merge.py` |
| `engine/` | DPP engine — `dpp.py`, `ranking.py`, `weapon_loader.py` |
| `data/merged/<faction>.json` | Merged BSData stats/weapons (source of truth for profiles) |
| `data/config/<faction>/` | Derived configs — `squads.json`, `characters.json`, `vehicles.json`, `weapon_options.json`, `supported.json` |
| `scripts/` | Generators + validators (see Commands) |
| `tests/` | Pytest suite — 3350 passing, 36 skipped (2026-08-10) |
| `findings/<faction>/findings.html` | Per-faction ranking pages |
| `findings/index.html` | Landing page — GENERATED, never hand-edited |
| `mfm/` | Munitorum Field Manual data (points source of truth) |
| `bsdata/` | Raw BSData 11e JSON |
| `mcp-server/` | MCP server (points to turtleatlas-mcp) |
| `resources/` | Guardrails, expert files |
| `docs/` | Roadmap (`docs/roadmap.md` is the single roadmap; root `ROADMAP.md` deleted 2026-08-05) |
| `memory/` | This layer — learned rules + reference |
| `workspace/` | Scratch — gitignored, never commit |

## Commands

```bash
python3 -m pytest                                            # full suite (3350 passed / 36 skipped)
python3 scripts/gen_findings_html.py --faction aeldari       # regen one faction page
python3 scripts/gen_findings_html.py --index                 # regen landing page counts
python3 scripts/gen_findings_html.py --all                   # regen all factions + index
python3 scripts/gen_squad_composition.py                     # regen squad composition configs (Aeldari pilot)
python3 scripts/validate_configs_vs_bsdata.py                # config ↔ catalog validation
python3 scripts/validate_squad_configs.py                    # squad config validation
python3 -m adversarial.deterministic_check --faction <faction>   # deterministic data checks
python3 -m pytest tests/test_findings_validation.py          # findings integrity
```

Pipeline order after config work: generator → validators → full pytest → regenerate findings + index → commit → ask before push.

## Data sources

| Source | Role |
|--------|------|
| BSData 11e JSON (`bsdata/`) | Primary — profiles, keywords, composition |
| MFM (`mfm/`) | Points source of truth |
| Wahapedia | Cross-check only, never primary |

## MCP server

```bash
./start-mcp.sh
# or
node mcp-server/index.js --port 3456
```

MCP Bootstrap Protocol: `list_experts` + `get_expert(<faction>)` + `get_sql_rules` before answering domain questions. `turtleatlas-mcp` is the knowledge server.

## Current state (2026-08-09)

- 30 factions ranked, 1403 datasheets, HTML findings for all
- Reroll-vs-MONSTER/VEHICLE engine live: `engine/reroll_detect.py` auto-detects
  reroll abilities from merged ability text (24 datasheets across 15 factions),
  `engine/dpp.py` applies qualified hit/wound/damage rerolls per toughness-band
  target; GMNDK Surge of Wrath configured (`data/config/grey-knights/weapon_options.json`)
  — NOW GENERALIZED to all class keywords (CHARACTER/INFANTRY/TITANIC/WALKER/
  MOUNTED + M/V = 33 datasheets): weakest-wins upgrades, aura-subject skip,
  roll-noun `\b` boundary fix
- Aeldari squad-composition pilot done: dual-profile weapons (Singing Spear/Chainsabres), parallel-variant alloc (Troupe/Windriders/Storm Guardians), per-model slots, multi-fixed-weapon models, mixed squads (Kabalite 9+Sybarite)
- **space-marines migrated to complex layer (Wave 1 done)**: generator
  bugs fixed en route — case-insensitive exact name match before substring
  (Eradicator With Heavy Bolters must not resolve to melta base entry),
  deterministic alloc-name tie-break (hash-order safe); Victrix config weapon
  swap fixed (power-sword in ranged slot)
- **dark-angels migrated to complex layer (Wave 1 done)**: no-Legends rule
  ([Legends] composition entries never match — Deathwing Command Squad kept,
  not rewritten), 2 stale config squads removed (Deathwing Command Squad
  [Legends-only], Ravenwing Talonmaster [no catalogue], 35→33), 32 squads
  migrated via --force; 6 complex-unit tests added
- **blood-angels migrated to complex layer (Wave 1 done)**: 33 squads
  migrated via --force, 0 skipped, 1 kept (Invader ATV — no top-level
  composition entry, curated builds preserved); 13 complex-unit tests added;
  validator +1 issue is the documented Outrider EXTRA-WEAPON false positive;
  findings unit set stable 97→97, top all-comers Take and Hold unit flipped
  Terminator Assault Squad → Tactical Squad (alloc lets Tactical take a
  special + heavy simultaneously)
- **space-wolves migrated to complex layer (Wave 1 done, merged after BA)**:
  36 squads via gen_squad_composition --force; 7 complex-unit tests added;
  SW plasma quirk FIXED (2026-08-10): choice profiles (standard/supercharge,
  frag/krak, strike/sweep) score as max-over-group via WeaponProfile.variants,
  so plasma resolves identically across SW/SM/DA/BA (supercharge-scored) and
  the displayed base is deterministically 'standard'. Long Fangs / Wolf Guard
  absent from SW merged BSData (not even [Legends]) — documented, not asserted.
- **black-templars migrated to complex layer (Wave 1 done, 2026-08-10)**:
  30 squads via --force, 0 skipped, 1 kept (Invader ATV — curated); Chaplain
  Grimaldus moved squads.json → characters.json (character, n=1, converted to
  weapon_options.builds schema; two old plasma builds collapse to one bare
  'Plasma Pistol'); 5 complex-unit/character tests added
- **deathwatch migrated to complex layer (Wave 1 done, 2026-08-10)**:
  29 squads via --force, 0 skipped, 2 kept (Invader ATV + Decimus Kill Team),
  Decimus then curated (was kept with a broken config — plasma swap backwards,
  ranged weapon in the melee slot; datasheet default Plasma pistol + Power
  weapon) → 30 changed entries total; generator leader fix (min==1 AND max==1
  = leader; base model with min=1/max>1 stays in pool — Deathwatch Terminator
  was resolving 2/5 models); validated behavior-neutral for shipped factions;
  7 complex-unit tests added
- 3350 tests passing, 36 skipped
- Detachment modifiers: 26 (GK 9 + CK 8 + Daemons 9); SM/DA + 20+ factions not yet modeled
- Head of main: merged SW + BA Wave-1 migrations. Dojo flow: main branch only, ask before push.
- Report regen is hash-seeded: `PYTHONHASHSEED=1 python3 -m pytest tests/test_truth_roles_report.py` (NOT `python3 -m tests.test_truth_roles_report` — that module has no `__main__` block and silently does nothing). NOTE: as of 2026-08-10 the committed report is NOT byte-reproducible under any seed (environment drift; best seed-2 has 2-line residual). For a migration, commit = committed report + ONLY the migrated factions' blocks (seed-stable across seeds 1/2/42) — see feedback.md "Truth-report regeneration is NOT byte-reproducible".

## Next moves (as of 2026-08-10)

1. Squad composition migration to remaining factions — complex layer done:
   Aeldari + GK + Space Marines + Dark Angels + Blood Angels + Space Wolves +
   Black Templars + Deathwatch (**Wave 1 complete 2026-08-10**); next per
   docs/checklist-squad-composition-migration.md: Wave 2 (Astra Militarum,
   Adeptus Mechanicus). **This is the gate.**
2. ~~Engine gap: multi-profile weapons (Cyclone Missile Launcher frag+krak under
   one name — loader resolves only first profile)~~ **DONE 2026-08-10** — choice
   profiles now score as max-over-group (WeaponProfile.variants); plasma
   standard/supercharge, frag/krak, strike/sweep, Starshot/Sunburst all
   correct; SM Terminator/Devastator + SW/SM/DA/BA slot pins updated
3. Detachment modifiers for SM, DA, all others — **BLOCKED (2026-08-10 decision):
   not until every army is on the slot setup.** A detachment bonus over an
   imaginary loadout is a lie; calculations must be determined by real gear first.
4. Engine gaps: T3 primary metric, concentrated fire, pistol/two-handed restriction, transport support

## Credentials

None. Public repo — mechanics and commands only. Credential loading goes through `$ENV_VAR` references, never hardcoded values.
