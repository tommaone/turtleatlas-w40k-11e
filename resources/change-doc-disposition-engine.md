# Disposition System & Non-DPP Value Framework

**Date:** 2026-07-05
**Author:** Leonardo (planning agent)
**Ticket:** N/A — foundation work
**PR:** TBD

## What changed

The system now understands **five detachment Dispositions** (Purge the Foe, Take and Hold, Reconnaissance, Priority Assets, Disruption) as first-class entities. Each detachment in every faction pack is tagged with its Disposition. A new `data/dispositions.json` provides the machine-readable rules for how Dispositions relate to mission types, how DP budgets work at each game size, and how Strike Force armies combine 2–3 detachments within a 3DP budget.

A companion **Non-DPP Value framework** (`resources/non-dpp-value.md`) documents all the things a unit does besides damage — Objective Control, screening, actions, transport, reserves, durability — giving LLM agents a structured way to evaluate non-damage utility without computing numbers they shouldn't compute.

The existing guardrails document is expanded to cover what it was missing: enhancement effects, detachment buffs (systemic), the Disposition system, OC/scoring, screening, and actions. Pitfall examples are generalised away from being Grey Knights–only.

## Why

Before this change, the system had three gaps that limited its usefulness for army construction advice:

1. **Dispositions were invisible.** The `meta-bias.md` file correctly called out that only two missions are competitively viable, but there was no structured way to reason about which detachment is good for which mission. A detachment's Disposition (what it's designed to do) existed only as implicit knowledge in the faction pack docs.

2. **Non-damage value had no framework.** The DPP engine intentionally doesn't model OC, screening, actions, or mobility utility — but nothing told LLM agents what *does* handle those things. Agents either ignored them (producing one-dimensional "DPP is king" advice) or made up numbers.

3. **Guardrails were too narrow and incomplete.** Section 6 ("What DPP does NOT Model") was missing key systemic gaps, and all pitfall examples were Grey Knights–specific, making the doc less useful for other factions.

This work **does not** build a non-DPP value engine — it creates the vocabulary, data structures, and guardrails so that engine can be built later without conflicting with existing systems.

## Impact for BAs / POs

### Files created (4)

| File | Purpose |
|------|---------|
| `resources/disposition-system.md` | Human-readable: 5 Dispositions explained, DP budget tables, Strike Force construction rules, mission alignment guidance |
| `resources/non-dpp-value.md` | Human-readable: framework for OC, screening, actions, transport, reserves, durability — what each is, how to evaluate it verbally, what NOT to compute |
| `data/dispositions.json` | Machine-readable: Disposition definitions (name, ID, mission_weights, keywords), DP budget per game size, Strike Force rules, mission alignment table |
| `resources/change-doc-disposition-engine.md` | This document |

### Files modified (3)

| File | What changes |
|------|-------------|
| `resources/guardrails.md` | Section 6 expanded (enhancements, detachment buffs systemic, disposition, OC/scoring, screening, actions). Section 8 pitfalls generalised — no longer GK-only examples. Cross-reference to new docs added. |
| `data/config/*/supported.json` | New `dispositions` key added — maps each detachment (kebab-cased) to its disposition ID. Backed by the authoritative `disposition` field on the faction pack JSON. |
| `resources/meta-bias.md` | Cross-reference to disposition-system.md. Notes that Purge the Foe and Take and Hold align to specific Dispositions. |

### Data changes to faction pack JSONs (3 files affected)

| File | What changes |
|------|-------------|
| `data/grey-knights-faction-pack.json` | Each detachment entry gains `"disposition": "<disposition-id>"` |
| `data/chaos-knights-faction-pack.json` | Same |
| `data/chaos-daemons-faction-pack.json` | Same |

Each detachment's `disposition` field matches one of: `purge-the-foe`, `take-and-hold`, `reconnaissance`, `priority-assets`, `disruption`.

### What this unblocks

1. **Non-DPP value engine (future):** Once the framework doc is accepted, an engine can be built that scores OC efficiency, screening area, action monkey capability, and transport value — without conflicting with DPP.
2. **Detachment-aware ranking:** The ranking engine (`ranking.py`) already supports a `detachment` parameter. With Disposition metadata, it can auto-select the right mission weighting for a detachment.
3. **Strike Force construction tool (future):** With DP budget rules in machine-readable form, an agent can validate that a 3-detachment Strike Force fits within 3DP budget and spans appropriate Dispositions.
4. **Faction-agnostic guardrails:** The generalised pitfall section will serve all factions equally, reducing future maintenance.

### Edge cases

- **Detachments with no explicit Disposition in faction pack JSON:** Faction packs published before this change will not have the `disposition` field. The system treats missing `disposition` as "unclassified" — ranking works as before, but Disposition-aware features skip that detachment.
- **Same Disposition on multiple detachments in one faction:** Expected and valid. A faction may have 3x Purge the Foe detachments at different DP costs. No constraint on uniqueness.
- **DP budget at game sizes below Strike Force:** `data/dispositions.json` defines budgets for Incursion (1–2DP, 1–2 detachments) and Onslaught (3–5DP, 3–4 detachments) in addition to Strike Force.
- **Mission profiles in `supported.json` vs Dispositions:** These are different concepts. Mission profiles are DPS/SURV/MOB weight vectors used by the ranking engine. Dispositions are broader design intents. A `purge-the-foe` Detachment aligns with the `Purge the Foe` mission profile — the names match but the data structures serve different purposes.

