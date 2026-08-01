#!/usr/bin/env python3
"""Bulk-convert legacy squad configs to builds format with modes.

Mechanical conversion following the playbook
(docs/changes/army-config-refresh-playbook.md) Phase 3 semantics:

- No-option squads (specials == []) -> single "Melee" build, all n models
  at default loadout.
- Squads with specials -> "Melee" default + one mode per special named
  "Nx <special>" where N = special_max, models: [N special models + (n-N)
  default models]. Special replacement semantics mirror the engine legacy
  path (_eval_squad_variant):
    sp_loses_r (default True)  -> special model's ranged IS the special
    sp_loses_m (default False) -> special model's melee becomes Close combat weapon
    apoth_loses_r              -> LAST model loses its ranged (apothecary)
- Legacy fields removed: specials, special_max, sp_loses_r, sp_loses_m,
  apoth_loses_r, apoth_loses_m.
- pts verified against mfm/data/<slug>.yaml (first-tier convention);
  pts_3rd filled from MFM [3,) tier when present.
- Every weapon name is verified to resolve through the engine; unresolved
  names are reported (exit 2) for hand-fixing, file is still written.

Usage: python3 scripts/convert_squad_builds.py <slug> [<slug> ...]
       python3 scripts/convert_squad_builds.py --all-legacy
"""
import json
import sys
import os

import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LEGACY_KEYS = ("specials", "special_max", "sp_loses_r", "sp_loses_m",
               "apoth_loses_r", "apoth_loses_m")

DONE = {'chaos-daemons', 'grey-knights', 'death-guard', 'emperors-children',
        'genestealer-cults', 'tyranids', 'drukhari', 'leagues-of-votann',
        'chaos-knights', 'chaos-titan-legions', 'imperial-knights', 'titan-legions'}


def mfm_pts_map(slug):
    path = f'mfm/data/{slug}.yaml'
    if not os.path.exists(path):
        return {}
    data = yaml.safe_load(open(path))
    out = {}
    for u in data.get('units', []):
        name = (u.get('name') or '').lower()
        costs = {}
        for p in u.get('pricing', []):
            rng = p.get('range', '')
            for c in p.get('costs', []):
                key = '3rd' if rng.startswith('[3') else '1st'
                # keep the smallest-models first cost for the tier
                if key not in costs:
                    costs[key] = c.get('points')
        out[name] = costs
    return out


def convert_squad(name, cfg):
    """Return (new_cfg, warnings). Mirrors _eval_squad_variant semantics."""
    n = cfg['n']
    specials = cfg.get('specials', [])
    special_max = cfg.get('special_max', 0)
    sp_loses_r = cfg.get('sp_loses_r', True)
    sp_loses_m = cfg.get('sp_loses_m', False)
    apoth_loses_r = cfg.get('apoth_loses_r', False)
    base_ranged = cfg.get('ranged')
    base_melee = cfg.get('melee') or 'Close combat weapon'

    def default_model():
        m = {}
        if base_ranged:
            m['ranged'] = base_ranged
            if 'ranged_a' in cfg:
                m['ranged_a'] = cfg['ranged_a']
        m['melee'] = base_melee
        return m

    def special_model(sname):
        m = {'ranged': sname}
        m['melee'] = 'Close combat weapon' if sp_loses_m else base_melee
        return m

    builds = []
    # Default build: all n models at base loadout
    builds.append({'name': 'Melee', 'models': [{'count': n, **default_model()}]})

    # One mode per special
    for sname in specials:
        n_sp = min(special_max, n)
        models = [{'count': n_sp, **special_model(sname)}]
        rest = n - n_sp
        if rest > 0:
            models.append({'count': rest, **default_model()})
        label = f'{n_sp}x {sname}' if n_sp > 1 else sname
        builds.append({'name': label, 'models': models})

    new = {
        'n': n,
        'pts': cfg['pts'],
        'ranged': cfg.get('ranged'),
        'melee': cfg.get('melee'),
        'innate': cfg.get('innate', []),
        'info': cfg.get('info', {}),
    }
    if 'pts_3rd' in cfg:
        new['pts_3rd'] = cfg['pts_3rd']
    if cfg.get('innate'):
        new['innate'] = cfg['innate']
    new['builds'] = builds
    warnings = []
    if apoth_loses_r:
        warnings.append(f"{name}: apoth_loses_r dropped (builds format has no apothecary slot)")
    return new, warnings


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    if args == ['--all-legacy']:
        import glob
        slugs = []
        for path in sorted(glob.glob('data/config/*/squads.json')):
            slug = path.split('/')[2]
            if slug in DONE:
                continue
            sq = json.load(open(path))
            if any('specials' in v for v in sq.values() if isinstance(v, dict)):
                slugs.append(slug)
    else:
        slugs = args

    from engine.ranking import RankingEngine

    exit_code = 0
    for slug in slugs:
        path = f'data/config/{slug}/squads.json'
        if not os.path.exists(path):
            print(f"SKIP {slug}: no squads.json")
            continue
        sq = json.load(open(path))
        meta = {k: v for k, v in sq.items() if k.startswith('_')}
        eng = RankingEngine(slug)
        pts_map = mfm_pts_map(slug)

        new_sq = {}
        new_sq.update(meta)
        unresolved = []
        pts_fixes = []
        warnings_all = []
        for name, cfg in sq.items():
            if not isinstance(cfg, dict) or name.startswith('_'):
                continue
            if 'builds' in cfg:
                new_sq[name] = cfg  # already converted
                continue
            new_cfg, warns = convert_squad(name, cfg)
            warnings_all.extend(warns)
            # pts fix vs MFM
            mfm = pts_map.get(name.lower())
            if mfm:
                if mfm.get('1st') is not None and new_cfg['pts'] != mfm['1st']:
                    pts_fixes.append(f"{name}: {new_cfg['pts']} -> {mfm['1st']}")
                    new_cfg['pts'] = mfm['1st']
                if mfm.get('3rd') is not None and new_cfg.get('pts_3rd') != mfm['3rd']:
                    if 'pts_3rd' in new_cfg or True:
                        pts_fixes.append(f"{name} pts_3rd: {new_cfg.get('pts_3rd')} -> {mfm['3rd']}")
                        new_cfg['pts_3rd'] = mfm['3rd']
            # verify weapon resolution
            for b in new_cfg['builds']:
                for m in b['models']:
                    for key in ('ranged', 'melee'):
                        w = m.get(key)
                        if not w:
                            continue
                        try:
                            eng.W(w, unit_name=name)
                        except Exception:
                            unresolved.append(f"{name}/{b['name']}: {key} '{w}' does NOT resolve")
            new_sq[name] = new_cfg

        with open(path, 'w') as f:
            json.dump(new_sq, f, indent=2, ensure_ascii=False)
            f.write('\n')

        n_conv = sum(1 for k, v in new_sq.items()
                     if isinstance(v, dict) and not k.startswith('_') and 'builds' in v)
        print(f"=== {slug}: {n_conv} squads with builds")
        for p in pts_fixes:
            print(f"  pts {p}")
        for w in warnings_all:
            print(f"  WARN {w}")
        for u in unresolved:
            print(f"  UNRESOLVED {u}")
        if unresolved:
            exit_code = 2
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
