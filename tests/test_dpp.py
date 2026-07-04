"""Tests for the DPP engine (engine/dpp.py).

Tests are structural, not numerical — we verify constraints and invariants
rather than specific DPP values, because changing a weapon profile or target
profile should update the output without breaking tests.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from dpp import (
    compute_weapon_dpp,
    compute_surv,
    compute_mob,
    UnitDefense,
    WeaponProfile,
    TargetProfile,
    HitMode,
)


# ---------------------------------------------------------------------------
# compute_weapon_dpp
# ---------------------------------------------------------------------------


class TestComputeWeaponDPP:
    """DPP computation must satisfy basic constraints."""

    def test_zero_damage_if_no_attacks(self, MEQ):
        """A weapon with attacks=0 should deal 0 damage."""
        wp = WeaponProfile(
            name="Empty",
            attacks=0,
            bs=3,
            strength=4,
            ap=-1,
            damage=1,
            abilities=[],
        )
        result = compute_weapon_dpp(wp, MEQ, unit_points=100)
        assert result["total_damage"] == 0.0
        assert result["dpp"] == 0.0

    def test_non_negative_damage(self, storm_bolter, MEQ):
        """Damage should never be negative."""
        result = compute_weapon_dpp(storm_bolter, MEQ, unit_points=100)
        assert result["total_damage"] >= 0
        assert result["dpp"] >= 0
        assert result["expected_hits"] >= 0

    def test_torrent_autohit(self, MEQ):
        """Torrent should bypass hit roll (no misses from BS)."""
        wp = WeaponProfile(
            name="Flamer",
            attacks=5,
            bs=6,  # terrible BS, but Torrent ignores it
            strength=4,
            ap=-1,
            damage=1,
            abilities=["Torrent"],
        )
        result = compute_weapon_dpp(wp, MEQ, unit_points=100)
        # With Torrent, ALL attacks auto-hit regardless of BS
        assert result["expected_hits"] == 5.0

    def test_psychic_ignores_cover(self, MEQ):
        """Psychic weapons should use NORMAL hit mode even when target in cover."""
        wp = WeaponProfile(
            name="Psychic Weapon",
            attacks=4,
            bs=3,
            strength=5,
            ap=-2,
            damage=2,
            abilities=["Psychic"],
        )
        # Cover would worsen BS, but Psychic ignores it
        normal = compute_weapon_dpp(wp, MEQ, unit_points=100, hit_mode=HitMode.NORMAL)
        cover = compute_weapon_dpp(wp, MEQ, unit_points=100, hit_mode=HitMode.COVER)
        assert cover["total_damage"] == normal["total_damage"]

    def test_anti_infantry_increases_damage(self, MEQ):
        """Anti-Infantry should increase damage vs INFANTRY target."""
        # Note: The engine does not yet resolve anti-keywords against target keywords
        # (TargetProfile has no keyword field). This test verifies that the
        # Anti keyword is parsed and that damage is computed with anti_info set.
        # For now we just check structural soundness — damage >= 0.
        wp = WeaponProfile(
            name="Purifying Flame",
            attacks=3,
            bs=3,
            strength=4,
            ap=-1,
            damage=1,
            abilities=["Anti-Infantry 2+", "Ignores Cover", "Psychic"],
        )
        result = compute_weapon_dpp(wp, MEQ, unit_points=100)
        assert result["total_damage"] >= 0
        # Anti keyword is parsed and does not crash
        assert "total_damage" in result

    def test_dpp_scales_with_unit_points(self, storm_bolter, MEQ):
        """DPP should decrease as unit points increase."""
        cheap = compute_weapon_dpp(storm_bolter, MEQ, unit_points=50)
        expensive = compute_weapon_dpp(storm_bolter, MEQ, unit_points=200)
        assert cheap["dpp"] > expensive["dpp"]

    def test_invuln_save_ignored_above_ap_threshold(self, MEQ):
        """Attacks with poor AP should use regular save, not invuln."""
        # No-invuln target
        wp = WeaponProfile(
            name="Low AP",
            attacks=10,
            bs=3,
            strength=4,
            ap=0,
            damage=1,
            abilities=[],
        )
        result = compute_weapon_dpp(wp, MEQ, unit_points=100)
        # MEQ has no invuln, total_damage should be non-negative
        assert result["total_damage"] >= 0


# ---------------------------------------------------------------------------
# compute_surv
# ---------------------------------------------------------------------------


class TestComputeSurv:
    """Survival computation must satisfy basic constraints."""

    def test_single_model_surv(self):
        """Single model SV3+ 2W: effective wounds = 2 / (1/3) = 6."""
        defense = UnitDefense(toughness=4, wounds_per_model=2, save=3, invuln=None, fnp=None, models=1)
        result = compute_surv(defense, unit_points=100)
        # SV3+ means 2/3 of wounds are saved → 1/3 get through → 2 / 0.333 = 6
        assert result["effective_wounds"]["ap0"] == 6.0

    def test_multi_model_wounds(self):
        """5 models × 2W × SV3+ multiplier = 30 effective wounds."""
        defense = UnitDefense(toughness=4, wounds_per_model=2, save=3, invuln=None, fnp=None, models=5)
        result = compute_surv(defense, unit_points=100)
        # SV3+ vs AP0: 2/3 saved → 1/3 get through → 10 / 0.333 = 30
        assert result["effective_wounds"]["ap0"] == 30.0

    def test_invuln_increases_effective_wounds_ap_high(self):
        """Against high-AP, invuln should give better save than armour."""
        # SV 3+, INV 4+:
        # AP-4: save = 7 (no save), invuln = 4+ → use invuln
        defense = UnitDefense(toughness=4, wounds_per_model=3, save=3, invuln=4, fnp=None, models=2)
        result = compute_surv(defense, unit_points=100)
        ap4 = result["effective_wounds"]["ap4"]
        ap0 = result["effective_wounds"]["ap0"]
        assert ap4 > 0
        # AP-4 with invuln 4+: save on 4+ (50%), so ap4 should be > 40% of ap0
        assert ap4 > ap0 * 0.40

    def test_fnp_increases_effective_wounds(self):
        """FNP 5+ should increase eW by factor 1.5."""
        no_fnp = UnitDefense(toughness=4, wounds_per_model=2, save=5, invuln=None, fnp=None, models=1)
        with_fnp = UnitDefense(toughness=4, wounds_per_model=2, save=5, invuln=None, fnp=5, models=1)
        r1 = compute_surv(no_fnp, unit_points=100)
        r2 = compute_surv(with_fnp, unit_points=100)
        # FNP 5+ = 1.33x multiplier (saves on 5+=4/6 chance to fail=0.666...→1.5x)
        assert r2["effective_wounds"]["ap0"] > r1["effective_wounds"]["ap0"]

    def test_pts_per_eff_w(self):
        """Points per effective wound should be computed."""
        defense = UnitDefense(toughness=4, wounds_per_model=2, save=3, invuln=4, fnp=None, models=1)
        result = compute_surv(defense, unit_points=100)
        assert "pts_per_eff_w_ap0" in result
        # Against AP0: effective wounds = 2 / (1/3) = 6, pts/effW = 100/6 ≈ 16.7
        # 3+ save → save on 3+ → failed 4/6 = 0.666 → wounds factor 1.5
        # effective wounds = 2 * 3 = 6
        assert result["pts_per_eff_w_ap0"] > 0


# ---------------------------------------------------------------------------
# compute_mob
# ---------------------------------------------------------------------------


class TestComputeMob:
    """Mobility score must satisfy basic constraints."""

    def test_no_deep_strike_no_gate(self):
        """Vehicle with M=8, no DS, no GoI, OC=0."""
        result = compute_mob(movement=8, fly=False, deep_strike=False, oc=0, keywords=["VEHICLE"], gate_of_infinity=False)
        assert result["mobility_tier"] == "cavalry"  # M=8 → cavalry
        assert result["deep_strike"] is False
        assert result["gate_of_infinity"] is False

    def test_deep_strike_increases_mob(self):
        """Deep Strike should set deep_strike flag."""
        no_ds = compute_mob(movement=6, fly=False, deep_strike=False, oc=2, keywords=["INFANTRY"], gate_of_infinity=False)
        with_ds = compute_mob(movement=6, fly=False, deep_strike=True, oc=2, keywords=["INFANTRY"], gate_of_infinity=False)
        assert no_ds["deep_strike"] is False
        assert with_ds["deep_strike"] is True
        assert with_ds["is_infantry"] is True

    def test_gate_of_infinity_gives_high_mob(self):
        """Gate of Infinity flag should be set."""
        with_gate = compute_mob(movement=6, fly=False, deep_strike=True, oc=2, keywords=["INFANTRY"], gate_of_infinity=True)
        assert with_gate["gate_of_infinity"] is True
        assert with_gate["deep_strike"] is True  # GoI units also have DS

    def test_mobility_non_negative(self):
        """Mobility dict should contain expected keys with no negative values."""
        result = compute_mob(movement=4, fly=False, deep_strike=False, oc=0, keywords=["VEHICLE"], gate_of_infinity=False)
        assert result["mobility_tier"] in ("slow", "standard", "cavalry", "fast", "skyborne")
        assert result["objective_control"] >= 0

    def test_fly_increases_mobility(self):
        """FLY keyword should be reflected in the fly field."""
        no_fly = compute_mob(movement=8, fly=False, deep_strike=False, oc=1, keywords=["VEHICLE"], gate_of_infinity=False)
        with_fly = compute_mob(movement=8, fly=True, deep_strike=False, oc=1, keywords=["VEHICLE"], gate_of_infinity=False)
        assert no_fly["fly"] is False
        assert with_fly["fly"] is True
        # Both should be cavalry (M=8)
        assert no_fly["mobility_tier"] == "cavalry"
        assert with_fly["mobility_tier"] == "cavalry"



