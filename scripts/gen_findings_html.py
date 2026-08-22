#!/usr/bin/env python3
"""Generate findings.html for each faction from engine rankings."""
import sys, json, os, html, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.ranking import RankingEngine

FACTIONS = {
    'adepta-sororitas': 'Adepta Sororitas',
    'adeptus-custodes': 'Adeptus Custodes',
    'adeptus-mechanicus': 'Adeptus Mechanicus',
    'aeldari': 'Aeldari',
    'astra-militarum': 'Astra Militarum',
    'black-templars': 'Black Templars',
    'blood-angels': 'Blood Angels',
    'chaos-daemons': 'Chaos Daemons',
    'chaos-knights': 'Chaos Knights',
    'chaos-space-marines': 'Chaos Space Marines',
    'chaos-titan-legions': 'Chaos Titan Legions',
    'dark-angels': 'Dark Angels',
    'death-guard': 'Death Guard',
    'deathwatch': 'Deathwatch',
    'drukhari': 'Drukhari',
    'emperors-children': "Emperor's Children",
    'genestealer-cults': 'Genestealer Cults',
    'grey-knights': 'Grey Knights',
    'imperial-agents': 'Imperial Agents',
    'imperial-knights': 'Imperial Knights',
    'leagues-of-votann': 'Leagues of Votann',
    'necrons': 'Necrons',
    'orks': 'Orks',
    'space-marines': 'Space Marines',
    'space-wolves': 'Space Wolves',
    'tau-empire': "T'au Empire",
    'thousand-sons': 'Thousand Sons',
    'titan-legions': 'Titan Legions',
    'tyranids': 'Tyranids',
    'world-eaters': 'World Eaters',
}

# Landing-page sections: ordered faction slugs per section. Counts are NOT
# hardcoded here — gen_index() reads them from the generated findings.html
# files, so the index can never drift from the faction pages again.
INDEX_SECTIONS = [
    ("Imperium (14 factions)", [
        'adepta-sororitas', 'adeptus-custodes', 'adeptus-mechanicus',
        'astra-militarum', 'black-templars', 'blood-angels', 'dark-angels',
        'deathwatch', 'grey-knights', 'imperial-agents', 'imperial-knights',
        'space-marines', 'space-wolves', 'titan-legions',
    ]),
    ("Chaos (8 factions)", [
        'chaos-daemons', 'chaos-knights', 'chaos-space-marines',
        'chaos-titan-legions', 'death-guard', 'emperors-children',
        'thousand-sons', 'world-eaters',
    ]),
    ("Xenos (8 factions)", [
        'aeldari', 'drukhari', 'genestealer-cults', 'leagues-of-votann',
        'necrons', 'orks', 'tau-empire', 'tyranids',
    ]),
]

INDEX_HEADER = '''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Faction Findings — turtleatlas-w40k-11e</title>
<style>
  *{box-sizing:border-box}
  body{font-family:system-ui,-apple-system,sans-serif;max-width:1100px;margin:0 auto;padding:30px 20px;background:#0d1117;color:#c9d1d9}
  h1{font-size:1.8em;margin:0 0 4px;color:#f0f6fc}
  .subtitle{color:#8b949e;font-size:0.95em;margin-bottom:28px}
  .section{margin-bottom:30px}
  .section h2{font-size:1.1em;color:#8b949e;border-bottom:1px solid #21262d;padding-bottom:8px;margin-bottom:14px;font-weight:600;letter-spacing:0.5px;text-transform:uppercase}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px}
  .card{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;background:#161b22;border:1px solid#30363d;border-radius:8px;text-decoration:none;color:#c9d1d9;transition:border-color 0.15s,background 0.15s}
  .card:hover{border-color:#58a6ff;background:#1c2128;text-decoration:none}
  .fname{font-size:0.95em;font-weight:500}
  .fmeta{font-size:0.8em;color:#6e7681;white-space:nowrap}
  .tierbar{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 16px}
  .tierbtn{padding:6px 14px;background:#161b22;border:1px solid#30363d;border-radius:6px;color:#c9d1d9;font-size:0.85em;cursor:pointer}
  .tierbtn.active{background:#1f6feb;border-color:#1f6feb;color:#fff}
  .tierrow{display:flex;align-items:center;gap:10px;padding:8px 12px;background:#161b22;border:1px solid#30363d;border-radius:8px;margin-bottom:6px;text-decoration:none;color:#c9d1d9}
  .tierrow:hover{border-color:#58a6ff;background:#1c2128;text-decoration:none}
  .tierbadge{flex:0 0 34px;height:34px;display:flex;align-items:center;justify-content:center;border-radius:6px;font-weight:700;font-size:1.05em;color:#fff}
  .t-S{background:#d29922}.t-A{background:#3fb950}.t-B{background:#58a6ff}.t-C{background:#bc8cff}.t-D{background:#6e7681}
  .tiername{flex:1;font-size:0.95em}
  .tierscore{font-size:0.85em;color:#8b949e;white-space:nowrap}
</style></head><body>
<h1>Faction Findings</h1>
<p class="subtitle">DPP rankings for Warhammer 40,000 — 11th Edition. Data-driven, deterministic. No LLM in the loop.</p>
'''


DECAY = 0.95  # rank-decay: effective roster depth ~1/(1-lambda) = 20 units


