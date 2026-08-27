#!/usr/bin/env python3
"""Army advisor: which faction to play, from engine-derived facts.

Modular by design: emits findings/advisor.json (machine-readable, MCP /
conversational ready) and can render docs/army-choice-guide.md (--guide).

Metrics per faction (all derived from engine outputs, never re-computed):
- overall_index      mean rank-decay score across the 5 dispositions
- floor / ceiling    worst / best disposition score
- versatility        100 - (ceiling-floor) spread; high = plays every mission
- roster_depth       ranked datasheet count
- points_churn       MFM changelog mentions since edition start (GW attention)

Play-fit heuristics are LLM-synthesis tier (🔴 STRATEGY): they combine
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
import statistics
import glob

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


def durability_map():
    """FACT layer: median wounds + share of multi-wound units per faction.

    Grounds the difficulty wording — fragile/durable is derived from
    statline data, never vibes.
    """
    out = {}
    for f in sorted(glob.glob(str(REPO / "data" / "merged" / "*.json"))):
        fid = f.split("/")[-1][:-5]
        d = json.load(open(f))
        ws = []
        for u in d.get("units", []):
            st = (u.get("profile") or {}).get("stats") or {}
            try:
                ws.append(int(str(st.get("W", "1"))))
            except ValueError:
                ws.append(1)
        if not ws:
            continue
        med = statistics.median(ws)
        multi = sum(1 for w in ws if w >= 5) / len(ws)
        if med >= 5 and multi >= 0.5:
            band = "Durable"
        elif med <= 4 and multi < 0.45:
            band = "Fragile"
        else:
            band = "Mixed"
        out[fid] = {"median_w": med, "multi_wound_pct": round(multi * 100),
                    "band": band}
    return out


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
        # meta_ceiling (semantically retired 2026-08-27): fabrication of a
        # detached-scores ceiling is no longer produced. Detachment strength is
        # a heuristic (expert EXPERT.detachments ratings), not an engine number.
        # meta_ceiling stays null — no fake ceiling.
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
## How to read this (plain words — judgement layer, not engine fact)

The engine measures how strong each faction's models are on paper
(statlines and points). It cannot measure rules packages, skill floor,
or how punishing an army is to play — those are expert calls below,
grounded in the durability facts shown.

- **Strength** — where the faction ranks today on model quality.
  Changes with balance updates; a strong army can get nerfed.
- **Versatility** — does it fight well on every mission type, or only
  one? Versatile armies forgive list-building mistakes.
- **Difficulty** — Durable armies (big wound pools) survive mistakes;
  Fragile armies (few wounds per model) punish every positioning error.
  Fragile + expensive + tricky rules = hard mode. Not a first army.
- **GW attention** — factions whose points changed a lot recently keep
  changing. Playing one means accepting that your points and rules
  will move under you.

"""


def guide(data):
    f = data["factions"]
    n = len(f)
    third = max(n // 3, 1)
    half = max(n // 2, 1)
    quart = max(n // 4, 1)
    dur = durability_map()
    for x in f:
        x["difficulty"] = dur.get(x["fid"], {}).get("band", "Mixed")

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
        "# Choosing Your Army — strength, versatility, difficulty",
        "",
        "*Generated 2026-08-23 from engine outputs (rank-decay roster index, "
        "MFM v1.2). Full method + caveats in findings/advisor.json.*",
        "",
        "> This narrows the field — it tells you where each faction's "
        "strength sits today and what the army demands from you as a "
        "player. It cannot tell you the future meta.",
        "",
        SIGNALS_DOC,
        "## If this is your first army",
        "",
        "> Start **Durable** and **versatile**. Avoid Fragile bands as a "
        "first army: they punish positioning mistakes that experienced "
        "players stop making around year two.",
        "",
    ]
    forgiving = [x for x in f if x["difficulty"] == "Durable"
                 and x["versatility"] >= sorted(y["versatility"] for y in f)[half]]
    lines += [f"- **{x['name']}** — durable models, plays all missions"
              for x in forgiving[:6]] or ["- (none clear the bar this pass)"]
    lines += [
        "",
        "## Strongest long-term signal",
    ]
    lines += [f"- **{x['name']}** — strength {x['overall_index']}, plays all "
              f"missions ({x['difficulty']} models)" for x in foundations]
    lines += ["", "## Specialist picks (strong in one mission)", ""]
    lines += [f"- **{x['name']}** — shines in {x['best_disposition']}"
              f" ({x['difficulty']} models)" for x in specialists]
    lines += ["", "## Active GW tuning (expect repricing)", ""]
    lines += [f"- **{x['name']}** — {x['points_churn']} MFM changelog entries"
              for x in tuning]
    lines += ["", "## Underrated right now", ""]
    lines += [f"- **{x['name']}** — overall {x['overall_index']}, versatile "
              f"{x['versatility']}" for x in value]
    lines += [
        "",
        "## Honest limitations",
        "",
    ] + [f"- {c}" for c in CAVEATS]
    GUIDE_OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {GUIDE_OUT}")

    # findings/army-choice-guide.html — same content, rendered for the
    # landing-page link (a raw .md URL is not user-friendly anywhere).
    import re as _re
    html = ["<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            "<title>Choosing Your Army</title><style>"
            "body{font-family:system-ui,sans-serif;max-width:860px;margin:0 auto;"
            "padding:30px 20px;background:#0d1117;color:#c9d1d9;line-height:1.6}"
            "h1{color:#f0f6fc}h2{color:#58a6ff;border-bottom:1px solid #21262d;"
            "padding-bottom:6px;margin-top:28px}blockquote{border-left:3px solid #bc8cff;"
            "margin:12px 0;padding:6px 14px;color:#d2a8ff;background:#161b22;border-radius:0 6px 6px 0}"
            "li{margin:4px 0}strong{color:#f0f6fc}"
            ".back{font-size:13px;margin-bottom:20px}"
            ".back a{color:#4fc3f7;text-decoration:none}</style></head><body>"]
    html.append('<div class="back"><a href="index.html">&larr; All Factions</a></div>')
    inlist = False
    for ln in lines:
        s = ln.strip()
        if not s:
            if inlist:
                html.append("</ul>")
                inlist = False
            continue
        bold = _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        if bold.startswith("# "):
            html.append(f"<h1>{bold[2:]}</h1>")
        elif bold.startswith("## "):
            if inlist:
                html.append("</ul>")
                inlist = False
            html.append(f"<h2>{_re.sub(r'</?strong>', '', bold[3:])}</h2>")
        elif bold.startswith(">"):
            html.append(f"<blockquote>{bold.lstrip('> ')}</blockquote>")
        elif bold.startswith("- "):
            if not inlist:
                html.append("<ul>")
                inlist = True
            html.append(f"<li>{bold[2:]}</li>")
        else:
            if inlist:
                html.append("</ul>")
                inlist = False
            html.append(f"<p>{bold}</p>")
    if inlist:
        html.append("</ul>")
    html.append("</body></html>")
    guide_html = GUIDE_OUT.parent.parent / "findings" / "army-choice-guide.html"
    guide_html.write_text("\n".join(html) + "\n", encoding="utf-8")
    print(f"wrote {guide_html}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--guide", action="store_true")
    args = ap.parse_args()
    d = build()
    if args.guide:
        guide(d)
