# OBJ percentile: cap `wounds_per_model` in the value to match the series

**Branch:** `fix/obj-wpm-cap-mission-branch`
**Ticket:** T5 (criticality P2) — "confirm & fix engine wpm cap inconsistency"

## What changed

`engine/ranking.py`, `RankingEngine.compute_ranking`, mission branch — the
per-unit OBJ value now caps `wounds_per_model` at 3, matching the OBJ percentile
*series* built a few lines above and the documented OBJ formula.

Before:

```python
# series (obj_vals), line ~2054
wpm = min(r["surv"].get("wounds_per_model", 1), 3)   # capped
...
# per-unit value, line ~2086
wpm = r["surv"].get("wounds_per_model", 1)           # NOT capped  <-- bug
```

After: the value uses `min(..., 3)` too.

The comment above the series already states the intended formula —
`(OC + banner_boost) × models × min(wpm, 3) × survival_turns`, *"Capped at 3 —
prevents high-W vehicles (W10+) from dominating OBJ"* — so the uncapped value
was the defect, not the cap.

## Why

`_obj_pct = _pct(value, series)` is only meaningful when `value` is computed on
the same scale as the entries in `series`. With the value uncapped, a W10+
unit was scored on its raw wound count while the distribution it was ranked
against capped every entry at 3. The result was a percentile that could exceed
100 — impossible for a percentile — e.g. **102** for GK vehicles and **103** for
Chaos Knights before the fix.

## Verification

- New guard: `tests/test_obj_percentile_consistency.py` asserts `_obj_pct ∈
  [0, 100]` for every unit, every mission, for grey-knights / chaos-knights /
  space-marines (fails before the fix — hence a red-testable regression guard,
  not just a snapshot).
- `python3 -m pytest -q` — all green.
- `python3 scripts/check_artifacts_current.py` — no content drift after
  regenerating `findings/` + `index.html`.

## Impact (scoring change — read before merging)

This is not a cosmetic fix: it corrects the OBJ component's percentile for
every unit with `wounds_per_model > 3`, which reorders mission rankings.

| Faction | units with obj/score change | rank order changed |
|---------|-----------------------------|--------------------|
| Grey Knights | 15 / 26 | yes |
| Space Marines | 62 / 85 | yes |
| Chaos Knights | 20 / 20 | yes |

Direction: high-W models no longer get an inflated OBJ percentile, so they drop
in OBJ-heavy missions (Take and Hold, Priority Assets). Low-W infantry are
unaffected (`min(wpm, 3) == wpm` for wpm ≤ 3).

## Known follow-up (NOT fixed here — separate ticket)

The **no-mission branch** has the same class of inconsistency, in the other
direction: its OBJ series caps `wpm` at 3 (`ranking.py:~2128`) but its per-unit
value omits `wpm` entirely (`ranking.py:~2148`). It does not produce
percentiles > 100 (the value is always ≤ the capped series), but the value and
series are still computed on different scales. Out of scope for this ticket —
worth its own.
