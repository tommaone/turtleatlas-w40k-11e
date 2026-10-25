#!/usr/bin/env python3
"""Army advisor: which faction to play, from engine-derived facts.

Modular by design: emits findings/advisor.json (machine-readable, MCP /
conversational ready) and can render docs/army-choice-guide.md (--guide).

Metrics per faction (all derived from engine outputs, never re-computed):
- overall_index      rank-decay score across the 5 dispositions (copied
                     verbatim from findings/army_tiers.json `overall`)
- floor / ceiling    worst / best disposition score
- versatility        100 - (ceiling-floor) spread; high = plays every mission
- roster_depth       ranked datasheet count
- points_churn       MFM changelog mentions since edition start (GW attention)

Play-fit heuristics are LLM-synthesis tier (🔴 STRATEGY): they combine
engine facts with assumptions listed in the output. `meta_ceiling` and
`meta_ceiling_best_detachment` are RETIRED (2026-08-27) and always null:
detachment-aware scoring was cancelled, not pending.

Usage:
    python3 scripts/army_advisor.py            # writes findings/advisor.json
    python3 scripts/army_advisor.py --guide    # also renders the markdown guide
"""
import argparse
from datetime import date
import json
import re
from pathlib import Path
import statistics
import glob
from html import escape as _html_escape

REPO = Path(__file__).resolve().parent.parent
TIERS = REPO / "findings" / "army_tiers.json"
CHANGELOG_DIR = REPO / "mfm" / "changelog"
GENERATED = '2026-10-21'  # frozen for reproducible artifacts


_VERSION_RE = re.compile(r"v(\d+)\.(\d+)")


def _esc(text: str) -> str:
    """HTML-escape for text content: & < > only.

    Quotes stay literal — every interpolation sits between tags, not in an
    attribute, so escaping them only churns the output.
    """
    return _html_escape(text, quote=False)


def _version_files() -> list:
    """Changelog version files, parsed and sorted ascending by (major, minor).

    One predicate shared by mfm_version() and points_churn(), so a stray
    v1.5-draft.md cannot be counted by the churn tally while being ignored by
    the version claim (or vice versa).
    """
    if not CHANGELOG_DIR.is_dir():
        raise FileNotFoundError(
            f"changelog directory missing: {CHANGELOG_DIR}. The MFM submodule "
            "may not be initialised."
        )
    out = []
    for path in CHANGELOG_DIR.glob("v*.md"):
        m = _VERSION_RE.fullmatch(path.stem)
        if m:
            out.append(((int(m.group(1)), int(m.group(2))), path))
    if not out:
        raise FileNotFoundError(f"no version files under {CHANGELOG_DIR}")
    return sorted(out, key=lambda t: t[0])


def mfm_version() -> str:
    """Latest MFM version present in the changelog dir, e.g. 'v1.5'.

    Derived rather than hardcoded: the header once said 'MFM v1.4' while the
    data underneath was already v1.5.
    """
    (major, minor), _ = _version_files()[-1]
    return f"v{major}.{minor}"

ADVISOR_OUT = REPO / "findings" / "advisor.json"
GUIDE_OUT = REPO / "docs" / "army-choice-guide.md"

CAVEATS = [
    "meta_ceiling and meta_ceiling_best_detachment are RETIRED (2026-08-27) "
    "and null for every faction: detachment strength is an expert heuristic, "
    "not an engine number, so no detached-scores ceiling is produced. Use "
    "overall_index / ceiling / floor, which are engine output",
    "statline quality persists across balance patches; rules packages do not",
    "points churn counts changelog mentions since edition start - a proxy "
    "for GW attention, not a prediction; Astartes flavours share one codex "
    "so their churn is partially double-counted",
    "win-rate correlation is partial: community results include rules "
    "packaging this index deliberately excludes",
    "first-army-fit is an expert judgement (user-domain + rule-text "
    "sourced per faction in resources/experts) — re-audit when the meta "
    "or play preferences shift",
]