def extract_army_scores(data, decay=DECAY):
    """Army-level score per mission from build_data output.

    Roster-quality index: weighted mean over ALL ranked datasheets with
    rank-decay weights (best unit counts most, tail still contributes).
    Replaces the synthetic 2000pt draft — real lists aren't greedy stacks,
    role data is too sparse to simulate legal construction, and players
    field variety rather than only their top sheets. Decay answers each
    failure mode:
      - small-roster factions (Chaos Knights ~5 sheets): every sheet counts,
        no arbitrary top-N cliff
      - elite-spike flattery: junk tail drags the score down
      - big-roster bias: weights saturate (sheet #60 ~= zero contribution)

    Per unit: best score across target-mix presets (best tool for the job).

    Returns {mission: score} dict (unrounded floats).
    """
    scores = {}
    for m in MISSIONS:
        best = {}
        for preset_units in data['meta'].values():
            for u in preset_units.get(m, []):
                prev = best.get(u['name'])
                if prev is None or u['score'] > prev[0]:
                    best[u['name']] = (u['score'], u['pts'])
        vals = sorted((v[0] for v in best.values()), reverse=True)
        if not vals:
            scores[m] = 0.0
            continue
        num = sum(s * (decay ** i) for i, s in enumerate(vals))
        den = sum(decay ** i for i in range(len(vals)))
        scores[m] = num / den
    return scores


TIERS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          'findings', 'army_tiers.json')


def compute_tiers_entry(fname, data, n_units):
    """Build one faction's army-tier entry for the landing page."""
    scores = extract_army_scores(data)
    return {
        'name': fname,
        'n_units': n_units,
        'missions': {m: round(s, 1) for m, s in scores.items()},
        'overall': round(sum(scores.values()) / len(scores), 1),
    }


def _tier_of(score, ranked_scores):
    """Percentile-based tier: S top 15%, A next 20%, B middle 30%, C next 20%, D bottom 15%."""
    n = len(ranked_scores)
    rank = ranked_scores.index(score)
    pct = rank / max(n - 1, 1)
    if pct < 0.15:
        return 'S'
    if pct < 0.35:
        return 'A'
    if pct < 0.65:
        return 'B'
    if pct < 0.85:
        return 'C'
    return 'D'


def render_tier_section(tiers):
    """Landing-page army tier list with disposition filter (client-side)."""
    import json as _json
    entries = sorted(tiers.values(), key=lambda t: -t['overall'])
    payload = [
        {'fid': fid, **t}
        for fid, t in tiers.items()
    ]
    data_js = _json.dumps(payload, ensure_ascii=False)

    buttons = ['Overall'] + MISSIONS
    btns_html = ''.join(
        f'<button class="tierbtn{" active" if i == 0 else ""}" '
        f'onclick="setTierMode(this,\'{b}\')">{b}</button>'
        for i, b in enumerate(buttons)
    )

    return (
        '<div class="section">\n'
        '  <h2>Army Tier List</h2>\n'
        f'  <p style="color:#8b949e;font-size:0.85em;margin:0 0 10px">'
        f'Roster-quality index per disposition — weighted mean over all ranked '
        f'datasheets, rank-decayed (best sheets count most, tail still matters; '
        f'effective depth ~20 units). No detachment/army rules. '
        f'Tiers are percentile-banded per view.</p>\n'
        f'  <div class="tierbar" id="tierbar">{btns_html}</div>\n'
        '  <div id="tierlist"></div>\n'
        '</div>\n'
        '<script>\n'
        f'var TIERS={data_js};\n'
        'function setTierMode(btn,mode){document.querySelectorAll(".tierbtn").forEach(function(b){b.classList.remove("active")});btn.classList.add("active");renderTiers(mode)}\n'
        'function tierOf(score,sorted){var r=sorted.indexOf(score);var p=r/Math.max(sorted.length-1,1);return p<0.15?"S":p<0.35?"A":p<0.65?"B":p<0.85?"C":"D"}\n'
        'function renderTiers(mode){var key=mode==="Overall"?null:mode;var rows=TIERS.map(function(t){return{fid:t.fid,name:t.name,score:key?t.missions[key]:t.overall}});rows.sort(function(a,b){return b.score-a.score});var sorted=rows.map(function(r){return r.score});var html="";rows.forEach(function(r,i){var t=tierOf(r.score,sorted);html+=\'<a class="tierrow" href="\'+r.fid+\'/findings.html"><span class="tierbadge t-\'+t+\'">\'+t+\'</span><span class="tiername">\'+(i+1)+". "+r.name+\'</span><span class="tierscore">\'+r.score.toFixed(1)+"</span></a>"});document.getElementById("tierlist").innerHTML=html}\n'
        'renderTiers("Overall");\n'
        '</script>\n'
    )


