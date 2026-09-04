"""Generate docs/detachment-atlas/ — per-army, layer-separated (L0-L4) HTML.

One self-contained page PER FACTION (docs/detachment-atlas/<faction>.html)
plus an index page. Each army page renders the layers separately:

  L0  PRVO-ZDROJE   - MFM facts (dp, objective, enhancements) + dispositions
                      + L0 source references (merged/config JSON paths)
  L1  ARMY (live)   - no static file exists (lego model, 2026-08-28):
                      army-level interpretation is composed live by the LLM
  L2  DETACHMENT    - static facts: rule paraphrase + strength/strength_notes
                      + limitations (committed data + workspace draft overlay)
  L3  ENGINE        - link to findings/<faction>/findings.html (engine output)
  L4  EXPERT CACHE  - link to resources/experts/<faction>.md (NL cache)

The JSON files stay the source of truth; pages are a read/annotate view.
Deterministic: all render_* functions are pure functions of COMMITTED repo
data. Workspace drafts (gitignored, unverified LLM L2 overlay) are NEVER
part of the committed render — the test suite locks byte-identity, so any
gitignored input would make the suite red on clean checkouts. Draft overlay
is available opt-in via `--with-drafts` for local review workbooks.
Slugs use the canonical generator slugify (apostrophes stripped, straight
and curly) — imported, never re-implemented.
"""

from __future__ import annotations

import html
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))  # allow `from scripts.... import` when run as script

from scripts.generate_detachments_heuristic import slugify

CONFIG_DIR = REPO_ROOT / "data" / "config"
MERGED_DIR = REPO_ROOT / "data" / "merged"
DRAFT_DIR = REPO_ROOT / "workspace" / "detachment-drafts"
FINDINGS_DIR = REPO_ROOT / "findings"
EXPERTS_DIR = REPO_ROOT / "resources" / "experts"
ATLAS_DIR = REPO_ROOT / "docs" / "detachment-atlas"

