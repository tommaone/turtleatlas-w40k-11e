# Pipeline hygiene: stale notes, duplicated tier logic, stale docstring

**Date:** 2026-10-16
**Author:** Raphael
**Ticket:** Pipeline hygiene (T2/T3/T6)
**PR:** branch `chore/pipeline-hygiene` (not pushed)

## What changed

Three stale claims in the merged-data pipeline, each verified false at HEAD
before it was rewritten. No pipeline behaviour changed.

### T2 — the false "`--all` is the only correct regeneration path" note

`memory/reference.md` claimed a single `--faction` regeneration "drops
abilities on cross-faction fallback units (space-marines: 17 units)" and that
`--all` was therefore the only correct path. False since commit `5725a9c`:
`main()` builds the global cross-faction unit index for both selectors, so

    python3 adapter/merge.py --faction space-marines --output /tmp/x

is byte-identical to the committed `data/merged/space-marines.json`. Verified
on this worktree; the 17 fallback units keep their abilities (0 with an empty
ability list). The note now says both paths are correct.

New guard `tests/test_merge_single_faction_reproducible.py` runs the real CLI
into `tmp_path` and asserts byte-identity with the committed artifact for
space-marines — the one faction with cross-faction fallback units, so the one
where a lost/order-shifted global index shows up in the output. It runs the
CLI rather than calling `merge_faction()` in-process on purpose: the function
takes no `global_index`, which is exactly the state the old note described. A
second, cheap test pins that committed fallback units carry abilities.

### T3 — duplicated tier logic in `merge.py`

`merge_faction()` re-implemented the plain-over-groupTitle tier rule that
`adapter/mfm_pricing.iter_base_entries` owns. The inline loop is now a call to
`iter_base_entries` (imported at the top of `adapter/merge.py`). Two
differences the inline copy carried had to be preserved to stay
byte-identical:

- legends are filtered before tier selection (the docstring lists no legend
  handling);
- the input list is **reversed** — `iter_base_entries` keeps the last entry of
  an exact name duplicate, while this map has always kept the first.
  space-wolves lists "Venerable Dreadnought" twice (130/140 tiers and a flat
  165); the committed artifact carries the first entry. Without the reverse,
  `--all` shifts that unit by 35pts.

The norm-keyed plain-over-group guard remains: `iter_base_entries` keys on the
original MFM name, `mfm_unit_map` keys on `norm_name`.

**Stale number corrected** ("99 -> 15"): `mfm/data/blood-angels.yaml` holds 121
entries, 38 of them legends; 83 non-legend entries merge, of which 69 are
group-only. Dropping the group-only fallback collapses blood-angels **83 → 14**
units (measured by running `merge_faction` with the groupTitle entries
filtered out). The adjacent "11 other factions / 459 group-only units" figure
was also stale — it is 11 factions, **390 group-only entries** (128 distinct
names) at these submodule pins. Corrected in `adapter/merge.py` and the
`iter_base_entries` docstring in `adapter/mfm_pricing.py`.

### T6 — `adapter/merge.py` header

"merges 10e BSData profiles" and "bsdata/ -> wh40k-10e" are stale — the
submodule URL is `BSData/wh40k-11e` (`.gitmodules`). Header fixed, and it now
records that both pins are **tagless SHAs** (`git describe --tags` fails in
both submodules): bsdata `cc58ee3`, mfm `8e0e635`. MFM's "v1.5" is a YAML field
(`mfm/data/meta.yaml` `version: "1.5"`), not a git tag. The same stale "10e" in
the `argparse` description was fixed with it.

## Why

Three notes described a pipeline that no longer exists, and one of them
("`--all` is the only correct path") costs a 5-minute regeneration when a
1-2 minute one produces identical bytes. The duplicated tier rule is the drift
`adapter/mfm_pricing.py`'s docstring explicitly warns about; it now has one
owner.

## Verification

- `python3 adapter/merge.py --all` — **no change to `data/merged/*`** (`git
  status` clean for that tree), i.e. the `iter_base_entries` swap is
  behaviour-neutral across all 30 factions.
- `python3 -m pytest -q` — **4614 passed, 68 skipped** (baseline 4612 + the 2
  new tests).
- `python3 scripts/check_artifacts_current.py` — no **content** drift; the only
  entries it flags are 3 timestamp-only files
  (`docs/army-choice-guide.md`, `findings/advisor.json`,
  `findings/army-choice-guide.html`) that carry `date.today()` and were
  committed 2026-10-15. Reverted, not committed. Pre-existing at HEAD: none of
  this change touches an input of `scripts/army_advisor.py`.

## Out of scope / named, not fixed

1. Two test docstrings carried the same false claims as T2/T3
   (`tests/test_no_dead_ability_prose.py` — "17 units, `--all` is the only
   correct path"; `tests/test_merge_mfm_pricing_tiers.py` — "99 -> 15"). Both
   were corrected in this change because they sit next to the new guard;
   the surrounding text (the partial reproducibility guarantee) is unchanged.
2. `memory/feedback.md:1518` still records the old "99 -> 15" figure. It is a
   dated lesson log, left as written.
3. The space-wolves duplicate "Venerable Dreadnought" (130/140 vs 165) is an
   upstream MFM data question: `data/config` and the SW golden test carry 165,
   merged data carries 130. Byte-identity was the constraint here, so the merge
   behaviour is unchanged. **Not yet ticketed** — it is the one live
   config-vs-merged points split found.
4. `scripts/sync_config_pts.py` and `tests/test_config_points_match_mfm.py`
   still carry their **own copies** of the tier rule (T3 only centralised
   `merge.py`). `adapter/mfm_pricing.py` now says so explicitly instead of
   listing them as consumers.
5. `adapter/bsdata_parser.py:4` still says "Parses 10e .cat files" and
   `tests/test_merge_mfm_pricing_tiers.py` still wires it to `bsdata/data/`,
   which does not exist at these pins (submodule is flat `*.json`). Harmless
   today (the parser returns `None`), outside T6's `merge.py` header scope.

## Impact for BAs / POs

- Nothing user-visible changed: no points, ability, DPP or ranking value moved
  — `data/merged/` is byte-identical.
- "Regenerate the data with one faction" is now a documented, tested path
  (~2 minutes instead of ~5), which shortens any single-faction data question.
- One conflicting number is now visible instead of hidden: space-wolves'
  Venerable Dreadnought is 165pts in the curated config and 130/140 in the
  merged MFM data. Both were already true; the follow-up (item 3, unticketed)
  decides which is right.
