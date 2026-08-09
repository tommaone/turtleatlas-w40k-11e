# Reference — Tools, Commands, Data Sources (turtleatlas-w40k-11e)

## Repo map

| Path | What |
|------|------|
| `adapter/` | BSData/MFM parsers — `bsdata_parser_11e.py`, `merge.py` |
| `engine/` | DPP engine — `dpp.py`, `ranking.py`, `weapon_loader.py` |
| `data/merged/<faction>.json` | Merged BSData stats/weapons (source of truth for profiles) |
| `data/config/<faction>/` | Derived configs — `squads.json`, `characters.json`, `vehicles.json`, `weapon_options.json`, `supported.json` |
| `scripts/` | Generators + validators (see Commands) |
| `tests/` | Pytest suite — 2898 passing, 36 skipped (2026-08-05) |
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
python3 -m pytest                                            # full suite (2898 passed / 36 skipped)
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

## Current state (2026-08-08)

- 30 factions ranked, ~1500 units, HTML findings for all
- Reroll-vs-MONSTER/VEHICLE engine live: `engine/reroll_detect.py` auto-detects
  reroll abilities from merged ability text (24 datasheets across 15 factions),
  `engine/dpp.py` applies qualified hit/wound/damage rerolls per toughness-band
  target; GMNDK Surge of Wrath configured (`data/config/grey-knights/weapon_options.json`)
  — NOW GENERALIZED to all class keywords (CHARACTER/INFANTRY/TITANIC/WALKER/
  MOUNTED + M/V = 33 datasheets): weakest-wins upgrades, aura-subject skip,
  roll-noun `\b` boundary fix
- Aeldari squad-composition pilot done: dual-profile weapons (Singing Spear/Chainsabres), parallel-variant alloc (Troupe/Windriders/Storm Guardians), per-model slots, multi-fixed-weapon models, mixed squads (Kabalite 9+Sybarite)
- **space-marines migrated to complex layer (Wave 1 pilot done)**: generator
  bugs fixed en route — case-insensitive exact name match before substring
  (Eradicator With Heavy Bolters must not resolve to melta base entry),
  deterministic alloc-name tie-break (hash-order safe); Victrix config weapon
  swap fixed (power-sword in ranged slot)
- 3314 tests passing, 36 skipped
- Detachment modifiers: 26 (GK 9 + CK 8 + Daemons 9); SM/DA + 20+ factions not yet modeled
- Head of main: `1a2c541`. Dojo flow: main branch only, ask before push.
- Report regen is hash-seeded: `PYTHONHASHSEED=1 python3 -m pytest tests/test_truth_roles_report.py` (NOT `python3 -m tests.test_truth_roles_report` — that module has no `__main__` block and silently does nothing)

## Next moves (as of 2026-08-08)

1. Squad composition migration to remaining factions (Aeldari + Space Marines done —
   Wave 1 next: Dark Angels → Blood Angels → Space Wolves; then Waves 2-4 per
   docs/checklist-squad-composition-migration.md)
2. Engine gap: multi-profile weapons (Cyclone Missile Launcher frag+krak under
   one name — loader resolves only first profile, so missile slots under-rate
   vs AP-and-D6 options; affects slot picks + DPP truth on Terminator/Devastator
   heavy slots, not just SM)
3. Detachment modifiers for SM, DA, all others
4. Engine gaps: T3 primary metric, concentrated fire, pistol/two-handed restriction, transport support

## Credentials

None. Public repo — mechanics and commands only. Credential loading goes through `$ENV_VAR` references, never hardcoded values.
