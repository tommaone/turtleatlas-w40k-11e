# resources/ — Knowledge Files

Human-readable reference files for 11e rules, DPP pitfalls, and faction domain knowledge.

## Structure

```
resources/
├── guardrails.md           # 11e rules reference & DPP pitfalls — load before DPP
├── non-dpp-value.md        # OC/screening/SURV framework — non-damage analysis
├── disposition-system.md   # Disposition/mission type analysis
├── meta-bias.md            # Meta bias analysis (internal notes)
├── change-doc-disposition-engine.md  # Disposition engine change doc
└── experts/                # Faction domain knowledge
    ├── grey-knights.md
    ├── chaos-knights.md
    └── chaos-daemons.md
```

## How to Use

1. Always load `guardrails.md` before doing any DPP computation — it contains critical 11e rules that affect damage calculations.
2. Load the relevant faction expert from `experts/` for squad limits, gotchas, and optimal loadouts.
3. Use `non-dpp-value.md` for non-damage analysis (objectives, screening, durability).

## Adding a New Expert

1. Create `experts/<faction>.md` following the existing pattern (disposition ranking, detachment breakdown, top combos, gotchas)
2. Update `data/config/<faction>/detachment_modifiers.json` with verified modifiers
3. Run DPP engine to verify numeric outputs
4. Add per-expert test in the MCP server (turtleatlas-mcp/tests/expert/)

## Adding a New Faction

1. Add BSData profile JSON to `data/merged/` (run `adapter/merge.py --faction <name>`)
2. Create `data/config/<faction>/detachment_modifiers.json`
3. Create `resources/experts/<faction>.md`
4. Verify all detachment rules from 40k.app
5. Run DPP engine
6. Add disposition ranking
