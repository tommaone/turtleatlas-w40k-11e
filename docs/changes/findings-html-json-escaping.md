# Escaping the findings-HTML JSON sink and innerHTML writes

**Date:** 2026-10-16
**Author:** Turtleman (siege/maintenance)
**Ticket:** Follow-up #1 from `docs/changes/escaping-and-artifact-guard.md`
**PR:** TBD (direct-to-main per the operator on the prior ticket)

## What changed

`findings/*/findings.html` (and the landing page `findings/index.html`) embed
data into a `<script>` element and then write it to `innerHTML` at render time.
Both sinks, previously unescaped:

### 1. The `<script>` JSON sink (`_js_safe`)

The `DATA` / `EXPERT` / `WEIGHTS` / `FACTORS` literals were `json.dumps(...)`
output dropped straight into the page. `json.dumps` does **not** escape `<`, so
an expert note or unit name containing `</script>` closed the element early and
injected markup — the exact class of bug the guide fix closed for
`resources/experts/`, from the same source files.

`_js_safe(json_text)` escapes `<` → `\u003c` and the U+2028/U+2029 line
separators (which break a JS string literal). The browser parses the escapes
back to the original characters, so the value the page sees is unchanged.

### 2. The faction name in `<title>` / `<h1>`

`fname` was interpolated raw. It is now passed through
`html.escape(fname, quote=False)`.

### 3. The `innerHTML` sink (`esc` / `escObj`)

The render functions concatenate unit names, weapon names, expert prose and
mission keys into `innerHTML`. A new `esc()` escapes `& < > "` (`'` left alone,
as the code uses single-quoted JS strings), and `escObj()` walks each data object
once at load and escapes every string value in place — `DATA`, `EXPERT`,
`FACTORS`. Mission names are object **keys**, which `escObj` does not touch, so
the three render sites that show a mission key (`renderMissions`,
`renderTop10` badges, `renderInsights` heading) call `esc(mission)` explicitly.

### 4. Pre-existing bug exposed and fixed: the `html` module was shadowed

`gen_findings_html.py` does `import ... html ...` at the top, but the
`if __name__ == '__main__':` block assigns `html = gen_html(...)`. That block is
module scope (an `if` statement does not create a scope in Python), so the name
`html` was rebound to a **string** — and the second faction in the loop crashed
on `html.escape`. The variable is renamed to `page`. This was latent until §2
introduced the first ever use of the `html` module inside `gen_html`.

### 5. The landing page (`index.html`) had the same two sinks

`render_tier_section` embeds the tier list as a `<script>` literal
(`var TIERS={...}`) built from `json.dumps`, and the payload carries `h_army` —
the faction's army-rule text, expert-derived — so it had the identical
`</script>` breakout as the faction pages. It now goes through `_js_safe`.

The page's own `esc` (used on the tier-card tooltip) escaped only `&` and `<`,
but the tooltip is written into a `title="..."` attribute, so a `"` in the
army-rule label broke the attribute. It now escapes `& < > "` like the faction
page's `esc`.

### Key/value invariant (do not collapse)

`escObj` escapes object **values**, not keys. Mission names are keys, so the
three render sites that print a mission name call `esc(mission)` explicitly. Any
future render site that prints a data key rather than a value must do the same —
"run `escObj` on everything" does not cover keys.

## Why

Same root as the guide fix: `resources/experts/` prose is untrusted text, and it
reaches this second rendering path unchanged. A `<` in an expert note is a data
value, not markup, and must survive as one.

## Verification

- Regenerated all 30 factions + `index.html`. **Only `leagues-of-votann` changed a
  JSON literal line**: its expert text contains a literal `<7 YPs`, now
  `\u003c7 YPs`. Every other JSON literal is byte-identical, and `index.html`
  changed only in the `esc` function line (no `h_army` value contains `<`). So no
  page renders differently for the current corpus, and the embedded JSON text
  changes only where a `<`/U+2028/U+2029 actually occurs (votann's expert note).
- `node` parses the escaped votann `EXPERT` literal and yields the original
  `...<7 YPs...`, and `node --check` passes on the regenerated faction script and
  the index script.
- 8 new tests in `tests/test_findings_html_escaping.py`: `_js_safe` unit;
  `</script>` breakout in `DATA` escaping to `\u003c` and round-tripping through
  `json.loads`; the same for `EXPERT` prose; a breakout in a mission **key** plus
  an array-of-strings value; `fname` escaping in `<title>`/`<h1>`; the landing
  page's TIERS payload escaping `h_army`; the landing-page `esc` covering `>` and
  `"`; and a structural guard that `esc`/`escObj` are shipped and applied.
  Red-testable: with `_js_safe` swapped for identity the breakout count assertion
  (`</script>` appears once) fails.
- Full suite **4612 passed / 68 skipped / 0 failed**; MCP smoke **16/16**;
  `node --check mcp-server/index.js` OK.

## Impact for BAs / POs

- A `<`, U+2028 or `</script>` in an expert file or unit name can no longer break
  or inject into a findings page (faction pages or the landing page), and a `"`
  in an army-rule label can no longer break the tier-card tooltip.
- No score, ranking or DPP value changed; the page a reader sees is identical for
  the current data.

## Known follow-ups (named, not fixed here)

1. **Unit-name search uses the escaped form.** `renderRow` writes
   `data-name="'+u.name.toLowerCase()+'"` and `filterMission` matches against it;
   after `escObj`, a unit name containing `& < > "` is indexed in its entity form
   (`&` → `&amp;`), so searching for the raw character would miss. No current
   unit name contains those characters (they come from BSData), so this is
   theoretical today — flagged so a future name with `&`/`<` is not a surprise.
2. `escObj` does not escape object **keys** (see the invariant above); a future
   render site printing a data key must call `esc()` explicitly.
3. Follow-up #2 from the prior change doc stands: `engine/dpp.py`
   `merge_weapon_modifiers` / `merge_detachment_modifiers` are production-dead.