## Out of scope

- **Non-DPP value engine implementation:** This work creates the framework doc and data structures but does NOT implement any engine code that computes OC efficiency, screening, or action scores. That is explicitly future work.
- **Modifying the DPP engine (`engine/dpp.py`):** No changes to damage calculations. The DPP engine stays exactly as it is.
- **Modifying the MCP server (`mcp-server/index.js`):** No changes to tool handlers, tool schemas, or the server itself. The MCP server continues to load faction pack JSONs as before — the new `disposition` field is simply ignored by existing code until a new tool or feature reads it.
- **Modifying the ranking engine (`engine/ranking.py`):** No functional changes. The ranking engine already supports detachment-aware ranking. The new data fields enrich what's available but don't change existing behaviour.
- **Adding new MCP tools:** No new tools are added. The Disposition data becomes available to agents through existing tools (e.g., `get_detachment` returns `disposition` as part of the output).
- **Retroactive disposition assignment:** We assign dispositions for the three existing factions (GK, CK, CD). Older faction packs are not retroactively modified.
- **Meta-bias revision:** The claim that only 2 mission types are viable is not changed or challenged. The new docs simply make the system aware of all 5 Dispositions so the bias is explicit, not implicit.

---

## Shredder Review Checklist (pre-delivery)

| Check | Status |
|-------|--------|
| 1. No "best" without context | ✅ All Dispositions include context (mission type, DP budget, game size) |
| 2. No implicit role from keyword alone | ✅ `disposition` field is explicit, not inferred from detachment name |
| 3. No epistemic collapse | ✅ Human-readable docs and machine-readable data preserve constraint context |
| 4. No ability chaining certainty | ✅ Disposition system framed as design intent, not guaranteed performance |
| 5. Assumption registry present | ✅ `non-dpp-value.md` includes explicit "what this framework does NOT model" |
| 6. Rule paraphrased as authoritative | ✅ All rules quoted or cited, not paraphrased as system fact |
| 7. No re-computation by LLM | ✅ The framework doc instructs LLMs what NOT to compute — no numerical OC or screening scores are derived |

---

## Data: `dispositions.json` Schema (as implemented)

```json
{
  "version": "11.0",
  "dispositions": [
    {
      "id": "purge-the-foe",
      "name": "Purge the Foe",
      "description": "Kill-focused mission — rewards high DPS, trading efficiency, threat range",
      "live": true,
      "meta_weight": "primary",
      "keywords": ["kill", "dps", "trading", "threat-range"],
      "profile": { "dps": 0.70, "surv": 0.20, "mob": 0.10 }
    },
    {
      "id": "take-and-hold",
      "name": "Take and Hold",
      "description": "Objective-focused mission — rewards durability, OC, mobility for board control",
      "live": true,
      "meta_weight": "secondary",
      "keywords": ["objective", "durable", "oc", "board-control"],
      "profile": { "dps": 0.20, "surv": 0.50, "mob": 0.30 }
    },
    {
      "id": "reconnaissance",
      "name": "Reconnaissance",
      "description": "Mobility and positioning focused mission",
      "live": false,
      "meta_weight": null,
      "keywords": ["mobility", "scoring", "deep-strike", "actions"],
      "profile": { "dps": 0.15, "surv": 0.25, "mob": 0.60 }
    },
    {
      "id": "priority-assets",
      "name": "Priority Assets",
      "description": "Mixed kill/board — rewards flexible units that can fight and hold",
      "live": false,
      "meta_weight": null,
      "keywords": ["flexible", "durable-dps"],
      "profile": { "dps": 0.50, "surv": 0.30, "mob": 0.20 }
    },
    {
      "id": "disruption",
      "name": "Disruption",
      "description": "Debuff/control mission — rewards battleshock, area denial, movement blocking",
      "live": false,
      "meta_weight": null,
      "keywords": ["control", "battleshock", "denial"],
      "profile": { "dps": 0.35, "surv": 0.35, "mob": 0.30 }
    }
  ],
  "dp_budget": {
    "combat_patrol": { "max_dp": 1, "description": "500pts games, 1 detachment" },
    "incursion": { "max_dp": 2, "description": "1000pts games, 1-2 detachments" },
    "strike_force": { "max_dp": 3, "description": "2000pts games, 2-3 detachments" },
    "onslaught": { "max_dp": 4, "description": "3000pts games, 2-4 detachments" }
  },
  "rules": {
    "one_disposition_per_detachment": "Each detachment enables exactly one disposition. A detachment's disposition is defined in its faction pack.",
    "mission_alignment": "Your army must include at least one detachment whose disposition matches your chosen mission. If no detachment matches, your army is unaligned (no mission bonus).",
    "detachment_points": "Detachment Point (DP) costs vary by detachment. Total DP across all detachments cannot exceed the game size's max_dp."
  },
  "mission_alignment": {
    "purge-the-foe": { "viable": true, "note": "Default for competitive ranking" },
    "take-and-hold": { "viable": true, "note": "Objective-focused" },
    "reconnaissance": { "viable": false, "note": "Effectively dead per Mordian Glory consensus" },
    "priority-assets": { "viable": false, "note": "Effectively dead per consensus" },
    "disruption": { "viable": false, "note": "Effectively dead per consensus" }
  },
  "meta_bias": {
    "source": "Mordian Glory (community consensus, July 2026)",
    "default_mission": "purge-the-foe",
    "note": "This bias expires if GW releases a new GT Mission Pack"
  }
}
```

