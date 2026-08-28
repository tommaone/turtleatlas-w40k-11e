"""Generate docs/detachment-l2-review.html — human-readable L2 review workbook.

Renders EVERY faction's detachments.json scaffold + merged MFM enhancements +
L2 expert fields (when present) into ONE self-contained HTML file in the repo's
findings style. The user reviews detachment ratings in the browser — the JSON
files stay the source of truth; this page is a read/annotate view.

Deterministic: render() is a pure function of repo data (factions sorted,
detachments sorted by dp_cost then name). Run `python3 scripts/
gen_detach_review_html.py` to regenerate (commit the output together with any
reviewed JSON, so the browser view and the data never drift).

Slugs use the canonical generator slugify (apostrophes stripped, straight and
curly) — imported, never re-implemented.
"""

from __future__ import annotations

import html
import json
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))  # allow `from scripts.... import` when run as script

from scripts.generate_detachments_heuristic import slugify

CONFIG_DIR = REPO_ROOT / "data" / "config"
MERGED_DIR = REPO_ROOT / "data" / "merged"
DRAFT_DIR = REPO_ROOT / "workspace" / "detachment-drafts"
OUT_PATH = REPO_ROOT / "docs" / "detachment-l2-review.html"

L2_STRENGTHS = {"Strong", "Moderate", "Situational", "Weak"}
L2_TEMPO_AXES = {"infiltration", "attrition", "stat-augment", "castle", "rush"}

_CSS = """
  body{font-family:system-ui,-apple-system,sans-serif;max-width:1100px;margin:0 auto;padding:30px 20px;background:#0d1117;color:#c9d1d9;line-height:1.5}
  h1{font-size:1.5em;margin:0 0 4px}
  h2{margin-top:34px;border-bottom:1px solid #30363d;padding-bottom:6px}
  h3{margin:0;font-size:1.05em}
  .meta{color:#8b949e;font-size:.85em}
  .badges{display:flex;gap:6px;flex-wrap:wrap}
  .badge{padding:2px 10px;border-radius:999px;font-size:.75em;border:1px solid #30363d;background:#161b22}
  .badge.dp{color:#58a6ff;border-color:#1f6feb}
  .badge.disp{color:#7ee787}
  .badge.done{color:#fff;background:#238636;border-color:#238636}
  .badge.pending{color:#d29922;border-color:#d29922}
  .badge.draft{color:#a371f7;border-color:#a371f7;background:#2a1f47}
  .card{padding:14px 16px;background:#161b22;border:1px solid #30363d;border-radius:8px;margin:10px 0}
  .cardhead{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;flex-wrap:wrap}
  .slug{font-family:ui-monospace,SFMono-Regular,monospace;font-size:.8em;color:#8b949e}
  dl{margin:10px 0 0;display:grid;grid-template-columns:190px 1fr;gap:4px 14px;font-size:.9em}
  dt{color:#8b949e}
  dd{margin:0}
  .pending{color:#484f58;font-style:italic}
  .enh{display:inline-block;margin-right:10px;color:#c9d1d9}
  .enh b{color:#58a6ff}
  table{width:100%;border-collapse:collapse;font-size:.9em}
  th,td{text-align:left;padding:6px 10px;border-bottom:1px solid #30363d}
  th{color:#8b949e;font-weight:600}
  details{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:10px 14px;margin:14px 0}
  summary{cursor:pointer;color:#58a6ff;font-weight:600}
  code{font-family:ui-monospace,SFMono-Regular,monospace;background:#0d1117;padding:1px 5px;border-radius:4px;font-size:.85em}
  a{color:#58a6ff}
"""


def _esc(s) -> str:
    return html.escape(str(s), quote=True)


def _fmt_list(items) -> str:
    return ", ".join(_esc(i) for i in items)


def render_rule(entry: dict) -> str:
    rule = entry.get("rule") or {}
    text = rule.get("text", "")
    parts = []
    if text:
        parts.append(f"<span>{_esc(text)} <span class='meta'>(_paraphrase: {bool(rule.get('_paraphrase'))}, _lang: {_esc(rule.get('_lang', ''))})</span></span>")
    affects = rule.get("affects")
    if affects:
        parts.append(f"<span>affects: {_fmt_list(affects)}</span>")
    src = rule.get("_source")
    if src:
        links = " ".join(
            f'<a href="{_esc(u)}" target="_blank" rel="noopener">{_esc(u)}</a>' for u in src
        )
        parts.append(f"<span>source: {links}</span>")
    return "<br>".join(parts)


def render_best_units(entry: dict) -> str:
    items = entry.get("best_units", [])
    if not items:
        return ""
    lines = []
    for bu in items:
        why = bu.get("why", "")
        src = bu.get("_source") or []
        srcs = ", ".join(_esc(s) for s in src)
        lines.append(
            f"<b>{_esc(bu.get('unit', '?'))}</b>{' — ' + _esc(why) if why else ''}"
            f"{' <span class=\'meta\'>[' + srcs + ']</span>' if srcs else ''}"
        )
    return "<br>".join(lines)