def durability_map():
    """FACT layer: median wounds + share of multi-wound units per faction.

    Statline bulk FACT — NOT a skill-floor / first-army signal. The band
    reads the whole roster INCLUDING vehicles, so a faction with a fragile
    2W infantry core plus a few Land Raiders medians out as "Durable".
    Example: world-eaters median W = 8 (11 infantry entries out of 30).
    Use this only to describe model bulk in advisor.json; first-army
    recommendations come from expert first-army-fit ratings instead.
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
                    "statline_band": band}
    return out


FIT_ORDER = {"Great": 4, "Good": 3, "Demanding": 2, "Bad": 1, "Unrated": 0}


def first_army_fit_map() -> dict[str, dict]:
    """EXPERT layer: first-army-fit band per faction from expert files.

    Single source of truth: resources/experts/<fid>.md — the `### First-Army
    Fit` bullet is authored there WITH a source trail and is never re-derived
    here. Factions without the line rate Unrated and are excluded from
    first-army recommendations (the engine cannot certify noob-friendliness).
    """
    out = {}
    for path in sorted((REPO / "resources" / "experts").glob("*.md")):
        m = re.search(
            r"\*\*First-Army Fit\*\*:\s*(Great|Good|Demanding|Bad|Unrated)"
            r"\s*—\s*(.+)",
            path.read_text())
        if not m:
            out[path.stem] = {"band": "Unrated", "why": ""}
            continue
        out[path.stem] = {"band": m.group(1), "why": m.group(2).strip()}
    return out


def _norm_name(s: str) -> str:
    """Normalise a faction display name for matching.

    The changelog uses typographic apostrophes (Emperor\u2019s Children,
    T\u2019au Empire); the tiers table uses ASCII ones. Case varies too.
    """
    return (
        s.replace("\u2019", "'").replace("\u2018", "'").strip().lower()
    )


def points_churn() -> dict[str, int]:
    """Count changelog mentions per faction, as a proxy for GW attention.

    The MFM submodule restructured this file (2026-09): DATA-CHANGELOG.md
    became a pointer and the entries moved to changelog/v<X.Y>.md. The old
    parser read only DATA-CHANGELOG.md and silently returned {} after the
    bump, which zeroed points_churn for all 28 factions.

    Two formats coexist and must both be counted:
      v1.0-v1.4  '- **Faction**: ...' bullets (many per faction)
      v1.5+      '### Faction  _(v1.4 -> v1.5)_' sections (one per faction)
    They do not overlap - v1.5 has zero bullets and older files zero tables -
    so summing both cannot double-count.
    """
    counts: dict[str, int] = {}
    for _, path in _version_files():
        text = path.read_text(encoding="utf-8")
        names = re.findall(r"^- \*\*([^*]+?)\*\*:", text, re.M)
        names += [n.strip() for n in re.findall(r"^### ([^_]+?)\s*_\(.*?\)", text, re.M)]
        for raw in names:
            key = _norm_name(raw)
            if key:
                counts[key] = counts.get(key, 0) + 1
    return counts


def compute():
    """Pure computation: returns the advisor dict without writing files."""
    tiers = json.loads(TIERS.read_text())
    churn = points_churn()
    fit = first_army_fit_map()
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
            "points_churn": churn.get(_norm_name(t["name"]), 0),
            "first_army_fit": fit.get(fid, {}).get("band", "Unrated"),
            "first_army_fit_why": fit.get(fid, {}).get("why", ""),
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
        "generated": GENERATED,
        "factions": factions,
    }
    return out


def build():
    """compute() + write advisor.json (the CLI path)."""
    out = compute()
    ADVISOR_OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"wrote {ADVISOR_OUT} ({len(out['factions'])} factions)")
    return out


SIGNALS_DOC = """\
## How to read this (plain words — judgement layer, not engine fact)

The engine measures how strong each faction's models are on paper
(statlines and points). It cannot measure rules packages, skill floor,
or how punishing an army is to play — those are the expert calls below,
each carrying a source trail in the faction's expert file.

- **Strength** — where the faction ranks today on model quality.
  Changes with balance updates; a strong army can get nerfed.
- **Versatility** — does it fight well on every mission type, or only
  one? Versatile armies forgive list-building mistakes.
- **First-army fit** — expert-rated Great / Good / Demanding / Bad,
  authored in resources/experts/<faction>.md. This is a skill-floor
  judgement, NOT engine fact. Engine "statline bulk" (median wounds
  across the whole roster, vehicles included) is listed in
  findings/advisor.json as reference only — it is NOT a first-army
  signal: World Eaters read "Durable" off a vehicle-inflated median
  while their 2W melee core punishes every positioning error.
- **GW attention** — factions whose points changed a lot recently keep
  changing. Playing one means accepting that your points and rules
  will move under you.

