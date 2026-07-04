"""
GK Unit Ranking — thin CLI wrapper around generic engine/ranking.py.

All hardcoded data extracted to data/config/grey-knights/*.json.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.ranking import RankingEngine

# ── Engine instance (lazy) ──────────────────────────────────────────
_ENGINE: RankingEngine | None = None


def _engine():
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = RankingEngine("grey-knights")
    return _ENGINE


# ── Backward-compat exports ────────────────────────────────────────
# Target, mission, meta profiles
TARGET_PROFILES = {}       # populated on-demand below
MISSION_PROFILES = {}
META_PROFILES = {}
MEQ = None

# Module-level init
def _init():
    global TARGET_PROFILES, MISSION_PROFILES, META_PROFILES, MEQ
    eng = _engine()
    # TargetProfile objects
    TARGET_PROFILES.update(eng.config.target_profiles)
    MISSION_PROFILES.update(eng.config.mission_profiles)
    META_PROFILES.update(eng.config.meta_profiles)
    MEQ = TARGET_PROFILES.get("MEQ")

_init()

# ── Public API ─────────────────────────────────────────────────────

def compute_ranking(target=MEQ, mission=None, meta_name=None, tier="1st"):
    """Compute unit ranking delegating to generic engine."""
    return _engine().compute_ranking(target=target, mission=mission, meta_name=meta_name, tier=tier)


def print_ranking(results, target_name="MEQ", mission_name=None, meta_name=None, tier="1st"):
    """Print ranking delegating to generic engine."""
    return _engine().print_ranking(results, target_name=target_name,
                                    mission_name=mission_name, meta_name=meta_name, tier=tier)


def mob_score(mob):
    """Mobility score 0-100."""
    return RankingEngine.mob_score(mob)


def resolve_loadout(name, target=MEQ, pricing=None):
    """Resolve loadout delegating to generic engine."""
    return _engine().resolve_loadout(name, target=target, pricing=pricing)


def best_squad_variant(name, target=MEQ):
    """Best squad variant delegating to generic engine."""
    return _engine()._best_squad_variant(name, target)


def best_vehicle_variant(ranged_names, melee_names, unit_name, target=MEQ):
    """Best vehicle variant delegating to generic engine."""
    return _engine()._best_vehicle_variant(ranged_names, melee_names, unit_name, target)


# ── CLI ────────────────────────────────────────────────────────────

def main():
    import argparse
    eng = _engine()
    targets = eng.config.target_profiles
    missions = eng.config.mission_profiles
    metas = eng.config.meta_profiles

    parser = argparse.ArgumentParser(description="Unit Ranking — three-vector DPS/SURV/MOB")
    parser.add_argument("--target", "-t", default="MEQ",
                        choices=list(targets.keys()),
                        help="Target profile to evaluate DPP against (ignored if --meta set)")
    parser.add_argument("--mission", "-m", default=None,
                        choices=list(missions.keys()),
                        help="Mission profile for weighted ranking")
    parser.add_argument("--tier", default="1st", choices=["1st", "3rd"],
                        help="Pricing tier: 1st unit (default) or 3rd+ unit")
    parser.add_argument("--matrix", action="store_true",
                        help="Print cross-target DPP matrix and exit")
    parser.add_argument("--meta", default=None,
                        choices=list(metas.keys()),
                        help="Multi-target meta profile (loadouts optimised for weighted mix)")
    args = parser.parse_args()

    if args.matrix:
        if args.meta:
            by_target = {}
            meta_targets = eng.config._resolve_meta(args.meta)
            for tn, _, _ in meta_targets:
                tp = targets[tn]
                by_target[tn] = compute_ranking(target=tp, tier=args.tier)
            print(f"## Meta Matrix: {args.meta}\n")
            _print_matrix(by_target)
        else:
            by_target = {}
            for tn, tp in targets.items():
                by_target[tn] = compute_ranking(target=tp, tier=args.tier)
            _print_matrix(by_target)
        return

    if args.meta:
        results = compute_ranking(target=MEQ, mission=args.mission, meta_name=args.meta, tier=args.tier)
        print_ranking(results, target_name=None, mission_name=args.mission, meta_name=args.meta, tier=args.tier)
    else:
        target = targets[args.target]
        results = compute_ranking(target=target, mission=args.mission, tier=args.tier)
        print_ranking(results, target_name=args.target, mission_name=args.mission, tier=args.tier)


def _print_matrix(results_by_target):
    """Print cross-target DPP matrix for top units."""
    target_names = list(results_by_target.keys())
    all_units = {}
    for tn, results in results_by_target.items():
        for r in results:
            all_units.setdefault(r["name"], {})[tn] = r["dpp"]
    scored = []
    for uname, tdps in all_units.items():
        avg = sum(tdps.values()) / len(tdps)
        scored.append((avg, uname, tdps))
    scored.sort(reverse=True)
    print("## Cross-Target DPP Matrix (top 12)\n")
    print("```")
    header = f'{"Unit":<40s}'
    for tn in target_names:
        header += f' {tn:>9s}'
    print(header)
    print("-" * len(header))
    for avg, uname, tdps in scored[:12]:
        line = f'{uname:<40s}'
        for tn in target_names:
            val = tdps.get(tn, 0)
            line += f' {val:>9.4f}'
        print(line)
    print("```\n")


if __name__ == "__main__":
    main()
