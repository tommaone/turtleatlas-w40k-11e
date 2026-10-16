# Disposition design files — parked, not wired

**Date:** 2026-10-16
**Author:** Leonardo (planning agent)
**Ticket:** N/A — dead-artefact audit of the 2026-07-05 disposition work
**PR:** TBD

## What changed

Nothing in the running system behaves differently. Three unfinished-feature
artefacts from the July 2026 disposition work were confirmed to be read by
nothing, and they now carry a clear warning header so nobody mistakes them for
live data:

- `data/dispositions.json` — a `_note` field was added at the top of the file.
- `data/config/chaos-knights/disposition_ranking.md` — a warning banner was
  added above the title.
- `docs/change-doc-disposition-engine.md` — the design doc was corrected so it
  no longer reads as if the whole system is live; it now separates what is
  WIRED from what is PARKED.

No file was deleted. No code was changed. This is a reversible "label it"
action.

## Why

The disposition work was designed in one pass but only partly built. The design
doc described a complete system, and one parking-lot file (`dispositions.json`)
holds a **third, divergent weight model** — a set of DPS/SURV/MOB weights that
contradicts both the engine's real weights and the findings-page display. Left
unlabelled, that file is a trap: the next person to open it would reasonably
  believe it is the source of truth and build on data that the pipeline never
  reads.

## Verification (nothing reads these)

Confirmed by grep on 2026-10-16:

- `grep -rn 'dispositions\.json' engine mcp-server scripts adapter tests` — **no
  matches**. The file is referenced only from prose docs/resources
  (`docs/change-doc-disposition-engine.md`, `resources/disposition-system.md`,
  `resources/guardrails.md`, `resources/meta-bias.md`), never loaded at runtime.
- `compute_disposition_ranking` appears only at its definition
  (`engine/ranking.py:2157`) — **no callers** in engine, MCP server, scripts or
  tests.

## Impact for BAs / POs

**Nothing breaks, nothing shifts, no user-facing behaviour changes.** What you
need to know:

- **What is LIVE** (part of the product today): each detachment's disposition is
  stored in the `supported.json` `dispositions` map, and a validation guard
  (`can_detachment_play_disposition`) uses it to prevent an army combining a
  detachment with a disposition it cannot legally play.
- **What is PARKED** (not part of the product): the `dispositions.json`
  definitions, its DP budgets, mission-alignment table and meta-bias; the
  Chaos Knights markdown tier list; and the `compute_disposition_ranking()`
  engine function. None of these are read by any tool, script or test.
- **The trap:** `dispositions.json` contains a set of mission weights that
  disagree with the two weight tables the product actually uses. If any future
  feature reads this file without noticing, it will produce numbers that
  contradict the rest of the product. The warning header now prevents that.

No screens, flows or integrations are affected. No data was migrated or
recalculated.

## Recommendation (per artefact)

| Artefact | Recommendation | Rationale |
|----------|----------------|-----------|
| `data/dispositions.json` | **Delete** (pending BA/PO sign-off) | Read by nothing; its third weight model is a false-truth hazard, not an asset. Build any future DP-budget feature on `supported.json` + MFM instead. |
| `data/config/chaos-knights/disposition_ranking.md` | **Delete** (pending BA/PO sign-off) | Hand-written expert tier list wired to nothing; a dated snapshot that will silently rot. Keep the reasoning as an expert note if still wanted. |
| `compute_disposition_ranking()` (`engine/ranking.py`) | **Wire or delete** | Currently dead code. Either expose it as a tool if per-disposition detachment ranking is wanted, or remove it. Do not leave it parked. |

Deletion is deliberately NOT part of this change — this is park + document only,
so it can be reversed by reverting a single commit.

## Out of scope

- No deletion of any file or function.
- No change to the live `supported.json` `dispositions` map, the validation
  guard, the MCP server, or the engine's functional behaviour.
- No change to the engine mission profiles (`data/config/_base.json`) or the
  findings-page display weights (`scripts/gen_findings_html.py`).
- No resolution of the design-doc's proposal for a future non-DPP value engine.
