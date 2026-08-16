"""Engine integration locks for conditional damage-boost (Rend and Tear class).

Pipeline tests: the engine is the single source of computation. These tests
assert the FEATURE CONTRACT (a +1-damage boost adds +1 per unsaved wound vs
matching targets, and nothing vs non-matching targets) and lock the World
Eaters Exalted Eightbound vehicle-meta result (total_damage 9.71 / dpp
0.0747 — values produced by the engine, verified 2026-08-16).

Run: python3 -m pytest tests/test_damage_boost.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.dpp import WeaponProfile, compute_weapon_dpp

BOOST = {"amount": 1, "targets": ["MONSTER", "VEHICLE"]}


@pytest.fixture
def chainblades():
    """Exalted Eightbound Chainblades (D2, S8, AP-3, A4 WS3+)."""
    return WeaponProfile(
        name="Chainblades", attacks=4, bs=3, strength=8, ap=-3,
        damage=2, abilities=[],
    )


class TestWeaponLevelContract:
    """The boost must apply per-target, before the overkill cap, exactly once."""

    def test_boost_applies_vs_vehicle(self, chainblades, Knight):
        """Knight (T13, W26/model): D2→D3 with no overkill → +50% damage."""
        base = compute_weapon_dpp(chainblades, Knight, unit_points=130)
        boosted = compute_weapon_dpp(chainblades, Knight, unit_points=130,
                                     damage_boost=BOOST)
        assert boosted["total_damage"] > base["total_damage"]
        # 2-decimal rounding on both sides absorbs up to 0.01.
        assert boosted["total_damage"] == pytest.approx(
            base["total_damage"] * 1.5, abs=0.01
        ), "D2→D3 on a non-capped target must be exactly +50%"

    def test_no_boost_vs_infantry(self, chainblades, MEQ):
        """MEQ (T4) is not in the MONSTER/VEHICLE toughness band → identical."""
        base = compute_weapon_dpp(chainblades, MEQ, unit_points=130)
        boosted = compute_weapon_dpp(chainblades, MEQ, unit_points=130,
                                     damage_boost=BOOST)
        assert boosted["total_damage"] == base["total_damage"]

    def test_no_boost_without_spec(self, chainblades, Knight):
        """No damage_boost argument → identical to baseline (no regression)."""
        base = compute_weapon_dpp(chainblades, Knight, unit_points=130)
        assert base["total_damage"] > 0
        assert base["total_damage"] == compute_weapon_dpp(
            chainblades, Knight, unit_points=130, damage_boost=None
        )["total_damage"]

    def test_variant_group_forwards_boost(self, Knight):
        """Dual-profile weapons must forward damage_boost through variants."""
        wp = WeaponProfile(
            name="Samni'arius", attacks=8, bs=2, strength=14, ap=-3,
            damage=6.5, abilities=["Devastating Wounds"], variants=[
                WeaponProfile(name="Spinegrinder (Sweep)", attacks=16, bs=2,
                              strength=7, ap=-2, damage=2,
                              abilities=["Devastating Wounds"], variants=[]),
            ],
        )
        base = compute_weapon_dpp(wp, Knight, unit_points=330)
        boosted = compute_weapon_dpp(wp, Knight, unit_points=330, damage_boost=BOOST)
        # Best profile (strike here) carries the boost; it must change.
        assert boosted["total_damage"] > base["total_damage"]


class TestExaltedEightboundRanking:
    """End-to-end: World Eaters Exalted Eightbound vs vehicle meta.

    Pre-change: total_damage 6.47 / dpp 0.0498 (rank 9/29 Purge the Foe).
    Post-change (Rend and Tear modeled): 9.71 / 0.0747 (rank ~3rd, behind
    Forgefiend 0.0954 and Chaos Predator Annihilator 0.0882). Values are
    engine output, locked as a drift probe — if the engine improves, this
    pin updates with it.
    """

    def test_vehicle_meta_damage(self):
        from engine.ranking import RankingEngine
        e = RankingEngine("world-eaters")
        r = e.compute_ranking(mission="Purge the Foe", meta_name="vehicle")
        row = next(u for u in r if u.get("name") == "Exalted Eightbound")
        assert row["total_damage"] == pytest.approx(9.71, abs=0.01)
        assert row["dpp"] == pytest.approx(0.0747, abs=0.0001)
        spec = row["damage_boost"]
        assert spec is not None
        assert spec["amount"] == 1
        assert spec["phase"] == "melee"
        assert "MONSTER" in spec["targets"] and "VEHICLE" in spec["targets"]

    def test_rank_improves_over_unboosted(self):
        """The boost must lift Exalted Eightbound's vehicle ranking meaningfully."""
        from engine.ranking import RankingEngine
        e = RankingEngine("world-eaters")
        r = e.compute_ranking(mission="Purge the Foe", meta_name="vehicle")
        row = next(u for u in r if u.get("name") == "Exalted Eightbound")
        ranked = [u["name"] for u in r]
        assert ranked.index("Exalted Eightbound") < 10, (
            f"Rend and Tear should put Exalted Eightbound in the top third "
            f"(got rank {ranked.index('Exalted Eightbound')})"
        )
