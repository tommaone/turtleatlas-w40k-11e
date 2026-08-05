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

## Current state (2026-08-05)

- 28 factions ranked, ~1500 units, HTML findings for all
- Aeldari squad-composition pilot done: dual-profile weapons (Singing Spear/Chainsabres), parallel-variant alloc (Troupe/Windriders/Storm Guardians), per-model slots, multi-fixed-weapon models, mixed squads (Kabalite 9+Sybarite)
- 2898 tests passing, 36 skipped
- Detachment modifiers: 26 (GK 9 + CK 8 + Daemons 9); SM/DA + 20+ factions not yet modeled
- Head of main: `6e4558e` (docs roadmap). Dojo flow: main branch only, ask before push.

## Next moves (as of 2026-08-05)

1. Squad composition migration to remaining factions (Aeldari is the pilot)
2. Detachment modifiers for SM, DA, all others
3. Engine gaps: army rules modeling, T3 primary metric, concentrated fire, pistol/two-handed restriction, transport support

## Credentials

None. Public repo — mechanics and commands only. Credential loading goes through `$ENV_VAR` references, never hardcoded values.
