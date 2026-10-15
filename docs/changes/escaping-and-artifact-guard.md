# Escaping, artifact-guard completeness, and a behaviour-neutral engine cleanup

**Date:** 2026-10-15
**Author:** Turtleman (siege/maintenance)
**Ticket:** N/A — Shredder review follow-ups on the advisor-caveat changeset
**PR:** TBD

## What changed

Three independent hardening items, all following the advisor-caveat commit
that fixed stale detachment claims in the MCP surface.

### 1. HTML escaping in the army-choice guide (`scripts/army_advisor.py`)

The guide page interpolated expert-file text (faction `fit_why`) and faction
names into HTML with no escaping. `render_guide_html(lines)` is now a pure,
testable function that HTML-escapes every field (`& < >`, quotes left literal)
before wrapping it in a tag, then promotes `**bold**` to `<strong>`.

The visible fix is one line: `resources/experts/<faction>.md` was emitted as a
literal invalid `<faction>` tag; it is now `&lt;faction&gt;`.

### 2. Markdown table-cell escaping in the MCP server (`mcp-server/index.js`)

A `#mdCell(v)` helper escapes `|` (to `\|`) and collapses newlines, applied to
every data-derived text cell across the ranking, comparison, army-index and
faction-tier tables. A pipe or newline in a unit or faction name previously
broke the whole table for the agent reading it.

### 3. Untracked-artifact detection in the artifact guard (`scripts/check_artifacts_current.py`)

`git diff HEAD` cannot see untracked files, so a newly-created artifact (a new
faction's `data.json`, a new findings report) slipped past the guard entirely.
`_stale_paths()` now unions `git diff HEAD` with `git ls-files --others
--exclude-standard`, deduped; untracked paths are reported as real content
drift.

### 4. Behaviour-neutral engine cleanup (`engine/ranking.py`)

Detachment modifiers were retired 2026-08-27, so `_load_detachment_modifiers()`
always returns `{}` and `detachment_pairs` in `compute_ranking()` was always
empty. The always-empty machinery was removed: the pair-building loops, the
nested `_modifier_applies()` helper, and the per-unit merge block. The two
surviving `if unit_surv_mod:` / `if unit_mob_mod:` branches were also dead (the
variables can only be `None`), so they are gone; `unit_weapon_mod` stays an
explicit `None` passed to the DPP calls as an optional argument.

**Kept deliberately:** the public retired-API stubs (`get_detachment_modifiers`,
`list_detachments_with_modifiers`, `_load_detachment_modifiers`), the
`detachment` / `detachment_choice` / `detachments` parameters, and the
disposition-validation guard (a detachment that cannot play the chosen
disposition still raises `ValueError`).

### 5. `engine/gk_ranking.py` CLI help told the truth about nothing

`--detachment` said "Detachment name to apply modifiers from" and
`--detachment-choice` said "Index of modifier choice"; modifiers are retired.
Both strings now say what the flags actually do (validate against the
disposition; accepted for compatibility), and the dead `choices=` argument was
dropped.

## Why

Escape the untrusted input at every sink it reaches; close the guard gap that
let artifacts drift silently; remove dead machinery that made a false claim
(the "rules-aware adjustment") look plausible. The engine cleanup removes the
plumbing that implied detachment scoring was live.

## Verification

- `engine/ranking.py`: `compute_ranking` output for grey-knights (base, single
  detachment + disposition, multi-detachment, and two invalid pairs) captured
  before the edit; **byte-identical** after, including the `ValueError`
  messages. The artifact guard regenerated **all 30 factions** and every one
  was "unchanged" — independent confirmation the cleanup is behaviour-neutral
  end-to-end.
- Full suite **4604 passed / 68 skipped / 0 failed**; MCP smoke **16/16**.
- Guide HTML diff vs HEAD is exactly one line (the `<faction>` escaping).
- `test_guide_html_escapes_interpolated_text` is red-testable: with `_esc`
  replaced by identity, `<script>` leaks and the blockquote assert fails.
- `test_stale_paths_flags_untracked_artifacts` is red-testable: `git diff`
  alone lists only the modified file, never the untracked one. It also asserts
  `classify()` routes the untracked file to **content drift** (the
  `git show HEAD:<path>` failure branch), not a timestamp bump.

## Known follow-ups (named, not fixed here)

1. **`scripts/gen_findings_html.py` has the same untrusted sink, unescaped.**
   `const EXPERT={expert_json}` (line ~879) embeds expert text inside a
   `<script>` block via `json.dumps`, which does not escape `<`, so an expert
   file containing `</script>` breaks out; line ~908 concatenates
   `EXPERT.play_pattern` / `army_rule` / `r.why` straight into `innerHTML`. Same
   `resources/experts/` source as the guide this change escaped. **Needs its own
   ticket** — it is a wider change (a safe JSON-embedding helper plus an
   escaping pass over the insights renderer).
2. **`engine/dpp.py` `merge_weapon_modifiers` / `merge_detachment_modifiers`
   are now production-dead** (only `tests/test_engine_gaps.py` still call
   them); this change removed their last production caller. Candidate for
   removal in the same ticket as item 1 or a separate cleanup.
3. **`compute_ranking(detachments=[("x", None)])`** previously raised
   `TypeError` on the malformed index; it is now silently ignored. Unreachable
   from any in-repo caller.
4. **Retired-API stubs remain** — `get_detachment_modifiers` /
   `list_detachments_with_modifiers` are documented compatibility shims with a
   CLI caller (`engine/gk_ranking.py`) and a test asserting they return `[]`.
   Removing them is a separate ticket with the CLI, test and docs.

## Impact for BAs / POs

- The army-choice guide page can no longer be broken (accidentally or
  otherwise) by a stray `<` or `&` in an expert file.
- MCP table output an agent reads is now structurally intact even if a name
  contains a pipe.
- The artifact guard now catches a class of drift it was blind to
  (newly-created files), so "the check is green" means more than it did.
- No score, ranking or DPP value changed. Nothing user-visible in the numbers.