def render_spam(entry: dict) -> str:
    items = entry.get("spam", [])
    if not items:
        return ""
    lines = []
    for sp in items:
        why = sp.get("why", "")
        lines.append(
            f"{_esc(sp.get('count', ''))}× <b>{_esc(sp.get('unit', '?'))}</b>"
            f"{' with ' + _esc(sp.get('with', '')) if sp.get('with') else ''}"
            f"{' — ' + _esc(why) if why else ''}"
        )
    return "<br>".join(lines)


def render_combos(entry: dict) -> str:
    items = entry.get("combos", [])
    if not items:
        return ""
    lines = []
    for cb in items:
        effects = cb.get("effects", "")
        lines.append(
            f"<b>{_esc(cb.get('combo', ''))}</b>"
            f"{' — ' + _esc(effects) if effects else ''}"
        )
    return "<br>".join(lines)


def render_l2_field(entry: dict, field: str) -> str:
    """Render one L2 field's value for an entry; '' means not present."""
    if field == "rule":
        return render_rule(entry)
    if field == "best_units":
        return render_best_units(entry)
    if field == "spam":
        return render_spam(entry)
    if field == "combos":
        return render_combos(entry)
    val = entry.get(field)
    if val is None:
        return ""
    if isinstance(val, list):
        return _fmt_list(val)
    if isinstance(val, dict):
        if field == "play_style":
            parts = []
            if val.get("summary"):
                parts.append(_esc(val["summary"]))
            if val.get("tempo_axis"):
                parts.append(f"<span class='meta'>tempo: {_esc(val['tempo_axis'])}</span>")
            return "<br>".join(parts)
        return _esc(json.dumps(val, ensure_ascii=False))
    return _esc(val)


# canonical L2 field order + human labels
L2_FIELDS = [
    ("rule", "Rule (paraphrase)"),
    ("best_units", "Best units"),
    ("scoring_units", "Scoring units"),
    ("support_units", "Support units"),
    ("hammer_units", "Hammer units"),
    ("spam", "Spam / leaders"),
    ("combos", "Combos (internal)"),
    ("strength", "Strength"),
    ("strength_notes", "Strength notes"),
    ("limitations", "Limitations"),
    ("play_style", "Play style"),
]


L2_EXPERT_FIELDS = {f for f, _ in L2_FIELDS}


def _enhancements_for(faction: str, slug: str) -> list[dict]:
    merged_path = MERGED_DIR / f"{faction}.json"
    if not merged_path.exists():
        return []
    for det in json.loads(merged_path.read_text()).get("detachments", []):
        if slugify(det.get("name", "")) == slug:
            return det.get("enhancements", [])
    return []


def _draft_for(faction: str) -> dict:
    """L2 drafts from workspace (gitignored, LLM drafts — never committed data).

    Returns {slug: entry}. Drafts must only overlay L2 fields over the
    committed scaffold; they may not invent detachments (Tier-6 lock)."""
    p = DRAFT_DIR / f"{faction}.draft.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text()).get("detachments", {})


def _drafted_count(draft: dict) -> int:
    return sum(1 for e in draft.values() if any(f in e for f in L2_EXPERT_FIELDS))