def gen_index(tiers=None) -> int:
    """Rebuild findings/index.html from the per-faction findings.html files.

    Count = unique unit names across all missions, matching the faction page
    subtitle (build_data's n_units). Factions with a missing findings.html
    are skipped with a warning — never rendered as a fake "0 units" card.

    tiers: {fid: entry} from compute_tiers_entry — renders the army tier list.
    Loaded from findings/army_tiers.json when not provided (--index path).
    """
    counts = {}
    for fid, fname in FACTIONS.items():
        p = os.path.join(OUT, fid, 'findings.html')
        if not os.path.isfile(p):
            continue
        names = set(re.findall(r'\{"name": "([^"]+)"', open(p, encoding='utf-8').read()))
        counts[fid] = len(names)

    tier_section = ''
    if tiers is None and os.path.isfile(TIERS_FILE):
        with open(TIERS_FILE, encoding='utf-8') as f:
            tiers = json.load(f)
    if tiers:
        tier_section = render_tier_section(tiers)

    sections_html = []
    for title, fids in INDEX_SECTIONS:
        cards = []
        for fid in fids:
            if fid not in counts:
                print(f'WARNING: {fid} has no findings.html — card skipped')
                continue
            cards.append(
                f'      <a class="card" href="{fid}/findings.html">\n'
                f'        <span class="fname">{FACTIONS[fid]}</span>\n'
                f'        <span class="fmeta">{counts[fid]} units</span>\n'
                f'      </a>'
            )
        sections_html.append(
            '<div class="section">\n'
            f'  <h2>{title}</h2>\n'
            '  <div class="grid">\n'
            + '\n'.join(cards)
            + '\n  </div>\n</div>'
        )

    html_out = (INDEX_HEADER + tier_section
                + '\n'.join(sections_html) + '\n</body></html>\n')
    out = os.path.join(OUT, 'index.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html_out)
    print(f'index.html written ({len(counts)} factions)')
    return len(counts)
MISSIONS = ['Take and Hold', 'Purge the Foe', 'Reconnaissance', 'Priority Assets', 'Disruption']
WEIGHTS = {
    'Take and Hold': {'dps': 20, 'surv': 30, 'obj': 35, 'mob': 15},
    'Purge the Foe': {'dps': 60, 'surv': 15, 'obj': 5, 'mob': 20},
    'Reconnaissance': {'dps': 10, 'surv': 10, 'obj': 20, 'mob': 60},
    'Priority Assets': {'dps': 40, 'surv': 20, 'obj': 30, 'mob': 10},
    'Disruption': {'dps': 25, 'surv': 15, 'obj': 25, 'mob': 35},
}
MISSION_FACTORS = {
    'Take and Hold': {
        'playstyle': 'Hold 2-3 objectives for as many turns as possible.',
        'factors': [
            'High OC units lock down objectives (OBJ 35%)',
            'Survivability = turns on objective = more VP (SURV 30%)',
            'DPP matters — you still need to clear the point (DPP 20%)',
            'Movement helps reposition between objectives (MOB 15%)',
            'OC0 units cannot score (penalised)',
        ],
    },
    'Purge the Foe': {
        'playstyle': 'Destroy enemy units for VP. Kill more than you lose.',
        'factors': [
            'DPP dominates — raw killing power per point (DPP 60%)',
            'Survivability keeps your damage on the table (SURV 15%)',
            'Movement secondary — need to reach targets (MOB 20%)',
            'OC barely matters — few objectives to hold (OBJ 5%)',
            'High-AP, high-D weapons favoured',
        ],
    },
    'Reconnaissance': {
        'playstyle': 'Perform actions across the board. Board control wins.',
        'factors': [
            'Movement dominates — reach actions, score objectives (MOB 60%)',
            'Cheap units = more actions per 2000pts (cost penalty active)',
            'Deep Strike / Fly = flexible deployment, bypass terrain',
            'OC matters for holding mid-game objectives (OBJ 20%)',
            'DPP nearly irrelevant — not a killing mission (DPP 10%)',
            'OC0 units cannot perform actions (penalised)',
        ],
    },
    'Priority Assets': {
        'playstyle': 'Control specific objectives while dealing damage.',
        'factors': [
            'Balanced damage + objective play (DPP 40%, OBJ 30%)',
            'Survivability keeps units on objectives (SURV 20%)',
            'Movement less critical — fight for fixed positions (MOB 10%)',
            'INV/FNP valuable — units must survive to hold',
            'Mixed roster: killy units + OC units',
        ],
    },
    'Disruption': {
        'playstyle': 'Deny enemy scoring while controlling the board.',
        'factors': [
            'Movement controls tempo — dictate engagements (MOB 35%)',
            'Balanced: need damage, durability, and board presence',
            'Cheap units = more board coverage (cost penalty active)',
            'OC matters for contesting enemy objectives (OBJ 25%)',
            'DPP still relevant — must threaten key targets (DPP 25%)',
            'Deep Strike / Fly for surprise positioning',
            'OC0 units cannot perform actions (penalised)',
        ],
    },
}
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'findings')


# Canonical target-mix scenarios. Every faction exposes these presets via
# config meta_profiles (base defines them; curated factions override with the
# same keys). The findings renderer computes rankings against EACH preset and
# lets the viewer switch. This satisfies the formula-transparency rule: a DPP
# number carries the target composition it was computed against.
META_LABELS = {
    'all-comers': 'Balanced / All-comers',
    'competitive': 'Competitive / Mixed',
    'anti-horde': 'Anti-horde / GEQ swarm',
    'infantry': 'Infantry-heavy / Terminator list',
    'vehicle': 'Vehicle-heavy',
    'elite': 'Elite / Terminator-heavy',
}
# Default preset shown on load per faction. Fallback: first preset in config.
DEFAULT_META = 'competitive'


def _preset_list(supported_meta):
    """Ordered list of (slug, label) for the faction's available metas.

    Preserves config order, dedupes, and reorders so DEFAULT_META is first
    if present. Unknown slugs fall back to their raw slug as label.
    """
    slugs = [k for k in supported_meta.keys() if not k.startswith('_')]
    # de-dupe preserving order
    seen = set()
    ordered = [s for s in slugs if not (s in seen or seen.add(s))]
    if DEFAULT_META in ordered:
        ordered = [DEFAULT_META] + [s for s in ordered if s != DEFAULT_META]
    return [(s, META_LABELS.get(s, s)) for s in ordered]


def _meta_weights_display(supported_configs, slug):
    """Percent weights of a preset for the banner: [[name, pct], ...].

    Normalised to sum 100 so the banner reads as the opponent army mix.
    """
    spec = supported_configs.get(slug)
    if not spec:
        return []
    profiles = spec.get('profiles', spec) if isinstance(spec, dict) else spec
    total = sum(float(w) for _, w in profiles)
    if total <= 0:
        return []
    return [[name, round(float(w) / total * 100)] for name, w in profiles]


