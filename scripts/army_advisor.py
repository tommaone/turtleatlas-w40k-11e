#!/usr/bin/env python3
"""Army buy-advisor: long-term trend metrics from engine outputs.

Modular by design: emits findings/advisor.json (machine-readable, MCP /
conversational ready) and can render docs/army-choice-guide.md (--guide).

Metrics per faction (all derived from engine outputs, never re-computed):
- overall_index      mean rank-decay score across the 5 dispositions
- floor / ceiling    worst / best disposition score
- versatility        100 - (ceiling-floor) spread; high = plays every mission
- roster_depth       ranked datasheet count
- points_churn       MFM changelog mentions since edition start (GW attention)

Buy-signal heuristics are LLM-synthesis tier (🔴 STRATEGY): they combine
engine facts with assumptions listed in the output. The `meta_ceiling`
field stays null until detachment-aware scoring ships (war plan P3).

Usage:
    python3 scripts/army_advisor.py            # writes findings/advisor.json
    python3 scripts/army_advisor.py --guide    # also renders the markdown guide
"""
import argparse
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TIERS = REPO / "findings" / "army_tiers.json"
CHANGELOG = REPO / "mfm" / "DATA-CHANGELOG.md"
ADVISOR_OUT = REPO / "findings" / "advisor.json"
GUIDE_OUT = REPO / "docs" / "army-choice-guide.md"

CAVEATS = [
    "meta_ceiling is engine-computed only for factions with VERIFIED "
    "detachment data (grey-knights, chaos-knights, chaos-daemons, "
    "dark-angels, space-marines); null = generalist index is the ceiling "
    "proxy (auto-generated MFM stubs are not detachment rules)",
    "statline quality persists across balance patches; rules packages do not",
    "points churn counts changelog mentions since edition start - a proxy "
    "for GW attention, not a prediction; Astartes flavours share one codex "
    "so their churn is partially double-counted",
    "win-rate correlation is partial: community results include rules "
    "packaging this index deliberately excludes",
]


def points_churn() -> dict[str, int]:
    """Count changelog bullet mentions per faction display name."""
    text = CHANGELOG.read_text()
    # Faction names appear as '**Aeldari**:' bullets
    counts: dict[str, int] = {}
    for m in re.finditer(r"\*\*([A-Z][^*]+?)\*\*", text):
        name = m.group(1).strip()
        counts[name] = counts.get(name, 0) + 1
    return counts


def build():
    tiers = json.loads(TIERS.read_text())
    churn = points_churn()
    factions = []
    for fid, t in tiers.items():
        ms = t["missions"]
        vals = list(ms.values())
        ceiling, floor = max(vals), min(vals)
        # meta_ceiling (war plan P3): detachment-aware overall when the
        # faction carries verified detachment modifiers — engine-computed,
        # never hand-authored. None = generalist only.
        det = t.get("det") or {}
        factions.append({
            "fid": fid,
            "name": t["name"],
            "overall_index": t["overall"],
            "ceiling": ceiling,
            "floor": round(floor, 1),
            "versatility": round(100 - (ceiling - floor), 1),
            "roster_depth": t["n_units"],
            "best_disposition": max(ms, key=ms.get),
            "worst_disposition": min(ms, key=ms.get),
            "points_churn": churn.get(t["name"], 0),
            "meta_ceiling": det.get("overall"),
            "meta_ceiling_best_detachment": (det.get("best") or {}).get(
                max(ms, key=ms.get)),
            "_classification": "engine_output+heuristic",
            "_caveats": CAVEATS,
        })
    factions.sort(key=lambda x: -x["overall_index"])
    out = {
        "_formula": {
            "overall_index": "rank-decay weighted mean (lambda=0.95) of unit "
                             "mission scores across Take and Hold, Purge the Foe, "
                             "Reconnaissance, Priority Assets, Disruption",
            "unit_score": "engine _mission_score (quad-vector percentile composite)",
            "not_modeled": CAVEATS,
        },
        "generated": "2026-08-23",
        "factions": factions,
    }
    ADVISOR_OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"wrote {ADVISOR_OUT} ({len(factions)} factions)")
    return out


SIGNALS_DOC = """\
## Signal definitions (heuristic layer — 🔴 STRATEGY, not engine fact)

- **Foundation pick** — top-third overall AND top-half versatility.
  Statlines carry the army through any mission and most balance passes.
  Best long-term hold.
- **Specialist weapon** — top-third ceiling but bottom-half versatility.
  Buys a tournament edge in one disposition; risky as an only army.
- **Active tuning** — top-quartile points churn. GW is actively moving
  this faction's costs; expect swings both ways. Buy cheap-ish now only
  if you accept repricing.
- **Value window** — mid index or better but bottom-tier community win
  rate recently: underlying quality the meta hasn't re-priced. Highest
  upside, needs patience.
"""


def guide(data):
    f = data["factions"]
    n = len(f)
    third = max(n // 3, 1)
    half = max(n // 2, 1)
    quart = max(n // 4, 1)

    foundations = [x for x in f[:third]
                   if x["versatility"] >= sorted(y["versatility"] for y in f)[half]]
    low_vers = sorted(y["versatility"] for y in f)[quart]  # bottom quartile
    specialists = [x for x in f
                   if x["ceiling"] >= f[0]["ceiling"] - 3
                   and x["versatility"] <= low_vers][:6]
    tuning = sorted(f, key=lambda x: -x["points_churn"])[:quart]
    value = [x for x in f[third:2 * third]
             if x["versatility"] >= sorted(y["versatility"] for y in f)[half]]

    lines = [
        "# Choosing Your Army — practical help so you don't waste money",
        "",
        "*Generated 2026-08-23 from engine outputs (rank-decay roster index, "
        "MFM v1.2). Full method + caveats in findings/advisor.json.*",
        "",
        SIGNALS_DOC,
        "## Foundation picks (buy with confidence)",
        "",
    ]
    lines += [f"- **{x['name']}** — overall {x['overall_index']}, versatility "
              f"{x['versatility']} (best {x['best_disposition']})" for x in foundations]
    lines += ["", "## Specialist weapons (buy for a plan)", ""]
    lines += [f"- **{x['name']}** — ceiling {x['ceiling']} in {x['best_disposition']}"
              for x in specialists]
    lines += ["", "## Active GW tuning (expect repricing)", ""]
    lines += [f"- **{x['name']}** — {x['points_churn']} MFM changelog entries"
              for x in tuning]
    lines += ["", "## Value windows (underpriced quality)", ""]
    lines += [f"- **{x['name']}** — overall {x['overall_index']}, versatile "
              f"{x['versatility']}" for x in value]
    lines += [
        "",
        "## Honest limitations",
        "",
    ] + [f"- {c}" for c in CAVEATS]
    GUIDE_OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {GUIDE_OUT}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--guide", action="store_true")
    args = ap.parse_args()
    d = build()
    if args.guide:
        guide(d)
