#!/usr/bin/env python3
"""Generate findings.html for each faction from engine rankings."""
import sys, json, os, html
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
    'tyranids': 'Tyranids',
    'world-eaters': 'World Eaters',
}
MISSIONS = ['Take and Hold', 'Purge the Foe', 'Reconnaissance', 'Priority Assets', 'Disruption']
WEIGHTS = {
    'Take and Hold': {'dps': 0, 'surv': 25, 'obj': 55, 'mob': 20},
    'Purge the Foe': {'dps': 60, 'surv': 15, 'obj': 5, 'mob': 20},
    'Reconnaissance': {'dps': 10, 'surv': 10, 'obj': 20, 'mob': 60},
    'Priority Assets': {'dps': 40, 'surv': 20, 'obj': 30, 'mob': 10},
    'Disruption': {'dps': 25, 'surv': 15, 'obj': 25, 'mob': 35},
}
MISSION_FACTORS = {
    'Take and Hold': {
        'playstyle': 'Hold 2-3 objectives for as many turns as possible.',
        'factors': [
            'OC is king — high OC units lock down objectives (OBJ 55%)',
            'Survivability = turns on objective = more VP (SURV 25%)',
            'Movement less critical — static defence wins',
            'Cost efficiency neutral — quality beats quantity',
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


def build_data(fid):
    """Compute rankings and return DATA dict for JS embedding."""
    e = RankingEngine(fid)
    data = {}
    for m in MISSIONS:
        r = e.compute_ranking(mission=m)
        w = WEIGHTS[m]
        units = []
        for u in r:
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
                'inv': u['surv'].get('invuln'),
                'fnp': u['surv'].get('fnp'),
                'cfnp': u.get('conditional_fnp'),
                'cfnp_type': u.get('conditional_fnp_type'),
                'oc_boost': u.get('oc_boost', 0),
                'cost_eff': u.get('_cost_eff'),
            })
        data[m] = units
    return data


def gen_html(fname, data, n_units):
    """Generate the full findings HTML."""
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
.raw{{font-weight:600;font-size:11px;color:#b0bec5}}</style></head><body>
<div class="back"><a href="../index.html">&larr; All Factions</a></div>
<h1>{fname}</h1>
<div class="subtitle">{n_units} datasheets · {len(MISSIONS)} missions · Quad-vector (DPP + SURV + OBJ + MOB)</div>
<div class="tabs"><div class="tab active" onclick="showTab('missions')">Mission Rankings</div><div class="tab" onclick="showTab('top10')">Top 20 Summary</div><div class="tab" onclick="showTab('insights')">Key Insights</div></div>
<div id="missions" class="tab-content active"></div>
<div id="top10" class="tab-content"></div>
<div id="insights" class="tab-content"></div>
<script>
const DATA={data_json};
const WEIGHTS={weights_json};
const FACTORS={factors_json};

function showTab(id){{document.querySelectorAll('.tab-content').forEach(t=>t.classList.remove('active'));document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));document.getElementById(id).classList.add('active');event.target.classList.add('active')}}
function scoreClass(s){{return s>=75?'score-high':s>=50?'score-mid':'score-low'}}
function rankClass(r){{return r===1?'rank rank-1':r===2?'rank rank-2':r===3?'rank rank-3':'rank'}}
function bar(pct,cls){{return '<div class="bar-bg"><div class="bar-fill '+cls+'" style="width:'+pct+'%"></div><div class="bar-label">'+pct+'%</div></div>'}}
function contrib(v){{return v===0?'<span class="contrib contrib-zero">--</span>':'<span class="contrib contrib-pos">+'+v+'</span>'}}
function renderRow(u,i){{var tags=(u.ds?'<span class=\\"tag tag-ds\\">DS</span>':'')+(u.fly?'<span class=\\"tag tag-fly\\">FLY</span>':'')+(u.inv?'<span class=\\"tag tag-inv\\">INV '+u.inv+'</span>':'')+(u.fnp?'<span class=\\"tag tag-fnp\\">FNP '+u.fnp+'</span>':'')+(u.cfnp?'<span class=\\"tag tag-cfnp\\">CFNP '+u.cfnp+'+ vs '+u.cfnp_type+'</span>':'')+(u.oc_boost?'<span class=\\"tag tag-ocboost\\">OC+'+u.oc_boost+'/banner</span>':'')+(u.cost_eff!==null&&u.cost_eff!==undefined?'<span class=\\"tag tag-cost\\">COST '+u.cost_eff+'</span>':'');return '<tr class="'+(i<3?'top3':'')+'" data-name="'+u.name.toLowerCase()+'"><td class="'+rankClass(i+1)+'">'+(i+1)+'</td><td class="unit-name">'+u.name+'</td><td class="pts">'+u.pts+'</td><td class="score '+scoreClass(u.score)+'">'+u.score+'</td><td class="raw">'+u.dpp+'</td><td class="bar-cell">'+bar(u.dpp_pct,'dpp')+' '+contrib(u.dpp_c)+'</td><td class="raw">'+u.surv_turns+'t</td><td class="bar-cell">'+bar(u.surv_pct,'surv')+' '+contrib(u.surv_c)+'</td><td class="raw">'+u.obj_raw+'</td><td class="bar-cell">'+bar(u.obj_pct,'obj')+' '+contrib(u.obj_c)+'</td><td class="raw">'+u.mob_raw+'</td><td class="bar-cell">'+bar(u.mob_pct,'mob')+' '+contrib(u.mob_c)+'</td><td>'+tags+'</td><td style="font-size:10px;color:#78909c">T'+u.t+' W'+u.w+' OC'+u.oc+'</td></tr>'}}
function filterMission(mid){{var q=document.getElementById('search-'+mid).value.toLowerCase();var rows=document.getElementById('table-'+mid).querySelectorAll('tr[data-name]');var shown=0;rows.forEach(function(r){{var m=!q||r.getAttribute('data-name').indexOf(q)!==-1;r.style.display=m?'':'none';if(m)shown++}});document.getElementById('count-'+mid).textContent=shown+' / '+rows.length+' units'}}
function renderMissions(){{var c=document.getElementById('missions'),html='';for(var mission in DATA){{var units=DATA[mission],w=WEIGHTS[mission],f=FACTORS[mission]||{{}},mid=mission.replace(/[^a-z]/gi,'');var factorHtml='';if(f.playstyle)factorHtml+='<div class="mission-playstyle">'+f.playstyle+'</div>';if(f.factors)factorHtml+='<ul class="factor-list">'+f.factors.map(function(x){{return '<li>'+x+'</li>'}}).join('')+'</ul>';html+='<div class="mission-card"><div class="mission-header"><div class="mission-name">'+mission+' <span style="font-size:13px;color:#78909c">('+units.length+' units)</span></div><div class="mission-weights"><span class="weight w-dpp">DPP '+w.dps+'%</span><span class="weight w-surv">SURV '+w.surv+'%</span><span class="weight w-obj">OBJ '+w.obj+'%</span><span class="weight w-mob">MOB '+w.mob+'%</span></div></div>'+(factorHtml?'<div class="mission-factors">'+factorHtml+'</div>':'')+'<div class="search-bar"><input id="search-'+mid+'" type="text" placeholder="Search units..." oninput="filterMission(\\''+mid+'\\')"><span class="count" id="count-'+mid+'">'+units.length+' / '+units.length+' units</span></div><div class="table-scroll"><table id="table-'+mid+'"><tr><th>#</th><th>Unit</th><th>Pts</th><th>Score</th><th>DPP</th><th class="bar-cell"></th><th>SURV</th><th class="bar-cell"></th><th>OBJ</th><th class="bar-cell"></th><th>MOB</th><th class="bar-cell"></th><th>Tags</th><th>Profile</th></tr>';units.forEach(function(u,i){{html+=renderRow(u,i)}});html+='</table></div></div>'}}c.innerHTML=html}}
function renderTop10(){{var c=document.getElementById('top10'),unitData={{}};for(var mission in DATA){{var units=DATA[mission];for(var i=0;i<units.length;i++){{var u=units[i];if(!unitData[u.name])unitData[u.name]={{name:u.name,pts:u.pts,ds:u.ds,fly:u.fly,inv:u.inv,fnp:u.fnp,cfnp:u.cfnp,cfnp_type:u.cfnp_type,oc_boost:u.oc_boost,t:u.t,w:u.w,oc:u.oc,missions:{{}}}};unitData[u.name].missions[mission]={{score:u.score,rank:i+1}}}}}}for(var k in unitData){{var u=unitData[k],scores=Object.values(u.missions).map(function(m){{return m.score}});u.avgScore=Math.round(scores.reduce(function(a,b){{return a+b}},0)/scores.length*10)/10}}var sorted=Object.values(unitData).sort(function(a,b){{return b.avgScore-a.avgScore}}).slice(0,20);var html='<h2>Top 20 Units (Avg Score)</h2>';sorted.forEach(function(u,idx){{var badges=Object.entries(u.missions).sort(function(a,b){{return b[1].score-a[1].score}}).map(function(kv){{var m=kv[0],v=kv[1];return '<span class="mission-badge '+(v.rank===1?'top1':v.rank<=3?'top3':'top5')+'">#'+v.rank+' '+m+' ('+v.score+')</span>'}}).join(' ');var bc=['#ffd700','#c0c0c0','#cd7f32'];html+='<div class="insight-card" style="border-left-color:'+(idx<3?bc[idx]:'#4fc3f7')+'"><div class="insight-title" style="display:flex;justify-content:space-between"><span>#'+(idx+1)+' '+u.name+'</span><span class="pts">'+u.pts+'pts · avg '+u.avgScore+'</span></div><div style="margin:6px 0">'+(u.ds?'<span class="tag tag-ds">DS</span>':'')+(u.fly?'<span class="tag tag-fly">FLY</span>':'')+(u.inv?'<span class="tag tag-inv">INV '+u.inv+'</span>':'')+(u.fnp?'<span class="tag tag-fnp">FNP '+u.fnp+'</span>':'')+(u.cfnp?'<span class="tag tag-cfnp">CFNP '+u.cfnp+'+ vs '+u.cfnp_type+'</span>':'')+(u.oc_boost?'<span class="tag tag-ocboost">OC+'+u.oc_boost+'/banner</span>':'')+'<span style="font-size:11px;color:#78909c;margin-left:8px">T'+u.t+' W'+u.w+' OC'+u.oc+'</span></div><div>'+badges+'</div></div>'}});c.innerHTML=html}}
function renderInsights(){{var c=document.getElementById('insights'),html='<h2>Key Insights</h2>';for(var mission in DATA){{var units=DATA[mission];if(units.length>0){{var u=units[0];html+='<div class="insight-card"><div class="insight-title">#1 in '+mission+': '+u.name+'</div><div class="insight-text">'+u.score+' score · '+u.pts+'pts · '+u.dpp+' DPP · T'+u.t+' W'+u.w+(u.inv?' INV'+u.inv:'')+(u.fnp?' FNP'+u.fnp:'')+(u.cfnp?' CFNP'+u.cfnp+'+'+u.cfnp_type:'')+(u.oc_boost?' OC+'+u.oc_boost+'/banner':'')+(u.ds?' DS':'')+(u.fly?' FLY':'')+' OC'+u.oc+'</div></div>'}}}}c.innerHTML=html}}
renderMissions();renderTop10();renderInsights();
</script></body></html>'''


if __name__ == '__main__':
    for fid, fname in FACTIONS.items():
        e = RankingEngine(fid)
        n_units = len(set(list(e.config.squads.keys()) + list(e.config.characters.keys()) + list(e.config.vehicles.keys())))
        data = build_data(fid)
        html = gen_html(fname, data, n_units)
        out_dir = os.path.join(OUT, fid)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, 'findings.html'), 'w') as f:
            f.write(html)
        print(f'{fname}: {n_units} units, written to {out_dir}/findings.html')
