# Reference — Tools, Commands, Data Sources (turtleatlas-w40k-11e)

## Repo map

| Path | What |
|------|------|
| `adapter/` | BSData/MFM parsers — `bsdata_parser_11e.py`, `merge.py` |
| `engine/` | DPP engine — `dpp.py`, `ranking.py`, `weapon_loader.py` |
| `data/merged/<faction>.json` | Merged BSData stats/weapons (source of truth for profiles) |
| `data/config/<faction>/` | Derived configs — `squads.json`, `characters.json`, `vehicles.json`, `weapon_options.json`, `supported.json` |
| `scripts/` | Generators + validators (see Commands) |
| `tests/` | Pytest suite — 3594 passing, 36 skipped, 1 xfailed (2026-08-15) |
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
python3 -m pytest                                            # full suite (3594 passed / 36 skipped / 1 xfailed — seed for truth-report stability: PYTHONHASHSEED=1)
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

## Current state (2026-08-15)

- **Head of main:** `3370194` — caps sweep on the 9 alloc-layer factions
  (aeldari/BT/BA/DA/DW/GK/orks/SM/SW): 7 FLAT_CAPS entries, generator
  `max=None` FLAT_CAPS rescue fix, 8 stale tests corrected to datasheet
  truth. Full seeded suite: **3594 passed / 36 skipped / 1 xfailed**.
- 30 factions ranked, 1403 datasheets, HTML findings for all.
- **Complex-layer squad configs (alloc pools / per-model slots) — 11
  factions**: aeldari, black-templars, blood-angels, chaos-space-marines,
  dark-angels, deathwatch, emperors-children, grey-knights, orks,
  space-marines, space-wolves. Chaos Daemons book-scoped (17 squads, mostly
  fixed-wargear so no alloc needed). Characters slots schema: ALL 30
  factions (2026-08-11).
- **Knights (IK/CK)** are NOT squad composition — live in
  `characters.json` with `weapon_options.builds`. Questoris (Crusader/
  Errant/Paladin/Warden/Preceptor: 3 slots), Gallant/Destrier (2), Desecrator
  (1), Despoiler (2 slots, 13 builds) done 2026-08-13. Remaining for the
  slot-completion audit: Castellan/Valiant (2 builds each, 0 slots),
  Tyrant (4, 0), all Cerastus (0), Canis Rex / Defender / Rampager /
  Ruinator / Abominant / Magaera / Styrix re-audit.
- **World Eaters**: 10 squads, all flat builds — not yet migrated.
- **Validator state**: 0 CRITICAL/MAJOR across shipped factions; MEDIUM/LOW
  noise envelope per faction (BT 129, BA 128, DA 133, SW 136, SM 129,
  DW 119, aeldari 7, GK 3, Orks 75) — pre-existing MISSING/EXTRA classes,
  compare against HEAD not zero.
- **Detachment modifiers**: 26 (GK 9 + CK 8 + Daemons 9); SM/DA + all
  others BLOCKED until every army is on the slot setup.
- **Truth-report isolation rule**: regen with configs applied vs stashed
  (same `PYTHONHASHSEED=1`); commit = committed report + ONLY the migrated
  factions' blocks. Report is NOT byte-reproducible under any seed from a
  fresh checkout (environment drift) — the diff-vs-HEAD method is the gate.
- Report regen command: `PYTHONHASHSEED=1 python3 -m pytest
  tests/test_truth_roles_report.py` (runs the session fixture that writes
  the file; a bare `python3 -m` is a silent NO-OP — no `__main__` block).

## Next moves (as of 2026-08-15)

1. Squad composition migration to remaining factions — complex layer done:
   Aeldari + GK + Space Marines + Dark Angels + Blood Angels + Space Wolves +
   Black Templars + Deathwatch (Wave 1) + CSM/EC/Orks (Wave 2) + alloc caps
   sweep on the 9 alloc-layer factions (2026-08-15, commit `3370194`).
   **Wave 3 (2026-08-15, USER DECISION — changed from AM/AdMech): Chaos
   Knights + Imperial Knights slot-completion audit first (knights live in
   characters.json weapon_options.builds, NOT squads; 2026-08-13 pass slotted
   Questoris + Despoiler — this wave completes Cerastus/Castellan/Valiant/
   Tyrant/Armiger-class builds), then World Eaters generator migration (10
   squads, light tier).** Commit + push the IK/CK batch BEFORE starting WE
   (explicit user request). **This is the gate.**
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
