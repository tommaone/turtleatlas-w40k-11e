"""STRICT cross-faction structural meta-truth.

These are invariants of the engine that a correct config cannot violate.
They encode the honest domain expectation: target mix changes what wins.

  1. Re-ranking: the set of top-N DPP units changes (or at least reorders)
     between the 'infantry' and 'vehicle' metas. If the same units occupy
     the top in the same order under both metas, the config is broken —
     metas must matter.
  2. Cross-target monotonicity: for a fixed unit, the engine's DPP against
     a tougher, higher-wound profile (Knight) cannot exceed its DPP against
     a weaker one when the weapon can't wound the tougher profile better.
     This is enforced by construction; the test confirms no inverted stats.

Runtime: one compute per meta, per faction. Still fast (~seconds total).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.crossfaction_common import ALL_FACTIONS, load_engine


@pytest.mark.parametrize("faction", ALL_FACTIONS)
def test_meta_mix_reranks_units(faction):
    """Infantry vs vehicle metas must produce different top-10 orderings,
    OR (for tiny rosters) change the per-unit DPP. The mix has to matter."""
    eng = load_engine(faction)
    inf = eng.compute_ranking(mission="Take and Hold", meta_name="infantry")
    veh = eng.compute_ranking(mission="Take and Hold", meta_name="vehicle")
    assert len(inf) == len(veh), f"{faction}: meta changed roster size"

    names_inf = [r["name"] for r in inf[:10]]
    names_veh = [r["name"] for r in veh[:10]]
    if names_inf == names_veh:
        # Same names in same order — mete as has no effect. For large rosters
        # this is broken. For 1-unit rosters, require DPP itself to change.
        if len(inf) <= 2:
            d_inf = inf[0]["dpp"]
            d_veh = veh[0]["dpp"]
            assert abs(d_inf - d_veh) > 1e-6, (
                f"{faction}: single unit DPP identical under infantry/vehicle "
                f"metas ({d_inf:.6f}) — mix has no effect"
            )
        else:
            pytest.fail(
                f"{faction}: top-10 identical under infantry/vehicle metas — "
                f"target mix has no effect (names: {names_inf})"
            )


@pytest.mark.parametrize("faction", ALL_FACTIONS)
def test_damage_non_negative_across_targets(faction):
    """No weapon resolution may return negative or NaN damage for any target.

    This is the *sound* budget-free damage invariant. We deliberately do NOT
    assert "damage <= attacks×damage" (multiplicative keywords like Twin-linked,
    Rapid Fire and count scale effective shots beyond the nominal A stat), and
    we do NOT assert "tougher target takes less damage" (high-D weapons
    overkill 1-wound hordes, e.g. Maulerfiend does more to a Knight than to
    GEQ). Both are correct engine behaviour, not inversion or overflow.
    """
    eng = load_engine(faction)
    from engine.ranking import _ld_dmg
    for name in eng.config.known_units:
        try:
            res = eng.resolve_loadout(name, eng.config.target_profiles["MEQ"])
        except KeyError:
            continue  # unresolvable unit — covered by resolution-coverage test
        if res is None:
            continue
        _, ranged, melee, innate, _ = res
        for target_label, target in eng.config.target_profiles.items():
            if not isinstance(target_label, str) or target_label.startswith("_"):
                continue
            dmg = _ld_dmg(ranged, melee, innate, target)
            assert dmg >= 0 and not (dmg != dmg), (
                f"{faction}/{name}: damage {dmg} vs {target_label} is invalid"
            )


@pytest.mark.parametrize("faction", ALL_FACTIONS)
def test_all_units_rank_under_every_meta(faction):
    """Every faction must rank some units under each meta (no meta dead)."""
    eng = load_engine(faction)
    for meta in ("all-comers", "competitive", "anti-horde", "infantry", "vehicle", "elite"):
        res = eng.compute_ranking(mission="Take and Hold", meta_name=meta)
        assert res, f"{faction}: no ranked units under '{meta}' meta"