def build_data(faction, max_points=2000):
    """Compute rankings per meta preset for a faction.

    Returns (DATA, n_ranked_units) where DATA['meta'][meta][mission] = [unit,...]
    and DATA['meta_info'] lists each preset's slug, display label, and the
    target-mix weights (%) it was computed against. n_ranked_units is the count
    of unique unit names across all metas×missions — the source of truth for
    the displayed unit count (config counts may differ because the engine
    filters out units: max_points, Legends, resolve_loadout → None,
    faction-keyword mismatch, missing merged data).
    """
    e = RankingEngine(faction)
    presets = _preset_list(e.config.meta_profiles)
    meta_info = [{
        'slug': slug,
        'label': label,
        'weights': _meta_weights_display(e.config.meta_profiles, slug),
    } for slug, label in presets]

    data = {}
    all_unit_names = set()
    for slug, _label in presets:
        data[slug] = {}
        for m in MISSIONS:
            r = e.compute_ranking(mission=m, meta_name=slug, max_points=max_points)
            w = WEIGHTS[m]
            units = []
            for u in r:
                all_unit_names.add(u['name'])
                # OBJ raw value
                base_oc = u['mob'].get('objective_control', 0)
                boost = u.get('oc_boost', 0)
                total_oc = (base_oc + boost) * u['surv'].get('models', 1)
                obj_raw = RankingEngine.obj_score(total_oc, u['_surv_turns']) if total_oc > 0 else 0.0

                # Weighted contributions
                dpp_c = round(w['dps'] * u['_dps_pct'] / 100, 1) if w['dps'] else 0
                surv_c = round(w['surv'] * u['_surv_pct'] / 100, 1) if w['surv'] else 0
                obj_c = round(w['obj'] * u['_obj_pct'] / 100, 1) if w.get('obj') else 0
                mob_c = round(w['mob'] * u['_mob_pct'] / 100, 1) if w['mob'] else 0
                units.append({
                    'name': u['name'],
                    'pts': u['points'],
                    'score': round(u['_mission_score'], 1),
                    'dpp': round(u['dpp'], 4),
                    'dpp_pct': u['_dps_pct'],
                    'surv_turns': u['_surv_turns'],
                    'surv_pct': u['_surv_pct'],
                    'obj_raw': round(obj_raw, 1),
                    'obj_pct': u['_obj_pct'],
                    'mob_raw': u['_mob_pct'],
                    'mob_pct': u['_mob_pct'],
                    'dpp_c': dpp_c,
                    'surv_c': surv_c,
                    'obj_c': obj_c,
                    'mob_c': mob_c,
                    'ds': u['mob'].get('deep_strike', False),
                    'fly': u['mob'].get('fly', False),
                    'oc': base_oc,
                    't': u['surv']['toughness'],
                    'w': u['surv']['wounds_per_model'],
                    'wpm': u['surv'].get('wounds_per_model'),
                    'inv': u['surv'].get('invuln'),
                    'fnp': u['surv'].get('fnp'),
                    'cfnp': u.get('conditional_fnp'),
                    'cfnp_type': u.get('conditional_fnp_type'),
                    'oc_boost': u.get('oc_boost', 0),
                    'cost_eff': u.get('_cost_eff'),
                    'loadout': u.get('loadout_desc', ''),
                    'wd': u.get('weapon_details'),
                    'ld': u.get('loadout_detail'),
                })
            data[slug][m] = units
    return {'meta': data, 'meta_info': meta_info}, len(all_unit_names)


