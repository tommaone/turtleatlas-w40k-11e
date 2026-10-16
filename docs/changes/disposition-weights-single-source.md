# Disposition weights: single source of truth

**Date:** 2026-10-16
**Author:** Turtleman (siege/maintenance)
**Ticket:** P1 — disposition weights duplicated; findings-HTML copy wrong for Take and Hold
**PR:** TBD

## What changed

Disposition ("mission") weights were defined twice. The engine scored with one
copy; the findings HTML displayed another — and for **Take and Hold** the display
copy was wrong.

- **Engine truth** — `data/config/_base.json` `mission_profiles`, merged into
  every faction config via `_extends`, loaded at `engine/ranking.py:98`
  (`self.mission_profiles`) and used to score at `engine/ranking.py:2035`.
  Take and Hold there = dps 0.15 / surv 0.35 / obj 0.40 / mob 0.10.
- **Wrong display copy** — `scripts/gen_findings_html.py` `WEIGHTS` (hardcoded
  literal) and the `MISSION_FACTORS` prose percentages. Take and Hold there =
  20/30/35/15.

`scripts/gen_findings_html.py`:

1. `build_data` now derives `mission_weights` from the per-faction effective
   engine config (`e.config.mission_profiles`) at generation time, converting
   floats ×100 to integer percents, and returns it alongside `(DATA, n_units)`.
   Only the 5 keys in `MISSIONS` are emitted — `_base.json`'s extra
   `"Purge (general)"` key is excluded.
2. The hardcoded numeric `WEIGHTS` literal is deleted. Each page embeds its own
   derived weights as `const WEIGHTS=...` (per-faction pages, intended).
3. `MISSION_FACTORS` prose percentages are now `{dps}`/`{surv}`/`{obj}`/`{mob}`
   placeholders, filled from the same derived dict by `_mission_factors_for()`
   — the qualitative text is unchanged, the numbers cannot drift.
4. The per-unit contribution columns (`dpp_c`/`surv_c`/`obj_c`/`mob_c`, computed
   in `build_data`) use the derived weights.

Test cleanup (`tests/test_tanky_archetypes.py`): removed the inline `WEIGHTS`
dict (a 4th copy) and the `_compute_score()` re-implementation of the engine
formula; the tests now assert on the engine's `unit["_mission_score"]` directly.
Call sites of the changed `build_data` return signature updated:
`tests/test_findings_validation.py` and `scripts/p0_snapshot.py`.

## Why

Duplicated truth drifts. The display copy disagreed with the engine on the
mission the report most cares about (objective-holding), so the mission-card
header and every per-unit OBJ/SURV contribution column were showing weights the
engine never used. Making the engine config the only numeric definition removes
the class of bug, not just this instance.

## Verification

- `python3 scripts/gen_findings_html.py --all` then `--index`.
- `findings/grey-knights/findings.html` now embeds Take and Hold as
  `{"dps": 15, "surv": 35, "obj": 40, "mob": 10}` and the FACTORS prose reads
  OBJ 40% / SURV 35% / DPP 15% / MOB 10%.
- `python3 -m pytest -q` — 4612 passed, 68 skipped.
- `python3 scripts/check_artifacts_current.py` — clean after committing the
  regenerated findings output.
- `grep` confirms the only numeric mission-weight definition in shipped
  code/spec is `data/config/_base.json`.

## Impact

- Generated findings HTML only: each faction page's embedded `WEIGHTS`/`FACTORS`
  and the per-unit contribution columns change for Take and Hold (and, for any
  faction that overrides `mission_profiles`, for those missions too). Engine
  scores/rankings are unchanged — the engine was already correct.
- No changes to engine behaviour, config, or the MCP sidecar `data.json`
  (which carries scores, not weights).