L2_STRENGTHS = {"Strong", "Moderate", "Situational", "Weak"}
L2_SOURCE_LABELS = {
    "wahapedia": "Wahapedia",
    "newrecruit": "NewRecruit",
    "40k.app": "40k.app",
    "tabletopbattles": "Goonhammer (tabletopbattles)",
    "mfm": "MFM",
    "bsdata": "BSData",
}

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
  .layer{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px 16px;margin:12px 0}
  .layer.l0{border-color:#1f6feb}
  .layer.l2{border-color:#a371f7}
  .layer.l3{border-color:#7ee787}
  .layer.l4{border-color:#d29922}
  .layer h3{margin-bottom:4px}
  .card{padding:14px 16px;background:#0d1117;border:1px solid #30363d;border-radius:8px;margin:10px 0}
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


def _rel(from_file: Path, to: Path) -> str:
    """Relative URL from a generated page to a repo path (../-aware)."""
    return os.path.relpath(to, from_file.parent).replace(os.sep, "/")


def _has_valid_source(draft_rule: dict) -> bool:
    """A draft rule is only worth showing when it carries an L0 source."""
    return bool(draft_rule and draft_rule.get("_source"))


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


def render_l2_field(entry: dict, field: str) -> str:
    """Render one L2 field's value for an entry; '' means not present."""
    if field == "rule":
        return render_rule(entry)
    val = entry.get(field)
    if val is None:
        return ""
    if isinstance(val, list):
        return _fmt_list(val)
    return _esc(val)


# canonical L2 field order + human labels — STATIC FACTS only (lego bricks).
# Unit roles, combos, play_style, army tips are composed LIVE by the LLM from
# L0-L3 at query time; they are never stored in L2 (distillate-of-distillate).
L2_FIELDS = [
    ("rule", "Rule (paraphrase)"),
    ("strength", "Strength"),
    ("strength_notes", "Strength notes"),
    ("limitations", "Limitations"),
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


def _l0_section(faction: str, meta: dict, entries: dict) -> str:
    """L0 prvo-zdroje: overené dáta (MFM detachments, dispositions, zdroje)."""
    merged = json.loads((MERGED_DIR / f"{faction}.json").read_text())
    merged_dets = merged.get("detachments", [])
    rows = []
    for det in merged_dets:
        slug = slugify(det.get("name", ""))
        entry = entries.get(slug, {})
        enh = det.get("enhancements", [])
        enh_html = " ".join(
            f"<span class='enh'>{_esc(e.get('name',''))} <b>{e.get('points','')} pts</b></span>"
            for e in enh
        )
        rows.append(
            f"<tr><td><a href='#l2-{_esc(slug)}'>{_esc(det.get('name',''))}</a></td>"
            f"<td>{det.get('dp','')}</td>"
            f"<td>{_esc(entry.get('disposition',''))}</td>"
            f"<td>{_esc(det.get('objective',''))}</td>"
            f"<td>{enh_html}</td></tr>"
        )
    merged_url = _rel(ATLAS_DIR / f"{faction}.html", MERGED_DIR / f"{faction}.json")
    config_url = _rel(ATLAS_DIR / f"{faction}.html", CONFIG_DIR / faction / "detachments.json")
    return (
        "<div class='layer l0'><h3>L0 — Prvo-zdroje (overené dáta)</h3>"
        "<p class='meta'>MFM: body, detachmenty (dp, objective), enhancements · "
        f"config: dispositions. Zdrojové súbory: "
        f"<a href='{merged_url}'>{_esc(faction)}.json (merged)</a> · "
        f"<a href='{config_url}'>config detachments.json</a></p>"
        "<table><tr><th>detachment</th><th>dp</th><th>disposition</th>"
        "<th>objective</th><th>enhancements (MFM)</th></tr>"
        + "".join(rows) + "</table></div>"
    )


def _l1_section() -> str:
    """L1 army vrstva — neexistuje žiadny statický súbor (lego model)."""
    return (
        "<div class='layer'><h3>L1 — Army vrstva (neexistuje ako súbor)</h3>"
        "<p class='meta'>Lego model (2026-08-28): army-level interpretácia (ktorý "
        "detachment s ktorým, archetypy, 3DP combos, herný štýl) sa skladá NAŽIVO "
        "LLM-om z L0 + L2 + L3 + kontext otázky. `army_profile.json` bol REJECTED — "
        "perzistovať kompozíciu = destilát destilátu.</p></div>"
    )


def _l2_section(faction: str, meta: dict, entries: dict, draft: dict) -> str:
    """L2 detachment fakty: rule parafráza + strength (draft overlay)."""
    faction_reviewed = bool(meta.get("human_reviewed"))
    cards = []
    for slug in sorted(entries, key=lambda s: (entries[s].get("dp_cost") or 99, s)):
        entry = entries[slug]
        # L2 overlay from the workspace draft (never committed data)
        display = {**entry, **draft.get(slug, {})}
        badges = [
            f"<span class='badge dp'>dp {entry.get('dp_cost')}</span>",
            f"<span class='badge disp'>{_esc(entry.get('disposition', ''))}</span>",
        ]
        if faction_reviewed:
            badges.append("<span class='badge done'>✓ human-reviewed</span>")
        elif slug in draft:
            badges.append("<span class='badge draft'>DRAFT (unverified)</span>")
        else:
            badges.append("<span class='badge pending'>pending</span>")

        dl_rows = [
            ("objective", _esc(display.get("objective", ""))),
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
        cards.append(
            f"<article class='card' id='l2-{_esc(slug)}'>"
            f"<div class='cardhead'><h3>{_esc(display.get('name', slug))}</h3>"
            f"<div class='badges'>{''.join(badges)}</div></div>"
            f"<div class='slug'>{_esc(slug)}</div>"
            f"<dl>{dl}</dl></article>"
        )
    reviewed_marker = " <b style='color:#7ee787'>reviewed</b>" if faction_reviewed else (
        f" <span class='meta'>{_drafted_count(draft)}/{len(entries)} drafted</span>" if draft else ""
    )
    return (
        f"<div class='layer l2'><h3>L2 — Detachment info (statické fakty)</h3>"
        f"<p class='meta'>{len(entries)} detachments{reviewed_marker} · rule = EN parafráza "
        f"mechaniky (nie GW text, nie lore) · strength = AI rating (traceable) · "
        f"unit roles/combos/play_style sa neukladajú — skladajú naživo</p>"
        + "".join(cards) + "</div>"
    )


def _l3_section(faction: str) -> str:
    p = FINDINGS_DIR / faction / "findings.html"
    if not p.exists():
        return (
            "<div class='layer l3'><h3>L3 — Engine ranking</h3>"
            "<p class='meta'>findings pre túto frakciu zatiaľ neboli vygenerované "
            "(scripts/gen_findings_html.py)</p></div>"
        )
    url = _rel(ATLAS_DIR / f"{faction}.html", p)
    return (
        "<div class='layer l3'><h3>L3 — Engine ranking (kalkulovaný výstup)</h3>"
        f"<p class='meta'>Ranking jednotiek (DPP/SURV/MOB) podľa engine — generalist, "
        f"best gear. <a href='{url}'>otvoriť findings/{_esc(faction)}/findings.html</a></p></div>"
    )


def _l4_section(faction: str) -> str:
    p = EXPERTS_DIR / f"{faction}.md"
    if not p.exists():
        return (
            "<div class='layer l4'><h3>L4 — Expert analysis (cache)</h3>"
            "<p class='meta'>expert file pre túto frakciu neexistuje</p></div>"
        )
    url = _rel(ATLAS_DIR / f"{faction}.html", p)
    return (
        "<div class='layer l4'><h3>L4 — Expert analysis (cache, nie zdroj)</h3>"
        f"<p class='meta'>LLM reasoning cache platný k danému dátumu — NIE je zdrojom "
        f"pipeline. <a href='{url}'>otvoriť experts/{_esc(faction)}.md</a></p></div>"
    )


def render_faction(faction: str, with_drafts: bool = False) -> str:
    data = json.loads((CONFIG_DIR / faction / "detachments.json").read_text())
    meta = data.get("_meta", {})
    entries = data.get("detachments", {})
    # gitignored workspace drafts are opt-in (local review workbooks only);
    # the committed render must never depend on them (determinism lock).
    draft = _draft_for(faction) if with_drafts else {}
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Detachment Atlas — {_esc(faction)} (L0-L4)</title>
<style>{_CSS}</style>
</head>
<body>
<header>
<p class="meta"><a href="index.html">← index</a></p>
<h1>{_esc(meta.get("index", faction))} <span class="meta">({_esc(faction)})</span></h1>
<p class="meta">vrstvy L0-L4 oddelené · JSON files remain the source of truth; workspace drafts are NOT part of the committed render</p>
</header>

{_l0_section(faction, meta, entries)}
{_l1_section()}
{_l2_section(faction, meta, entries, draft)}
{_l3_section(faction)}
{_l4_section(faction)}
</body>
</html>
"""


def render_index(with_drafts: bool = False) -> str:
    factions = sorted(p.name for p in CONFIG_DIR.iterdir()
                      if p.is_dir() and (p / "detachments.json").exists())
    total_dets = 0
    total_reviewed = 0
    total_drafted = 0
    rows = []
    for faction in factions:
        data = json.loads((CONFIG_DIR / faction / "detachments.json").read_text())
        meta = data.get("_meta", {})
        entries = data.get("detachments", {})
        draft = _draft_for(faction) if with_drafts else {}
        faction_reviewed = bool(meta.get("human_reviewed"))
        n = len(entries)
        total_dets += n
        drafted = _drafted_count(draft)
        if faction_reviewed:
            total_reviewed += n
        else:
            total_drafted += drafted
        status = "✓ reviewed" if faction_reviewed else (
            f"{drafted}/{n} drafted" if draft else "✗ pending"
        )
        rows.append(
            f"<tr><td><a href='{_esc(faction)}.html'>{_esc(faction)}</a></td>"
            f"<td>{n}</td><td>{_esc(status)}</td></tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Detachment Atlas — {len(factions)} armies (L0-L4)</title>
<style>{_CSS}</style>
</head>
<body>
<header>
<h1>Detachment Atlas</h1>
<p class="meta">per-army, layer-separated (L0-L4) · {len(factions)} factions · {total_dets} detachments · {total_reviewed} reviewed · {total_drafted} drafted · source: scripts/gen_detach_review_html.py · JSON files remain the source of truth; workspace drafts are NOT part of the committed render</p>
</header>

<details open>
<summary>Vrstvy (per army)</summary>
<ul>
<li><b>L0</b> — prvo-zdroje: MFM fakty (dp, objective, enhancements), dispositions, zdrojové súbory.</li>
<li><b>L1</b> — army vrstva: žiaden statický súbor (lego model 2026-08-28). Interpretácia sa skladá NAŽIVO.</li>
<li><b>L2</b> — detachment fakty: rule parafráza (<code>_paraphrase: true</code>, &le;600 chars) + strength (AI rating, traceable) + limitations.</li>
<li><b>L3</b> — engine ranking: <code>findings/&lt;faction&gt;/findings.html</code> (DPP/SURV/MOB).</li>
<li><b>L4</b> — expert cache: <code>resources/experts/&lt;faction&gt;.md</code> (nie zdroj pipeline).</li>
</ul>
</details>

<h2>Status</h2>
<table>
<tr><th>faction</th><th>detachments</th><th>reviewed / drafted</th></tr>
{''.join(rows)}
<tr><td><b>total</b></td><td><b>{total_dets}</b></td><td><b>{total_reviewed} reviewed · {total_drafted} drafted</b></td></tr>
</table>
</body>
</html>
"""


FACTIONS = sorted(
    p.name for p in CONFIG_DIR.iterdir()
    if p.is_dir() and (p / "detachments.json").exists()
)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--with-drafts", action="store_true",
        help="overlay gitignored workspace L2 drafts (local review workbook; "
             "NOT for committed output — breaks the determinism lock)",
    )
    args = parser.parse_args()
    ATLAS_DIR.mkdir(parents=True, exist_ok=True)
    (ATLAS_DIR / "index.html").write_text(render_index(with_drafts=args.with_drafts) + "\n")
    n = 1
    for faction in FACTIONS:
        (ATLAS_DIR / f"{faction}.html").write_text(
            render_faction(faction, with_drafts=args.with_drafts) + "\n"
        )
        n += 1
    print(f"{ATLAS_DIR.relative_to(REPO_ROOT)} written ({n} pages)")


if __name__ == "__main__":
    main()