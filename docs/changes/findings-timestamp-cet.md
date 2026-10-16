# Findings generation stamps: CET instead of UTC

**Ticket:** N/A — follow-up to the T1/T5 findings merge + Pages deploy
**Date:** 2026-10-16

## What changed

The "generated …" stamp on every faction page and on
`findings/index.html` now reports **Central European time** (CEST/CET) instead of
UTC.

- `scripts/gen_findings_html.py` — `GEN_TS` now uses
  `datetime.now(ZoneInfo('Europe/Bratislava')).strftime('%Y-%m-%d %H:%M %Z')`.
  `%Z` yields the correct label automatically (CEST in summer, CET in winter),
  and ZoneInfo keeps the offset right regardless of where the generator runs
  (CI is UTC).
- `_TS_RE` (used by `_mask_ts` for drift comparison) hardened from a literal
  `UTC` suffix to any `[A-Z]{2,5}` zone token, so a stamp difference in any zone
  is still masked and never misread as content drift.

## Why

The stamp was UTC (`time.gmtime()`), which does not match the wall clock of the
people reading or regenerating the site. Reported in local time, "generated"
reads as what it means.

## Note — the one-time forced regeneration

The generator writes a page **only when its masked content changes** (the stamp
is masked before comparison, by design, so pages keep a stable stamp). A
stamp-format change alone therefore rewrites nothing. To apply the new format
the pages had to be regenerated from scratch:

```
rm findings/*/findings.html findings/index.html
python3 scripts/gen_findings_html.py --all
python3 scripts/gen_findings_html.py --index
```

That is why the commit touches all 30 faction pages + the index with a
stamp-only change. After this commit the stamps are stable again — future runs
skip the write, exactly as before.

## Verification

- `git diff` on the findings pages is stamp-only (no non-stamp diff lines).
- `_mask_ts(work) == _mask_ts(HEAD)` for the pages → classified timestamp-only,
  not content drift.
- `python3 -m pytest -q` — 4620 passed, 68 skipped.
- `python3 scripts/check_artifacts_current.py` — OK after the commit (it flags
  the uncommitted stamp-only diff as stale with RC=1, by policy).