def gen_html(fname, data, n_units):
    """Generate the full findings HTML.

    data is the {meta, meta_info} structure from build_data. The whole page is
    re-rendered client-side when the target-mix preset changes; the active mix
    is shown in a banner so every DPP number is interpretable.
    """
    data_json = json.dumps(data, default=str)
    weights_json = json.dumps(WEIGHTS)
    factors_json = json.dumps(MISSION_FACTORS)
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>{fname} — Findings</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:#0a0e14;color:#c5cdd9;padding:20px}}
a{{color:#4fc3f7;text-decoration:none}}a:hover{{text-decoration:underline}}
.back{{margin-bottom:16px;font-size:13px}}
h1{{color:#4fc3f7;font-size:28px;margin-bottom:4px}}
h2{{color:#81c784;font-size:20px;margin:30px 0 15px;border-bottom:1px solid #1a2030;padding-bottom:8px}}
.subtitle{{color:#78909c;font-size:14px;margin-bottom:20px}}
.tabs{{display:flex;gap:4px;margin-bottom:20px;flex-wrap:wrap}}
.tab{{padding:10px 20px;background:#151b24;border:1px solid #263238;border-radius:6px 6px 0 0;cursor:pointer;font-size:13px;color:#90a4ae;transition:all .2s}}
.tab:hover{{background:#1a2030;color:#c5cdd9}}
.tab.active{{background:#0d2137;color:#4fc3f7;border-color:#4fc3f7;border-bottom-color:#0d2137}}
.tab-content{{display:none}}.tab-content.active{{display:block}}
.mission-card{{background:#151b24;border-radius:8px;padding:20px;margin-bottom:20px;border:1px solid #1a2030}}
.mission-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;flex-wrap:wrap;gap:8px}}
.mission-name{{font-size:18px;font-weight:700;color:#eceff1}}
.mission-weights{{display:flex;gap:8px;flex-wrap:wrap}}
.weight{{padding:4px 10px;border-radius:4px;font-size:11px;font-weight:600}}
.w-dpp{{background:#b71c1c;color:#ef9a9a}}.w-surv{{background:#1b5e20;color:#81c784}}
.w-obj{{background:#e65100;color:#ffcc80}}.w-mob{{background:#0d47a1;color:#64b5f6}}
table{{width:100%;border-collapse:collapse;font-size:12px}}
th{{background:#1a2030;color:#90a4ae;padding:8px 6px;text-align:left;font-weight:600;white-space:nowrap;position:sticky;top:0;z-index:1}}
td{{padding:7px 6px;border-bottom:1px solid #1a2030}}
tr:hover{{background:#141c28}}tr.top3{{background:#0d2137}}
.rank{{font-weight:700;color:#4fc3f7;width:30px}}
.rank-1{{color:#ffd700}}.rank-2{{color:#c0c0c0}}.rank-3{{color:#cd7f32}}
.unit-name{{font-weight:600;color:#eceff1}}.pts{{font-weight:600;color:#ffa726}}
.score{{font-weight:700;font-size:13px}}.score-high{{color:#66bb6a}}.score-mid{{color:#ffa726}}.score-low{{color:#ef5350}}
.bar-cell{{width:80px}}
.bar-bg{{background:#1a2030;border-radius:3px;height:14px;position:relative;overflow:hidden}}
.bar-fill{{height:100%;border-radius:3px;position:absolute;top:0;left:0}}
.bar-fill.dpp{{background:linear-gradient(90deg,#b71c1c,#ef5350)}}
.bar-fill.surv{{background:linear-gradient(90deg,#1b5e20,#4caf50)}}
.bar-fill.obj{{background:linear-gradient(90deg,#e65100,#ff9800)}}
.bar-fill.mob{{background:linear-gradient(90deg,#0d47a1,#42a5f5)}}
.bar-label{{position:absolute;right:3px;top:0;font-size:9px;font-weight:600;color:#fff;text-shadow:0 1px 2px rgba(0,0,0,.8);line-height:14px}}
.contrib{{font-size:9px;color:#78909c;text-align:right}}.contrib-pos{{color:#66bb6a}}.contrib-zero{{color:#546e7a}}
.tag{{display:inline-block;padding:1px 5px;border-radius:3px;font-size:9px;font-weight:600;margin-left:3px}}
.tag-ds{{background:#1a237e;color:#7986cb}}.tag-fly{{background:#4a148c;color:#ba68c8}}
.tag-inv{{background:#e65100;color:#ffcc80}}.tag-fnp{{background:#1b5e20;color:#81c784}}
.tag-cfnp{{background:#4a148c;color:#ce93d8}}.tag-ocboost{{background:#004d40;color:#80cbc4}}.tag-cost{{background:#37474f;color:#b0bec5}}
.ld-cell{{position:static;cursor:help}}
.ld-popup{{display:none;position:fixed;z-index:1000;background:#0d1520;border:1px solid #4fc3f7;border-radius:8px;padding:12px 16px;min-width:300px;max-width:90vw;width:420px;box-shadow:0 8px 32px rgba(0,0,0,.6);font-size:11px;color:#b0bec5;text-align:left;white-space:normal}}
.ld-popup h4{{color:#4fc3f7;font-size:12px;margin:0 0 8px;border-bottom:1px solid #1a2030;padding-bottom:4px}}
.ld-popup .ld-weapon{{display:flex;gap:8px;padding:3px 0;border-bottom:1px solid #1a203022;flex-wrap:wrap}}
.ld-popup .ld-weapon:last-child{{border-bottom:none}}
.ld-popup .ld-wslot{{font-weight:700;color:#90a4ae;min-width:48px;text-transform:uppercase;font-size:9px}}
.ld-popup .ld-wname{{color:#eceff1;font-weight:600}}
.ld-popup .ld-wname .ld-count{{color:#ffa726;margin-right:4px}}
.ld-popup .ld-wstats{{color:#78909c;font-size:10px}}
.ld-popup .ld-wvariant{{color:#ffa726;font-size:10px;margin-left:4px}}
.ld-popup .ld-mix{{margin-top:8px;padding-top:6px;border-top:1px solid #1a2030;color:#546e7a;font-size:10px}}
.ld-popup .ld-mix b{{color:#ffa726}}
@media(max-width:600px){{.ld-popup{{position:fixed;right:10px;left:10px;bottom:0;top:auto;width:auto;max-width:none;border-radius:8px 8px 0 0;max-height:50vh;overflow-y:auto}}.ld-cell:hover .ld-popup{{display:none}}.ld-cell.open .ld-popup{{display:block}}}}
.insight-card{{background:#151b24;border-radius:8px;padding:16px;margin-bottom:12px;border-left:4px solid #4fc3f7}}
.insight-title{{font-weight:700;color:#eceff1;margin-bottom:6px}}
.insight-text{{font-size:13px;color:#b0bec5}}
.mission-badge{{display:inline-block;padding:2px 8px;border-radius:3px;font-size:10px;font-weight:600;margin:2px}}
.mission-badge.top1{{background:#1b5e20;color:#81c784}}.mission-badge.top3{{background:#0d47a1;color:#64b5f6}}.mission-badge.top5{{background:#263238;color:#90a4ae}}
.table-scroll{{max-height:80vh;overflow-y:auto}}
.search-bar{{margin-bottom:15px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}}
.search-bar input{{background:#0d2137;border:1px solid #263238;border-radius:6px;padding:8px 14px;color:#eceff1;font-size:13px;width:300px;outline:none}}
.search-bar input:focus{{border-color:#4fc3f7}}.search-bar input::placeholder{{color:#546e7a}}
.search-bar .count{{color:#78909c;font-size:12px}}
.mission-factors{{background:#0d1520;border:1px solid #1a2030;border-radius:6px;padding:12px 16px;margin-bottom:15px}}
.mission-playstyle{{font-size:13px;font-weight:600;color:#b0bec5;margin-bottom:8px;font-style:italic}}
.factor-list{{margin:0;padding-left:18px;font-size:12px;color:#78909c;line-height:1.8}}
.factor-list li{{margin-bottom:2px}}
.raw{{font-weight:600;font-size:11px;color:#b0bec5}}
.preset-banner{{background:#0d1520;border:1px solid #263238;border-radius:8px;padding:12px 16px;margin-bottom:20px;display:flex;flex-wrap:wrap;align-items:center;gap:12px}}
.preset-banner label{{font-size:11px;font-weight:700;color:#90a4ae;text-transform:uppercase;letter-spacing:0.5px}}
.preset-banner select{{background:#0d2137;border:1px solid #4fc3f7;border-radius:6px;padding:8px 12px;color:#eceff1;font-size:13px;outline:none;cursor:pointer}}
.preset-weights{{display:flex;gap:6px;flex-wrap:wrap}}
.preset-weight{{background:#1a2030;border:1px solid #263238;border-radius:4px;padding:3px 8px;font-size:11px;color:#b0bec5}}
.preset-weight b{{color:#ffa726}}
.preset-note{{font-size:11px;color:#546e7a;width:100%}}</style></head><body>
<div class="back"><a href="../index.html" id="back-link">&larr; All Factions</a></div>
<h1>{fname}</h1>
<div class="subtitle">{n_units} datasheets · {len(MISSIONS)} missions · Quad-vector (DPP + SURV + OBJ + MOB)</div>
<div class="preset-banner" id="preset-banner"></div>
<div class="tabs"><div class="tab active" onclick="showTab('missions')">Mission Rankings</div><div class="tab" onclick="showTab('top10')">Top 20 Summary</div><div class="tab" onclick="showTab('insights')">Key Insights</div></div>
<div id="missions" class="tab-content active"></div>
<div id="top10" class="tab-content"></div>
<div id="insights" class="tab-content"></div>
<script>
const DATA={data_json};
const WEIGHTS={weights_json};
const FACTORS={factors_json};
(function(){{
  if(window.location.href.includes('htmlpreview.github.io')){{
    var bl=document.getElementById('back-link');
    if(bl)bl.href='https://htmlpreview.github.io/?https://raw.githubusercontent.com/tommaone/turtleatlas-w40k-11e/main/findings/index.html';
  }}
}})();

function showTab(id){{document.querySelectorAll('.tab-content').forEach(t=>t.classList.remove('active'));document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));document.getElementById(id).classList.add('active');event.target.classList.add('active')}}
function scoreClass(s){{return s>=75?'score-high':s>=50?'score-mid':'score-low'}}
function rankClass(r){{return r===1?'rank rank-1':r===2?'rank rank-2':r===3?'rank rank-3':'rank'}}
function bar(pct,cls){{return '<div class="bar-bg"><div class="bar-fill '+cls+'" style="width:'+pct+'%"></div><div class="bar-label">'+pct+'%</div></div>'}}
function contrib(v){{return v===0?'<span class="contrib contrib-zero">--</span>':'<span class="contrib contrib-pos">+'+v+'</span>'}}
function ldPopup(u){{if(!u.wd&&!u.ld)return'';var h='<div class="ld-popup">';h+='<h4>'+u.name+'</h4>';if(u.ld)h+='<div style="margin-bottom:6px;color:#eceff1;font-size:11px">'+u.ld.replace(/\\[best of [^\\]]+\\]/g,'')+'</div>';if(u.wd&&u.wd.length){{u.wd.forEach(function(w){{var cnt=w.count||1;var cntStr=cnt>1?'<span class="ld-count">'+cnt+'×</span>':'';h+='<div class="ld-weapon"><span class="ld-wslot">'+w.slot+'</span><span class="ld-wname">'+cntStr+w.name+'</span><span class="ld-wstats">A'+w.attacks+' '+w.skill+' S'+w.strength+' AP'+w.ap+' D'+w.damage+'</span>';if(w.abilities&&w.abilities.length)h+='<span class="ld-wvariant">'+w.abilities.join(', ')+'</span>';if(w.variants&&w.variants.length){{h+='<div style="margin-left:56px;margin-top:2px">';w.variants.forEach(function(v){{h+='<span class="ld-wvariant">'+v.name+': A'+v.attacks+' '+v.skill+' S'+v.strength+' AP'+v.ap+' D'+v.damage+'</span> '}});h+='</div>'}}h+='</div>'}})}}h+='<div class="ld-mix">DPP computed vs current target mix</div>';h+='</div>';return h}}
var _ldHideTimer=null;
function _ldPosPopup(el){{var popup=el.querySelector('.ld-popup');if(!popup)return;popup.style.display='block';var rect=el.getBoundingClientRect();var pH=popup.offsetHeight||200;var pW=popup.offsetWidth||420;var vw=window.innerWidth;var vh=window.innerHeight;var left=Math.min(Math.max(10,rect.left),vw-pW-10);if(rect.bottom+pH+10>vh)popup.style.top=Math.max(10,rect.top-pH-4)+'px';else popup.style.top=rect.bottom+4+'px';popup.style.left=left+'px'}}
function _ldHidePopup(el){{var popup=el.querySelector('.ld-popup');if(popup){{popup.style.display='none';popup.style.left='';popup.style.top=''}}}}
function toggleLd(el){{var wasOpen=el.classList.contains('open');document.querySelectorAll('.ld-cell.open').forEach(function(c){{c.classList.remove('open');_ldHidePopup(c)}});if(!wasOpen){{el.classList.add('open');_ldPosPopup(el)}}}}
document.addEventListener('click',function(e){{var cell=e.target.closest('.ld-cell');if(!cell)document.querySelectorAll('.ld-cell.open').forEach(function(c){{c.classList.remove('open');_ldHidePopup(c)}})}});
function renderRow(u,i){{var tags=(u.ds?'<span class=\\"tag tag-ds\\">DS</span>':'')+(u.fly?'<span class=\\"tag tag-fly\\">FLY</span>':'')+(u.inv?'<span class=\\"tag tag-inv\\">INV '+u.inv+'</span>':'')+(u.fnp?'<span class=\\"tag tag-fnp\\">FNP '+u.fnp+'</span>':'')+(u.cfnp?'<span class=\\"tag tag-cfnp\\">CFNP '+u.cfnp+'+ vs '+u.cfnp_type+'</span>':'')+(u.oc_boost?'<span class=\\"tag tag-ocboost\\">OC+'+u.oc_boost+'/banner</span>':'')+(u.cost_eff!==null&&u.cost_eff!==undefined?'<span class=\\"tag tag-cost\\">COST '+u.cost_eff+'</span>':'');return '<tr class="'+(i<3?'top3':'')+'" data-name="'+u.name.toLowerCase()+'"><td class="'+rankClass(i+1)+'">'+(i+1)+'</td><td class="unit-name">'+u.name+'</td><td class="pts">'+u.pts+'</td><td class="score '+scoreClass(u.score)+'">'+u.score+'</td><td class="ld-cell" onclick="toggleLd(this)"><span class="raw">'+u.dpp+'</span>'+ldPopup(u)+'</td><td class="bar-cell">'+bar(u.dpp_pct,'dpp')+' '+contrib(u.dpp_c)+'</td><td class="raw">'+u.surv_turns+'t</td><td class="bar-cell">'+bar(u.surv_pct,'surv')+' '+contrib(u.surv_c)+'</td><td class="raw">'+u.obj_raw+'</td><td class="bar-cell">'+bar(u.obj_pct,'obj')+' '+contrib(u.obj_c)+'</td><td class="raw">'+u.mob_raw+'</td><td class="bar-cell">'+bar(u.mob_pct,'mob')+' '+contrib(u.mob_c)+'</td><td>'+tags+'</td><td style="font-size:10px;color:#78909c">T'+u.t+' W'+u.w+' OC'+u.oc+'</td></tr>'}}
function filterMission(mid){{var q=document.getElementById('search-'+mid).value.toLowerCase();var rows=document.getElementById('table-'+mid).querySelectorAll('tr[data-name]');var shown=0;rows.forEach(function(r){{var m=!q||r.getAttribute('data-name').indexOf(q)!==-1;r.style.display=m?'':'none';if(m)shown++}});document.getElementById('count-'+mid).textContent=shown+' / '+rows.length+' units'}}
var ACTIVE='';
function isActive(meta){{return ACTIVE===''||ACTIVE===meta}}
function renderBanner(){{var b=document.getElementById('preset-banner'),opts=DATA.meta_info.map(function(p){{var sel=isActive(p.slug)?' selected':'';return '<option value="'+p.slug+'"'+sel+'>'+p.label+'</option>'}}).join('');var info=DATA.meta_info.filter(function(m){{return isActive(m.slug)}})[0]||DATA.meta_info[0];var weights=(info&&info.weights?info.weights.map(function(w){{return '<span class="preset-weight">'+w[0]+' <b>'+w[1]+'%</b></span>'}}).join(''):'');b.innerHTML='<div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;width:100%"><label for="meta-select">Target mix</label><select id="meta-select" onchange="setMeta(this.value)">'+opts+'</select><div class="preset-weights">'+weights+'</div></div><div class="preset-note">DPP is computed against this opponent army composition. Pack your list against a different meta and the rankings re-rank.</div>'}}
function setMeta(slug){{ACTIVE=slug;renderBanner();renderMissions();renderTop10();renderInsights()}}
function renderMissions(){{var c=document.getElementById('missions'),html='';var meta=ACTIVE===''?DATA.meta_info[0].slug:ACTIVE;for(var mission in DATA.meta[meta]){{var units=DATA.meta[meta][mission],w=WEIGHTS[mission],f=FACTORS[mission]||{{}},mid=mission.replace(/[^a-z]/gi,'');var factorHtml='';if(f.playstyle)factorHtml+='<div class="mission-playstyle">'+f.playstyle+'</div>';if(f.factors)factorHtml+='<ul class="factor-list">'+f.factors.map(function(x){{return '<li>'+x+'</li>'}}).join('')+'</ul>';html+='<div class="mission-card"><div class="mission-header"><div class="mission-name">'+mission+' <span style="font-size:13px;color:#78909c">('+units.length+' units)</span></div><div class="mission-weights"><span class="weight w-dpp">DPP '+w.dps+'%</span><span class="weight w-surv">SURV '+w.surv+'%</span><span class="weight w-obj">OBJ '+w.obj+'%</span><span class="weight w-mob">MOB '+w.mob+'%</span></div></div>'+(factorHtml?'<div class="mission-factors">'+factorHtml+'</div>':'')+'<div class="search-bar"><input id="search-'+mid+'" type="text" placeholder="Search units..." oninput="filterMission(\\''+mid+'\\')"><span class="count" id="count-'+mid+'">'+units.length+' / '+units.length+' units</span></div><div class="table-scroll"><table id="table-'+mid+'"><tr><th>#</th><th>Unit</th><th>Pts</th><th>Score</th><th>DPP</th><th class="bar-cell"></th><th>SURV</th><th class="bar-cell"></th><th>OBJ</th><th class="bar-cell"></th><th>MOB</th><th class="bar-cell"></th><th>Tags</th><th>Profile</th></tr>';units.forEach(function(u,i){{html+=renderRow(u,i)}});html+='</table></div></div>'}}c.innerHTML=html}}
function renderTop10(){{var c=document.getElementById('top10'),unitData={{}};var meta=ACTIVE===''?DATA.meta_info[0].slug:ACTIVE;for(var mission in DATA.meta[meta]){{var units=DATA.meta[meta][mission];for(var i=0;i<units.length;i++){{var u=units[i];if(!unitData[u.name])unitData[u.name]={{name:u.name,pts:u.pts,ds:u.ds,fly:u.fly,inv:u.inv,fnp:u.fnp,cfnp:u.cfnp,cfnp_type:u.cfnp_type,oc_boost:u.oc_boost,t:u.t,w:u.w,oc:u.oc,missions:{{}}}};unitData[u.name].missions[mission]={{score:u.score,rank:i+1}}}}}}for(var k in unitData){{var u=unitData[k],scores=Object.values(u.missions).map(function(m){{return m.score}});u.avgScore=Math.round(scores.reduce(function(a,b){{return a+b}},0)/scores.length*10)/10}}var sorted=Object.values(unitData).sort(function(a,b){{return b.avgScore-a.avgScore}}).slice(0,20);var html='<h2>Top 20 Units (Avg Score)</h2>';sorted.forEach(function(u,idx){{var badges=Object.entries(u.missions).sort(function(a,b){{return b[1].score-a[1].score}}).map(function(kv){{var k=kv[0],v=kv[1];return '<span class="mission-badge '+(v.rank===1?'top1':v.rank<=3?'top3':'top5')+'">#'+v.rank+' '+k+' ('+v.score+')</span>'}}).join(' ');var bc=['#ffd700','#c0c0c0','#cd7f32'];html+='<div class="insight-card" style="border-left-color:'+(idx<3?bc[idx]:'#4fc3f7')+'"><div class="insight-title" style="display:flex;justify-content:space-between"><span>#'+(idx+1)+' '+u.name+'</span><span class="pts">'+u.pts+'pts · avg '+u.avgScore+'</span></div><div style="margin:6px 0">'+(u.ds?'<span class="tag tag-ds">DS</span>':'')+(u.fly?'<span class="tag tag-fly">FLY</span>':'')+(u.inv?'<span class="tag tag-inv">INV '+u.inv+'</span>':'')+(u.fnp?'<span class="tag tag-fnp">FNP '+u.fnp+'</span>':'')+(u.cfnp?'<span class="tag tag-cfnp">CFNP '+u.cfnp+'+ vs '+u.cfnp_type+'</span>':'')+(u.oc_boost?'<span class="tag tag-ocboost">OC+'+u.oc_boost+'/banner</span>':'')+'<span style="font-size:11px;color:#78909c;margin-left:8px">T'+u.t+' W'+u.w+' OC'+u.oc+'</span></div><div>'+badges+'</div></div>'}});c.innerHTML=html}}
function renderInsights(){{var c=document.getElementById('insights'),html='<h2>Key Insights</h2>';var meta=ACTIVE===''?DATA.meta_info[0].slug:ACTIVE;for(var mission in DATA.meta[meta]){{var units=DATA.meta[meta][mission];if(units.length>0){{var u=units[0];html+='<div class="insight-card"><div class="insight-title">#1 in '+mission+': '+u.name+'</div><div class="insight-text">'+u.score+' score · '+u.pts+'pts · '+u.dpp+' DPP · T'+u.t+' W'+u.w+(u.inv?' INV'+u.inv:'')+(u.fnp?' FNP'+u.fnp:'')+(u.cfnp?' CFNP'+u.cfnp+'+'+u.cfnp_type:'')+(u.oc_boost?' OC+'+u.oc_boost+'/banner':'')+(u.ds?' DS':'')+(u.fly?' FLY':'')+' OC'+u.oc+'</div></div>'}}}}c.innerHTML=html}}
renderBanner();renderMissions();renderTop10();renderInsights();
document.addEventListener('mouseover',function(e){{var cell=e.target.closest('.ld-cell');if(cell){{clearTimeout(_ldHideTimer);if(!cell.classList.contains('open'))_ldPosPopup(cell)}}}});
document.addEventListener('mouseout',function(e){{var cell=e.target.closest('.ld-cell');if(cell){{var related=e.relatedTarget?e.relatedTarget.closest('.ld-cell'):null;if(related!==cell)_ldHideTimer=setTimeout(function(){{if(!cell.classList.contains('open'))_ldHidePopup(cell)}},150)}}}});
</script></body></html>'''


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Generate faction findings HTML')
    parser.add_argument('--all', action='store_true', help='Generate for all factions')
    parser.add_argument('--faction', type=str, help='Generate for a specific faction slug')
    parser.add_argument('--index', action='store_true',
                        help='Rebuild findings/index.html from existing faction pages')
    parser.add_argument('--max-points', type=int, default=2000,
                        help='Max unit points to include in rankings (default: 2000, 0=no limit)')
    args = parser.parse_args()

    max_pts = args.max_points if args.max_points > 0 else None

    if args.index and not args.faction and not args.all:
        gen_index()
        sys.exit(0)

    factions_to_gen = FACTIONS
    if args.faction:
        factions_to_gen = {args.faction: FACTIONS[args.faction]}

    tiers = None
    tiers_path = os.path.join(OUT, 'army_tiers.json')
    if os.path.isfile(tiers_path):
        with open(tiers_path, encoding='utf-8') as f:
            tiers = json.load(f)

    for fid, fname in factions_to_gen.items():
        data, n_units = build_data(fid, max_points=max_pts)
        html = gen_html(fname, data, n_units)
        out_dir = os.path.join(OUT, fid)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, 'findings.html'), 'w') as f:
            f.write(html)
        print(f'{fname}: {n_units} units, written to {out_dir}/findings.html')
        # Army tier list — only meaningful when generating the full faction set
        if not args.faction:
            tiers = tiers or {}
            tiers[fid] = compute_tiers_entry(fname, data, n_units)
            with open(tiers_path, 'w', encoding='utf-8') as f:
                json.dump(tiers, f, indent=1, ensure_ascii=False)

    # --all regenerates the landing page too, so counts can't drift
    if args.all:
        gen_index(tiers=tiers)