"""


def guide_lines(data):
    """Build the markdown lines for the army-choice guide (no file writes).

    Testable: the regression tests assert on these lines without touching
    generated artifacts.
    """
    f = data["factions"]
    n = len(f)
    third = max(n // 3, 1)
    half = max(n // 2, 1)
    quart = max(n // 4, 1)
    fit = first_army_fit_map()
    for x in f:
        x["difficulty"] = fit.get(x["fid"], {}).get("band", "Unrated")
        x["fit_why"] = fit.get(x["fid"], {}).get("why", "")

    vers = sorted(y["versatility"] for y in f)
    foundations = [x for x in f[:third] if x["versatility"] >= vers[half]]
    low_vers = vers[quart]  # bottom quartile — first-army needs >= this
    specialists = [x for x in f
                   if x["ceiling"] >= f[0]["ceiling"] - 3
                   and x["versatility"] <= low_vers][:6]
    tuning = sorted(f, key=lambda x: -x["points_churn"])[:quart]
    value = [x for x in f[third:2 * third] if x["versatility"] >= vers[half]]

    lines = [
        "# Choosing Your Army — strength, versatility, fit",
        "",
        f"*Generated {GENERATED} from engine outputs (rank-decay roster "
        f"index, MFM {mfm_version()}) + expert first-army-fit ratings. Full "
        f"method + caveats in findings/advisor.json.*",
        "",
        "> This narrows the field — it tells you where each faction's "
        "strength sits today and what the army demands from you as a "
        "player. It cannot tell you the future meta.",
        "",
        SIGNALS_DOC,
        "## If this is your first army",
        "",
        "> Start with a faction expert-rated **Great** (or **Good** with "
        "versatility above the bottom quarter). "
        "Statline bulk (big wound pools) is an engine fact, NOT a skill-"
        "floor signal — World Eaters read 'Durable' off a vehicle-inflated "
        "wound median while their 2W melee core punishes every positioning "
        "error.",
        "",
        "> Factions not listed have no expert first-army-fit rating yet: "
        "their engine strength is shown below, but the guide cannot "
        "certify them as forgiving.",
        "",
    ]
    forgiving = [x for x in f
                 if FIT_ORDER.get(x["difficulty"], 0) >= FIT_ORDER["Good"]
                 and (x["difficulty"] == "Great"
                      or x["versatility"] >= low_vers)]
    lines += [f"- **{x['name']}** — {x['fit_why'].split(' Sourced:')[0]}"
              for x in forgiving[:6]] or ["- (none clear the bar this pass)"]
    lines += [
        "",
        "## Strongest long-term signal",
    ]
    lines += [f"- **{x['name']}** — strength {x['overall_index']}, plays all "
              f"missions ({x['difficulty']} first-army fit)"
              for x in foundations]
    lines += ["", "## Specialist picks (strong in one mission)", ""]
    lines += [f"- **{x['name']}** — shines in {x['best_disposition']}"
              f" ({x['difficulty']} first-army fit)" for x in specialists]
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
    return lines


def render_guide_html(lines):
    """Render the guide's markdown subset to a standalone HTML page.

    Everything interpolated here descends from expert files and engine
    output, so each field is HTML-escaped before it is wrapped in a tag —
    a stray & or < in a faction's why-text must not reach the page raw.
    """
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

    def _bold(t):
        # Escape first, then promote **md** to <strong> (our own markup, so
        # it must survive the escape that precedes it).
        return _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", _esc(t))

    for ln in lines:
        s = ln.strip()
        if not s:
            if inlist:
                html.append("</ul>")
                inlist = False
            continue
        if s.startswith("## "):
            if inlist:
                html.append("</ul>")
                inlist = False
            html.append(f"<h2>{_re.sub(r'</?strong>', '', _bold(s[3:]))}</h2>")
        elif s.startswith("# "):
            html.append(f"<h1>{_bold(s[2:])}</h1>")
        elif s.startswith(">"):
            html.append(f"<blockquote>{_bold(s.lstrip('> '))}</blockquote>")
        elif s.startswith("- "):
            if not inlist:
                html.append("<ul>")
                inlist = True
            html.append(f"<li>{_bold(s[2:])}</li>")
        else:
            if inlist:
                html.append("</ul>")
                inlist = False
            html.append(f"<p>{_bold(s)}</p>")
    if inlist:
        html.append("</ul>")
    html.append("</body></html>")
    return "\n".join(html) + "\n"


def guide(data):
    lines = guide_lines(data)
    GUIDE_OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {GUIDE_OUT}")

    # findings/army-choice-guide.html — same content, rendered for the
    # landing-page link (a raw .md URL is not user-friendly anywhere).
    guide_html = GUIDE_OUT.parent.parent / "findings" / "army-choice-guide.html"
    guide_html.write_text(render_guide_html(lines), encoding="utf-8")
    print(f"wrote {guide_html}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--guide", action="store_true")
    args = ap.parse_args()
    d = build()
    if args.guide:
        guide(d)
