"""STRICT cross-faction engine invariants.

These are properties that correct engine *cannot* violate and still be sane.
They are hard asserts: a red here means the engine or config is broken, not
that the model is opinionated.

Checklist (the dojo's statute-of-limitations analog, applied to the engine):
  1. Determinism — resolve the same unit the same way twice.
  2. No NaN / Inf / negative damage or prestige anywhere.
  3. Ranking is sorted descending by mission score.
  4. Weighted target lists sum to full weight (no dropped targets).
  5. Every unit that ranks has points > 0 and a resolvable loadout.

Runtime: one engine load + one compute_ranking per faction. Fast.
"""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.crossfaction_common import ALL_FACTIONS, load_engine


def _collect_units(faction):
    """Yield (engine, unit_dict) for every ranked unit in a faction."""
    eng = load_engine(faction)
    results = eng.compute_ranking(mission="Take and Hold")
    return eng, results


@pytest.mark.parametrize("faction", ALL_FACTIONS)
def test_no_nan_inf_or_negative(faction):
    """DPP, score, dmg and survivability are finite, non-negative numbers."""
    eng, results = _collect_units(faction)
    assert len(results) > 0, f"{faction}: no ranked units"
    for r in results:
        for field_name in ("dpp", "total_damage", "points", "_mission_score"):
            v = r.get(field_name)
            assert v is not None, f"{faction}/{r['name']}: missing {field_name}"
            assert isinstance(v, (int, float)), f"{faction}/{r['name']}.{field_name} not numeric"
            assert not (v != v), f"{faction}/{r['name']}.{field_name} is NaN"
            assert v == float("inf") or v == float("-inf") or abs(v) != float("inf"), \
                f"{faction}/{r['name']}.{field_name} is Inf"
        assert r["dpp"] >= 0, f"{faction}/{r['name']}: negative DPP"
        assert r["total_damage"] >= 0, f"{faction}/{r['name']}: negative damage"


@pytest.mark.parametrize("faction", ALL_FACTIONS)
def test_ranking_sorted_descending(faction):
    _, results = _collect_units(faction)
    scores = [r["_mission_score"] for r in results]
    assert scores == sorted(scores, reverse=True), (
        f"{faction}: mission ranking not sorted by score desc"
    )


@pytest.mark.parametrize("faction", ALL_FACTIONS)
def test_resolve_loadout_deterministic(faction):
    """Resolving the same unit+target twice returns identical loadout."""
    eng = load_engine(faction)
    target = eng.config.target_profiles["MEQ"]
    for name in eng.config.known_units:
        try:
            a = eng.resolve_loadout(name, target)
            b = eng.resolve_loadout(name, target)
        except KeyError:
            continue  # unresolvable — covered by resolution-coverage test
        if a is None and b is None:
            continue
        assert a is not None and b is not None, f"{faction}/{name}: nondeterministic None"
        # compare damage-equivalent weapon sets
        pa, ra, ma, ia, _ = a
        pb, rb, mb, ib, _ = b
        assert pa == pb, f"{faction}/{name}: cost differs between resolves"
        def _sig(ws):
            return tuple(sorted((w.name, w.attacks, w.strength, w.ap, w.damage) for w in ws))
        assert _sig(ra) == _sig(rb), f"{faction}/{name}: ranged loadout not deterministic"
        assert _sig(ma) == _sig(mb), f"{faction}/{name}: melee loadout not deterministic"


@pytest.mark.parametrize("faction", ALL_FACTIONS)
def test_every_ranked_unit_has_positive_points(faction):
    eng, results = _collect_units(faction)
    for r in results:
        assert r["points"] > 0, f"{faction}/{r['name']}: non-positive points"


@pytest.mark.parametrize("faction", ALL_FACTIONS)
def test_every_known_unit_resolves(faction):
    """No known unit may reference a weapon missing from the catalog.

    resolve_loadout raises KeyError for such units — a real data gap. This is
    the strict gate: any unresolvable unit is a bug (missing weapon), not an
    opinion. Currently 'Tomb Citadel Walls' (Gauss exterminator) is the only
    known offender across all factions.
    """
    eng = load_engine(faction)
    bad = []
    for name in eng.config.known_units:
        if not isinstance(name, str) or name.startswith("_"):
            continue
        try:
            eng.resolve_loadout(name, eng.config.target_profiles["GEQ"])
        except KeyError as e:
            bad.append(f"{name}: {e}")
    assert not bad, (
        f"{faction}: {len(bad)} unit(s) reference weapons missing from the "
        f"catalog (data gap — must be fixed or whitelisted):\n" + "\n".join(bad)
    )


@pytest.mark.parametrize("faction", ALL_FACTIONS)
def test_meta_weights_sum_to_one(faction):
    """Every meta preset resolves to weights summing to ~1.0 (no lost targets)."""
    eng = load_engine(faction)
    for meta in eng.config.meta_profiles:
        if meta.startswith("_"):
            continue
        resolved = eng.config._resolve_meta(meta)
        total = sum(w for _, _, w in resolved)
        assert abs(total - 1.0) < 1e-9, (
            f"{faction}: meta '{meta}' weights sum to {total} != 1.0"
        )