def render() -> str:
    factions = sorted(p.name for p in CONFIG_DIR.iterdir()
                      if p.is_dir() and (p / "detachments.json").exists())
    total_dets = 0
    total_reviewed_dets = 0
    total_drafted_dets = 0
    reviewed_factions = 0
    drafted_factions = 0
    sections = []
    matrix_rows = []

    for faction in factions:
        data = json.loads((CONFIG_DIR / faction / "detachments.json").read_text())
        meta = data.get("_meta", {})
        entries = data.get("detachments", {})
        faction_reviewed = bool(meta.get("human_reviewed"))
        if faction_reviewed:
            reviewed_factions += 1
        draft = _draft_for(faction)
        faction_drafted = bool(draft) and not faction_reviewed
        if faction_drafted:
            drafted_factions += 1

        det_cards = []
        for slug in sorted(entries, key=lambda s: (entries[s].get("dp_cost") or 99, s)):
            entry = entries[slug]
            # L2 overlay from the workspace draft (never committed data)
            display = {**entry, **draft.get(slug, {})}
            total_dets += 1
            entry_reviewed = faction_reviewed
            if entry_reviewed:
                total_reviewed_dets += 1
            elif slug in draft:
                total_drafted_dets += 1

            badges = [
                f"<span class='badge dp'>dp {entry.get('dp_cost')}</span>",
                f"<span class='badge disp'>{_esc(entry.get('disposition', ''))}</span>",
            ]
            if entry_reviewed:
                badges.append("<span class='badge done'>✓ human-reviewed</span>")
            elif slug in draft:
                badges.append("<span class='badge draft'>DRAFT (unverified)</span>")
            else:
                badges.append("<span class='badge pending'>pending</span>")

            dl_rows = [
                (f"objective", _esc(display.get("objective", ""))),
                ("source (L0)", _esc(display.get("source", ""))),
            ]
            if slug in draft:
                dl_rows.append(("draft", "<span class='badge draft'>workspace draft — verify before promoting</span>"))
            enh = _enhancements_for(faction, slug)
            if enh:
                enh_html = " ".join(
                    f"<span class='enh'>{_esc(e['name'])} <b>{e.get('points', '')} pts</b></span>"
                    for e in enh
                )
                dl_rows.append(("enhancements (MFM)", enh_html))
            for field, label in L2_FIELDS:
                val = render_l2_field(display, field)
                if val:
                    dl_rows.append((label, val))
                else:
                    dl_rows.append((label, "<span class='pending'>— pending —</span>"))

            dl = "".join(f"<dt>{_esc(label)}</dt><dd>{value}</dd>" for label, value in dl_rows)
            det_cards.append(
                f"<article class='card' id='{_esc(faction)}-{_esc(slug)}'>"
                f"<div class='cardhead'><h3>{_esc(display.get('name', slug))}</h3>"
                f"<div class='badges'>{''.join(badges)}</div></div>"
                f"<div class='slug'>{_esc(slug)}</div>"
                f"<dl>{dl}</dl></article>"
            )

        idx = _esc(meta.get("index", faction))
        anchor = faction
        status_cell = "✓" if faction_reviewed else f"{_drafted_count(draft)}/{len(entries)}" if draft else "✗"
        matrix_rows.append(
            f"<tr><td><a href='#{anchor}'>{_esc(faction)}</a></td>"
            f"<td>{len(entries)}</td>"
            f"<td>{status_cell}</td></tr>"
        )
        reviewed_marker = " <b style='color:#7ee787'>reviewed</b>" if faction_reviewed else (
            f" <span class='meta'>{_drafted_count(draft)}/ drafty</span>" if draft else ""
        )
        sections.append(
            f"<section id='{anchor}'><h2>{_esc(faction)} "
            f"<span class='meta'>({len(entries)} detachments{reviewed_marker})</span></h2>"
            + "".join(det_cards) + "</section>"
        )

    drafted_note = (
        f" · {total_drafted_dets} drafted (<span class='badge draft'>DRAFT</span> = "
        f"workspace, unverified)" if total_drafted_dets else ""
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Detachment L2 Review Workbook — turtleatlas</title>
<style>{_CSS}</style>
</head>
<body>
<header>
<h1>Detachment L2 Review Workbook</h1>
<p class="meta">generated {date.today().isoformat()} · {len(factions)} factions · {total_dets} detachments · {total_reviewed_dets} reviewed{drafted_note} · source: scripts/gen_detach_review_html.py · JSON files remain the source of truth; drafts live in workspace/ (gitignored)</p>
</header>

<details open>
<summary>Review rules (rule.text = mechanical paraphrase)</summary>
<ul>
<li>EN paraphrase of mechanics, <b>no verbatim GW rule text</b>, <b>no lore</b> — `rule.text` flags `_paraphrase: true`, `_lang: "en"` (&le;600 chars).</li>
<li>Detachment names and keywords stay <b>exact</b> (&ldquo;Cabal Of Chaos&rdquo;, PSYKER, FACTION:&hellip;).</li>
<li>Every fact traces to L0 <code>_source</code> (MFM / Wahapedia / NewRecruit / analyst) — no opinions without source.</li>
<li>strength: Strong / Moderate / Situational / Weak, always with `strength_notes` + `limitations`.</li>
<li><span class='badge draft'>DRAFT</span> = LLM draft from workspace (unverified). Verify, then promote into <code>data/config/&lt;faction&gt;/detachments.json</code> and flip <code>_meta.human_reviewed: true</code> — commit per faction.</li>
</ul>
</details>

<h2>Status</h2>
<table>
<tr><th>faction</th><th>detachments</th><th>reviewed / drafted</th></tr>
{''.join(matrix_rows)}
<tr><td><b>total</b></td><td><b>{total_dets}</b></td><td><b>{total_reviewed_dets} reviewed · {total_drafted_dets} drafted</b></td></tr>
</table>

{''.join(sections)}
</body>
</html>
"""


def main() -> None:
    OUT_PATH.write_text(render() + "\n")
    print(f"{OUT_PATH.relative_to(REPO_ROOT)} written "
          f"({len(render().splitlines())} lines)")


if __name__ == "__main__":
    main()