Key differences from the proposal:
- `live` flag + `meta_weight` instead of `gt_viable` + `primary_mission`
- `profile` (dps/surv/mob) instead of `mission_weights`
- `keywords` are descriptive, not aliases
- `dp_budget` includes `combat_patrol` (1DP) and uses `description` strings
- `rules` section replaces `strike_force_rules`
- `mission_alignment` maps disposition IDs to viability + notes
- `meta_bias` section captures the community consensus source
- Version is `11.0` (matching Core Rules version)

## Data: Faction Pack `disposition` field (example for GK)

Each detachment in `data/grey-knights-faction-pack.json` gains:

```json
{
  "name": "ARGENT ASSAULT",
  "dp_cost": 1,
  "disposition": "purge-the-foe",
  "rules": [ /* existing */ ],
  "enhancements": [ /* existing */ ],
  "stratagems": [ /* existing */ ],
  "modifiers": { /* existing */ }
}
```

Full mapping:
| Detachment | `dp_cost` | `disposition` |
|---|---|---|
| Argent Assault | 1 | `purge-the-foe` |
| Fires of Purgation | 1 | `disruption` |
| Immaterial Interdiction | 1 | `priority-assets` |
| Warpbane Task Force | 2 | `purge-the-foe` |
| Augurium Task Force | 2 | `reconnaissance` |
| Banishers | 2 | `disruption` |
| Brotherhood Strike | 2 | `purge-the-foe` |
| Hallowed Conclave | 2 | `take-and-hold` |
| Sanctic Spearhead | 2 | `priority-assets` |

## Data: `supported.json` `dispositions` key (example for GK)

Each `data/config/*/supported.json` gains a top-level `dispositions` map.

The key is kebab-case detachment name; the value is the disposition ID string.
The authoritative source is the `disposition` field on each detachment in the
faction pack JSON. The `supported.json` copy is a convenience for the ranking
engine and MCP tools that don't load the full faction pack.

```json
{
  "dispositions": {
    "argent-assault": "purge-the-foe",
    "fires-of-purgation": "disruption",
    "immaterial-interdiction": "priority-assets",
    "warpbane-task-force": "purge-the-foe",
    "augurium-task-force": "reconnaissance",
    "banishers": "disruption",
    "brotherhood-strike": "purge-the-foe",
    "hallowed-conclave": "take-and-hold",
    "sanctic-spearhead": "priority-assets"
  }
}
```

---

## Implementation order

Priority matters. The dependency chain is:

```
dispositions.json  ─┬─► faction pack JSONs (add disposition field) ──► supported.json (add dispositions map)
                     │                    │
                     └─► disposition-system.md (human doc)
                    
guardrails.md (expand section 6, generalise pitfalls)
    │
    └─► meta-bias.md (cross-reference)
    
non-dpp-value.md (independent — no data dependencies)
```

**Parallelisable:**
- `dispositions.json` + `disposition-system.md` + faction pack modifications can be done in one pass (faction packs depend on disposition IDs being defined)
- `non-dpp-value.md` is fully independent — can be written in parallel
- `guardrails.md` modifications depend on understanding the expanded gap list but don't depend on the disposition JSON structure

**Not parallel:**
- `supported.json` modifications depend on `dispositions.json` AND faction pack modifications
- `meta-bias.md` cross-reference depends on knowing the final file names

## Implementation order (as executed)

| Step | Files | Turtle |
|------|-------|--------|
| 1 | `data/dispositions.json` | Donatello 🟣 |
| 2 | `data/*-faction-pack.json` (add `disposition` field) | Donatello 🟣 (fix after Shredder review) |
| 3 | `data/config/*/supported.json` (add `dispositions` map) | Donatello 🟣 |
| 4 | `resources/disposition-system.md` | Raphael 🔴 |
| 5 | `resources/non-dpp-value.md` | Raphael 🔴 |
| 6 | `resources/guardrails.md` (expand + generalise) | Raphael 🔴 |
| 7 | `resources/meta-bias.md` (cross-reference) | Raphael 🔴 |
| 8 | `resources/change-doc-disposition-engine.md` | Leonardo 🔵 |
| 9 | Shredder review + fix BLOCK issues | Shredder ⚔️ → Donatello 🟣 |
