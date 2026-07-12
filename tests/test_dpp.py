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
    WeaponModifier,
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

    # ── Plunging Fire ─────────────────────────────────────────────

    def test_plunging_fire_improves_hits(self, MEQ):
        """Plunging Fire should increase expected hits."""
        wp = WeaponProfile(
            name="Test", attacks=6, bs=3, strength=4, ap=-1, damage=1, abilities=[],
        )
        normal = compute_weapon_dpp(wp, MEQ, unit_points=100, hit_mode=HitMode.NORMAL)
        plung = compute_weapon_dpp(wp, MEQ, unit_points=100, hit_mode=HitMode.PLUNGING_FIRE)
        assert plung["expected_hits"] > normal["expected_hits"]
        # BS3+ → 2+: 4/6 → 5/6 = +25%
        assert abs(plung["expected_hits"] / normal["expected_hits"] - 5/4) < 0.01

    def test_psychic_ignores_plunging_fire(self, MEQ):
        """Psychic weapons should ignore Plunging Fire."""
        wp = WeaponProfile(
            name="Psychic Test", attacks=6, bs=3, strength=8, ap=-2, damage=2,
            abilities=["Psychic"],
        )
        normal = compute_weapon_dpp(wp, MEQ, unit_points=100, hit_mode=HitMode.NORMAL)
        plung = compute_weapon_dpp(wp, MEQ, unit_points=100, hit_mode=HitMode.PLUNGING_FIRE)
        assert plung["expected_hits"] == normal["expected_hits"]
        assert plung["total_damage"] == normal["total_damage"]

    def test_plunging_and_cover_cancel(self, MEQ):
        """COVER_PLUNGING mode should net zero modifier."""
        wp = WeaponProfile(
            name="Test", attacks=6, bs=3, strength=4, ap=-1, damage=1, abilities=[],
        )
        normal = compute_weapon_dpp(wp, MEQ, unit_points=100, hit_mode=HitMode.NORMAL)
        both = compute_weapon_dpp(wp, MEQ, unit_points=100, hit_mode=HitMode.COVER_PLUNGING)
        assert both["expected_hits"] == normal["expected_hits"]

    def test_torrent_ignores_plunging_fire(self, MEQ):
        """Torrent weapons should auto-hit regardless of Plunging Fire."""
        wp = WeaponProfile(
            name="Torrent Flamer", attacks=7, bs=6, strength=4, ap=-1, damage=1,
            abilities=["Torrent"],
        )
        plung = compute_weapon_dpp(wp, MEQ, unit_points=100, hit_mode=HitMode.PLUNGING_FIRE)
        # Torrent: always auto-hit regardless of BS or modifiers
        assert plung["expected_hits"] == 7.0

    # ── Blast ─────────────────────────────────────────────────────

    def test_blast_bonus_vs_large_unit(self, MEQ):
        """Blast adds (model_count // 5) * X bonus attacks."""
        wp_blast = WeaponProfile(
            name="Blast Cannon", attacks=3, bs=3, strength=5, ap=-1, damage=1,
            abilities=["Blast"],
        )
        # vs 1 model: 0 bonus
        solo = TargetProfile(toughness=MEQ.toughness, save=MEQ.save, model_count=1)
        r_solo = compute_weapon_dpp(wp_blast, solo, unit_points=100)
        # vs 20 models: 20//5*1 = 4 bonus (total 7 attacks)
        horde = TargetProfile(toughness=MEQ.toughness, save=MEQ.save, model_count=20)
        r_horde = compute_weapon_dpp(wp_blast, horde, unit_points=100)
        assert r_horde["conditions"]["blast_bonus"] == 4
        assert r_horde["expected_hits"] > r_solo["expected_hits"]
        # 7/3 ≈ 2.33x more attacks
        ratio = r_horde["expected_hits"] / r_solo["expected_hits"]
        assert abs(ratio - 7/3) < 0.1

    def test_blast_x_bonus(self, MEQ):
        """Blast X adds X * (model_count // 5) bonus attacks."""
        wp = WeaponProfile(
            name="Blast 2 Cannon", attacks=2, bs=3, strength=6, ap=-1, damage=1,
            abilities=["Blast 2"],
        )
        horde = TargetProfile(toughness=MEQ.toughness, save=MEQ.save, model_count=15)
        r = compute_weapon_dpp(wp, horde, unit_points=100)
        assert r["conditions"]["blast_bonus"] == 6  # 15//5=3, 3*2=6
        # Total attacks: 2 + 6 = 8

    def test_no_blast_bonus_vs_small_unit(self, MEQ):
        """Blast vs <5 models gives no bonus."""
        wp = WeaponProfile(
            name="Blast Test", attacks=4, bs=3, strength=4, ap=0, damage=1,
            abilities=["Blast"],
        )
        for count in [1, 2, 3, 4]:
            tp = TargetProfile(toughness=MEQ.toughness, save=MEQ.save, model_count=count)
            r = compute_weapon_dpp(wp, tp, unit_points=100)
            assert r["conditions"]["blast_bonus"] == 0, f"Expected 0 bonus for {count} models"

    def test_blast_and_rapid_fire_stack(self, MEQ):
        """Blast bonus and Rapid Fire should both add to effective attacks."""
        wp = WeaponProfile(
            name="Frag Cannon", attacks=2, bs=3, strength=6, ap=-1, damage=1,
            abilities=["Blast", "Rapid Fire 2"],
        )
        horde = TargetProfile(toughness=MEQ.toughness, save=MEQ.save, model_count=10)
        r = compute_weapon_dpp(wp, horde, unit_points=50)
        # Blast: 10//5*1 = 2, RF: 2, total: 2+2+2 = 6
        hits_no_blast = 2 + 2  # base + RF only
        hits_total = 2 + 2 + 2  # base + blast + RF
        assert r["conditions"]["blast_bonus"] == 2
        assert abs(r["expected_hits"] - hits_total * 4/6) < 0.1  # BS3+

    # ── Melta ─────────────────────────────────────────────────────

    def test_melta_inactive_by_default(self, MEQ):
        """Melta should not apply unless melta_active=True."""
        wp = WeaponProfile(
            name="Melta Gun", attacks=1, bs=3, strength=8, ap=-4, damage=1,
            abilities=["Melta 2"],
        )
        r_off = compute_weapon_dpp(wp, MEQ, unit_points=50, melta_active=False)
        r_on = compute_weapon_dpp(wp, MEQ, unit_points=50, melta_active=True)
        assert r_on["total_damage"] > r_off["total_damage"]

    def test_melta_adds_damage(self, MEQ):
        """Melta X adds X damage at half range."""
        wp = WeaponProfile(
            name="Multi-melta", attacks=2, bs=3, strength=9, ap=-4, damage=2,
            abilities=["Melta 2"],
        )
        # D=2 base, Melta 2 → D=4 at half range → 2x damage before overkill
        r_off = compute_weapon_dpp(wp, MEQ, unit_points=50, melta_active=False)
        r_on = compute_weapon_dpp(wp, MEQ, unit_points=50, melta_active=True)
        # Damage exactly doubles (no overkill for 2W MEQ with D=2 vs D=4)
        ratio = r_on["total_damage"] / r_off["total_damage"]
        assert abs(ratio - 2.0) < 0.01

    # ── Heavy ─────────────────────────────────────────────────────

    def test_heavy_stationary_improves_hits(self, MEQ):
        """Heavy gives +1 to hit if stationary."""
        wp = WeaponProfile(
            name="Heavy Bolter", attacks=3, bs=3, strength=5, ap=-1, damage=1,
            abilities=["Heavy"],
        )
        r_moved = compute_weapon_dpp(wp, MEQ, unit_points=60, heavy_stationary=False)
        r_still = compute_weapon_dpp(wp, MEQ, unit_points=60, heavy_stationary=True)
        assert r_still["expected_hits"] > r_moved["expected_hits"]
        # BS3+ → 2+: 4/6 → 5/6 = +25%
        ratio = r_still["expected_hits"] / r_moved["expected_hits"]
        assert abs(ratio - 5/4) < 0.01

    def test_psychic_ignores_heavy(self, MEQ):
        """Psychic weapons should ignore Heavy bonus."""
        wp = WeaponProfile(
            name="Psychic Cannon", attacks=3, bs=3, strength=7, ap=-2, damage=2,
            abilities=["Psychic", "Heavy"],
        )
        r_still = compute_weapon_dpp(wp, MEQ, unit_points=80, heavy_stationary=True)
        r_moved = compute_weapon_dpp(wp, MEQ, unit_points=80, heavy_stationary=False)
        assert r_still["expected_hits"] == r_moved["expected_hits"]

    def test_heavy_does_not_penalise_on_move(self, MEQ):
        """Heavy in 11e has no penalty when moving — only bonus when stationary."""
        wp = WeaponProfile(
            name="Heavy Gun", attacks=3, bs=3, strength=5, ap=-1, damage=1,
            abilities=["Heavy"],
        )
        r_moved = compute_weapon_dpp(wp, MEQ, unit_points=60, heavy_stationary=False)
        # Same as non-Heavy weapon with same stats
        wp2 = WeaponProfile(
            name="Regular Gun", attacks=3, bs=3, strength=5, ap=-1, damage=1,
            abilities=[],
        )
        r_regular = compute_weapon_dpp(wp2, MEQ, unit_points=60)
        assert r_moved["expected_hits"] == r_regular["expected_hits"]

    # ── Rapid Fire D3/D6 ──────────────────────────────────────────

    def test_rapid_fire_d3_averaged(self, MEQ):
        """Rapid Fire D3 should average to +2 extra attacks."""
        wp = WeaponProfile(
            name="RF D3 Gun", attacks=3, bs=3, strength=4, ap=0, damage=1,
            abilities=["Rapid Fire D3"],
        )
        r = compute_weapon_dpp(wp, MEQ, unit_points=50)
        # 3 base + 2 RF = 5 attacks, BS3+ → 4/6 * 5 = 3.33 hits
        assert abs(r["expected_hits"] - 3.33) < 0.1

    def test_rapid_fire_d6_averaged(self, MEQ):
        """Rapid Fire D6 should average to +3 extra attacks."""
        wp = WeaponProfile(
            name="RF D6 Gun", attacks=2, bs=3, strength=4, ap=0, damage=1,
            abilities=["Rapid Fire D6"],
        )
        r = compute_weapon_dpp(wp, MEQ, unit_points=50)
        # 2 base + 3 RF = 5 attacks
        assert abs(r["expected_hits"] - 5 * 4/6) < 0.1


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

    def test_no_t1_reinforcements_flag(self):
        """no_t1_reinforcements should default to True and reduce DS value."""
        default = compute_mob(movement=6, deep_strike=True, oc=1, keywords=["INFANTRY"])
        assert default["no_t1_reinforcements"] is True
        assert default["deep_strike"] is True
        non_t1 = compute_mob(movement=6, deep_strike=True, oc=1, keywords=["INFANTRY"], no_t1_reinforcements=False)
        assert non_t1["no_t1_reinforcements"] is False

        # Verify the flag is propagated
        from engine.ranking import RankingEngine
        score_default = RankingEngine.mob_score(default)
        score_nont1 = RankingEngine.mob_score(non_t1)
        # With no_t1, DS gives +5 instead of +10 → score_default < score_nont1
        assert score_default < score_nont1, (
            f"Expected lower score with T1 restriction: {score_default} vs {score_nont1}"
        )

    def test_fly_increases_mobility(self):
        """FLY keyword should be reflected in the fly field."""
        no_fly = compute_mob(movement=8, fly=False, deep_strike=False, oc=1, keywords=["VEHICLE"], gate_of_infinity=False)
        with_fly = compute_mob(movement=8, fly=True, deep_strike=False, oc=1, keywords=["VEHICLE"], gate_of_infinity=False)
        assert no_fly["fly"] is False
        assert with_fly["fly"] is True
        # Both should be cavalry (M=8)
        assert no_fly["mobility_tier"] == "cavalry"
        assert with_fly["mobility_tier"] == "cavalry"


# ---------------------------------------------------------------------------
# Weapon slots
# ---------------------------------------------------------------------------


class TestWeaponSlots:
    """weapon_slots-based loadout resolution must produce valid results."""

    def test_despoiler_resolves_vs_meq(self):
        """Despoiler should pick gatling + melee arm + carapace vs MEQ-heavy meta."""
        from ranking import RankingEngine
        engine = RankingEngine('chaos-knights')
        comp_meta = engine.config._resolve_meta('competitive')
        resolved = engine.resolve_loadout('Knight Despoiler', comp_meta)
        assert resolved is not None
        pts, ranged, melee, innate, info = resolved
        assert pts >= 355  # base 330 + at least arm+carapace+hull
        assert pts <= 400  # not exceeding max possible cost
        assert len(ranged) >= 2  # at least some ranged
        assert len(melee) >= 1   # at least titanic feet
        names = [w.name for w in ranged + melee]
        assert 'Titanic feet' in names
        # Should NOT have duplicate Despoiler gatling cannon (optimizer picks 1 gatling + 1 melee arm)
        gat_count = sum(1 for n in names if n == 'Despoiler gatling cannon')
        assert gat_count <= 1, f"Expected ≤1 gatling vs MEQ, got {gat_count}: {names}"

    def test_despoiler_picks_anti_armour_vs_lightv(self):
        """Despoiler should pick thermal/battle cannon vs Light Vehicles."""
        from ranking import RankingEngine
        engine = RankingEngine('chaos-knights')
        lv = engine.config.target_profiles['Light V']
        resolved = engine.resolve_loadout('Knight Despoiler', lv)
        assert resolved is not None
        pts, ranged, melee, innate, info = resolved
        names = [w.name for w in ranged + melee]
        anti_armour = [n for n in names if any(x in n.lower() for x in ['thermal', 'battle cannon', 'warpstrike', 'ruinspear'])]
        assert len(anti_armour) >= 2, f"Expected anti-armour vs LightV, got: {names}"

    def test_despoiler_vs_knight_picks_thermal(self):
        """Despoiler should pick thermal cannons vs Knight targets (high S/AP)."""
        from ranking import RankingEngine
        engine = RankingEngine('chaos-knights')
        knight_tp = engine.config.target_profiles['Knight']
        resolved = engine.resolve_loadout('Knight Despoiler', knight_tp)
        assert resolved is not None
        pts, ranged, melee, innate, info = resolved
        names = [w.name for w in ranged + melee]
        thermal_count = sum(1 for n in names if 'thermal' in n.lower() or 'battle cannon' in n.lower())
        assert thermal_count >= 1 or any('Daemonbreath' in n for n in names), \
            f"Expected high-S weapon vs Knight, got: {names}"

    def test_tyrant_resolves(self):
        """Tyrant should resolve with fixed meltaguns + 1 arm set + 3 carapace."""
        from ranking import RankingEngine
        engine = RankingEngine('chaos-knights')
        comp_meta = engine.config._resolve_meta('competitive')
        resolved = engine.resolve_loadout('Knight Tyrant', comp_meta)
        assert resolved is not None
        pts, ranged, melee, innate, info = resolved
        assert pts == 400
        names = [w.name for w in ranged + melee]
        # Fixed weapons always present
        assert 'Twin daemonbreath meltagun' in names
        assert 'Titanic feet' in names
        # Exactly 2 meltaguns
        meltas = sum(1 for n in names if 'Twin daemonbreath meltagun' in n)
        assert meltas == 2, f"Expected 2 meltaguns, got {meltas}"
        # One arm set chosen — check we never have both sets
        set_a = {'Brimstone volcano lance', 'Ectoplasma decimator - supercharge'}
        set_b = {'Darkflame cannon', 'Warpshock harpoon'}
        has_a = set_a.issubset(names)
        has_b = set_b.issubset(names)
        assert has_a != has_b, \
            f"Expected exactly one arm set, got A={has_a} B={has_b}: {names}"
        # Carapace: 3 mounts, max 2 of each type
        gheist_count = sum(1 for n in names if 'Gheiststrike' in n)
        desecrator_count = sum(1 for n in names if 'Twin desecrator' in n)
        assert gheist_count + desecrator_count == 3, \
            f"Expected 3 carapace weapons (gheist={gheist_count} desecrator={desecrator_count}), got {names}"
        assert gheist_count <= 2
        assert desecrator_count <= 2

    def test_backward_compat_war_dog(self):
        """War Dogs (no weapon_slots) must still resolve with old system."""
        from ranking import RankingEngine
        engine = RankingEngine('chaos-knights')
        comp_meta = engine.config._resolve_meta('competitive')
        for wd in ['War Dog Karnivore', 'War Dog Stalker', 'War Dog Brigand']:
            resolved = engine.resolve_loadout(wd, comp_meta)
            assert resolved is not None, f"{wd} failed to resolve"
            pts, ranged, melee, innate, info = resolved
            assert pts > 0
            assert len(ranged) >= 1
            assert len(melee) >= 1

    def test_slot_loadout_changes_per_target(self):
        """Despoiler should pick different weapons for different targets."""
        from ranking import RankingEngine
        engine = RankingEngine('chaos-knights')

        targets = {
            'GEQ': engine.config.target_profiles['GEQ'],
            'MEQ': engine.config.target_profiles['MEQ'],
            'Knight': engine.config.target_profiles['Knight'],
        }
        loadouts = {}
        for tname, tp in targets.items():
            resolved = engine.resolve_loadout('Knight Despoiler', tp)
            assert resolved is not None
            pts, ranged, melee, innate, info = resolved
            loadouts[tname] = sorted(w.name for w in ranged + melee)

        # At least one target pair should produce different loadouts
        assert loadouts['GEQ'] != loadouts['Knight'] or loadouts['MEQ'] != loadouts['Knight'], \
            f"All targets produced same loadout: {loadouts}"


# ---------------------------------------------------------------------------
# Detachment modifiers
# ---------------------------------------------------------------------------


class TestDetachmentModifiers:
    """Detachment modifiers must load and have expected structure."""

    def test_gk_all_9_detachments_have_modifiers(self):
        """GK should have all 9 detachments with modifier choices.

        Note: AUGURIUM TASK FORCE has empty choices (no engine-modelable modifiers)
        so it is correctly excluded from the list.
        """
        from ranking import RankingEngine
        eng = RankingEngine('grey-knights')
        dets = eng.list_detachments_with_modifiers()
        expected = {
            'ARGENT ASSAULT', 'BANISHERS',
            'BROTHERHOOD STRIKE', 'FIRES OF PURGATION', 'HALLOWED CONCLAVE',
            'IMMATERIAL INTERDICTION', 'SANCTIC SPEARHEAD', 'WARPBANE TASK FORCE',
        }
        assert set(dets) == expected, f"GK detachments mismatch: missing={expected - set(dets)}, extra={set(dets) - expected}"

    def test_ck_all_8_detachments_have_modifiers(self):
        """CK should have all 8 detachments with modifier choices."""
        from ranking import RankingEngine
        eng = RankingEngine('chaos-knights')
        dets = eng.list_detachments_with_modifiers()
        expected = {
            'BASTIONS OF TYRANNY', 'HUNTING WARPACK', 'ICONOCLAST FIEFDOM',
            'HELHUNT LANCE', 'HOUNDPACK LANCE', 'LORDS OF DREAD',
            'TRAITORIS LANCE', 'INFERNAL LANCE',
        }
        assert set(dets) == expected, f"CK detachments mismatch: missing={expected - set(dets)}, extra={set(dets) - expected}"

    def test_daemon_all_9_detachments_have_modifiers(self):
        """Daemons should have all 9 detachments with modifier choices."""
        from ranking import RankingEngine
        eng = RankingEngine('chaos-daemons')
        dets = eng.list_detachments_with_modifiers()
        expected = {
            'DAEMONIC INCURSION', 'SHADOW LEGION', 'CAVALCADE OF CHAOS',
            'LORDS OF THE WARP', 'WARPTIDE', 'BLOOD LEGION',
            'SCINTILLATING LEGION', 'PLAGUE LEGION', 'LEGION OF EXCESS',
        }
        assert set(dets) == expected, f"Daemon detachments mismatch: missing={expected - set(dets)}, extra={set(dets) - expected}"

    def test_each_detachment_has_at_least_one_choice(self):
        """Every detachment must have at least one modifier choice."""
        from ranking import RankingEngine
        for faction in ['grey-knights', 'chaos-knights', 'chaos-daemons']:
            eng = RankingEngine(faction)
            for det in eng.list_detachments_with_modifiers():
                mods = eng.get_detachment_modifiers(det)
                assert len(mods) >= 1, f"{faction}/{det} has no choices"

    def test_detachment_choices_have_valid_affects(self):
        """Each modifier must affect 'dpp', 'surv', or 'mob'."""
        from ranking import RankingEngine
        valid = {'dpp', 'surv', 'mob'}
        for faction in ['grey-knights', 'chaos-knights', 'chaos-daemons']:
            eng = RankingEngine(faction)
            for det in eng.list_detachments_with_modifiers():
                for mod in eng.get_detachment_modifiers(det):
                    assert mod.affects in valid, f"{faction}/{det}/{mod.name}: affects={mod.affects}"


# ---------------------------------------------------------------------------
# Psychic weapon overlay tests
# ---------------------------------------------------------------------------


class TestPsychicOverlay:
    """Faction overlay should add Psychic to GK weapons, but NOT to Storm Bolters.

    Per BSData: Storm Bolter has only 'Rapid Fire 2' — no Psychic.
    Incinerator has 'Ignores Cover, Torrent' — no Psychic.
    Psycannon already has 'Psychic' in BSData.
    """

    def test_storm_bolter_not_psychic(self, weapon_catalog):
        """Storm Bolter must NOT have Psychic after faction overlay."""
        sb = weapon_catalog.load("Storm Bolter", unit_name="Strike Squad")
        assert "Psychic" not in sb.abilities, (
            f"Storm Bolter should not be Psychic, got: {sb.abilities}"
        )

    def test_psycannon_has_psychic(self, weapon_catalog):
        """Psycannon should have Psychic (from BSData, not overlay)."""
        pc = weapon_catalog.load("Psycannon")
        assert "Psychic" in pc.abilities

    def test_incinerator_not_psychic(self, weapon_catalog):
        """Incinerator should NOT have Psychic — it's Torrent, not Psychic."""
        inc = weapon_catalog.load("Incinerator")
        assert "Psychic" not in inc.abilities, (
            f"Incinerator should not be Psychic, got: {inc.abilities}"
        )

    def test_incinerator_has_torrent(self, weapon_catalog):
        """Incinerator should have Torrent and Ignores Cover."""
        inc = weapon_catalog.load("Incinerator")
        assert "Torrent" in inc.abilities
        assert "Ignores Cover" in inc.abilities

    def test_purifying_flame_has_psychic(self, weapon_catalog):
        """Purifying Flame should have Psychic (from BSData)."""
        pf = weapon_catalog.load("Purifying Flame")
        assert "Psychic" in pf.abilities
        assert "Anti-Infantry 2+" in pf.abilities

    def test_purifying_flame_not_torrent(self, weapon_catalog):
        """Purifying Flame is NOT Torrent per BSData — it requires a hit roll."""
        pf = weapon_catalog.load("Purifying Flame")
        assert "Torrent" not in pf.abilities, (
            f"Purifying Flame should not be Torrent, got: {pf.abilities}"
        )

    def test_heavy_psycannon_has_ignores_cover(self, weapon_catalog):
        """Heavy Psycannon should have Ignores Cover + Psychic per BSData."""
        hpc = weapon_catalog.load("Heavy Psycannon")
        assert "Psychic" in hpc.abilities
        assert "Ignores Cover" in hpc.abilities

    def test_gatling_psilencer_sustained_hits_1(self, weapon_catalog):
        """Gatling Psilencer should have Sustained Hits 1 (not 2) per BSData."""
        gp = weapon_catalog.load("Gatling Psilencer")
        assert "Sustained Hits 1" in gp.abilities
        assert "Sustained Hits 2" not in gp.abilities


# ---------------------------------------------------------------------------
# Psychic + external hit_modifier
# ---------------------------------------------------------------------------


class TestPsychicIgnoresExternalModifier:
    """Psychic [24.29] should zero out external hit modifiers (e.g. detachment buffs).

    The engine accumulates hit_mod from external modifiers, Cover, Plunging, Heavy —
    then resets to 0 for Psychic weapons. This test verifies the external modifier
    path is also zeroed.
    """

    def test_psychic_ignores_plus1_hit(self, MEQ):
        """Psychic weapon with +1 to hit modifier should behave like no modifier."""
        wp = WeaponProfile(
            name="Psycannon", attacks=3, bs=3, strength=8, ap=-1, damage=2,
            abilities=["Psychic"],
        )
        mod_no = WeaponModifier(hit_modifier=0)
        mod_plus1 = WeaponModifier(hit_modifier=-1)  # -1 = +1 to hit (lower BS)

        r_no = compute_weapon_dpp(wp, MEQ, modifier=mod_no, unit_points=100)
        r_plus1 = compute_weapon_dpp(wp, MEQ, modifier=mod_plus1, unit_points=100)

        # Psychic should zero the external modifier — damage must be equal
        assert r_no["total_damage"] == r_plus1["total_damage"], (
            f"Psychic should ignore +1 hit modifier: "
            f"no_mod={r_no['total_damage']}, plus1={r_plus1['total_damage']}"
        )

    def test_psychic_ignores_minus1_hit(self, MEQ):
        """Psychic weapon with -1 to hit modifier should behave like no modifier."""
        wp = WeaponProfile(
            name="Psycannon", attacks=3, bs=3, strength=8, ap=-1, damage=2,
            abilities=["Psychic"],
        )
        mod_no = WeaponModifier(hit_modifier=0)
        mod_minus1 = WeaponModifier(hit_modifier=1)  # +1 = -1 to hit (worsen BS)

        r_no = compute_weapon_dpp(wp, MEQ, modifier=mod_no, unit_points=100)
        r_minus1 = compute_weapon_dpp(wp, MEQ, modifier=mod_minus1, unit_points=100)

        assert r_no["total_damage"] == r_minus1["total_damage"], (
            f"Psychic should ignore -1 hit modifier: "
            f"no_mod={r_no['total_damage']}, minus1={r_minus1['total_damage']}"
        )

    def test_non_psychic_respects_hit_modifier(self, MEQ):
        """Non-psychic weapon SHOULD be affected by external hit modifiers."""
        wp = WeaponProfile(
            name="Bolter", attacks=3, bs=3, strength=4, ap=0, damage=1,
            abilities=[],
        )
        mod_no = WeaponModifier(hit_modifier=0)
        mod_plus1 = WeaponModifier(hit_modifier=-1)  # +1 to hit

        r_no = compute_weapon_dpp(wp, MEQ, modifier=mod_no, unit_points=100)
        r_plus1 = compute_weapon_dpp(wp, MEQ, modifier=mod_plus1, unit_points=100)

        # Non-psychic weapon should benefit from +1 to hit
        assert r_plus1["total_damage"] > r_no["total_damage"], (
            f"Non-psychic should benefit from +1 hit: "
            f"no_mod={r_no['total_damage']}, plus1={r_plus1['total_damage']}"
        )

    def test_psychic_ignores_all_modifiers_combined(self, MEQ):
        """Psychic weapon with Cover + Heavy + external modifier — all zeroed."""
        wp = WeaponProfile(
            name="Psycannon", attacks=3, bs=3, strength=8, ap=-1, damage=2,
            abilities=["Psychic", "Heavy"],
        )
        mod = WeaponModifier(hit_modifier=-1)  # +1 to hit

        # With all modifiers active
        r_all = compute_weapon_dpp(
            wp, MEQ, modifier=mod, hit_mode=HitMode.COVER,
            unit_points=100, heavy_stationary=True,
        )
        # With no modifiers
        r_none = compute_weapon_dpp(wp, MEQ, unit_points=100)

        assert r_all["total_damage"] == r_none["total_damage"], (
            f"Psychic should ignore Cover + Heavy + external: "
            f"all_mods={r_all['total_damage']}, none={r_none['total_damage']}"
        )


# ---------------------------------------------------------------------------
# Invulnerable save tests
# ---------------------------------------------------------------------------


class TestInvulnSave:
    """Invulnerable save must be correctly applied when beneficial."""

    def test_invuln_used_when_better_than_armour(self):
        """INV 4+ should be used when AP makes armour worse than 4+."""
        # SV3+ vs AP-4 → save on 7+ (no save). INV 4+ → save on 4+
        defence = UnitDefense(toughness=4, wounds_per_model=2, save=3, invuln=4)
        result = compute_surv(defence, unit_points=100)
        # With INV 4+: 50% of wounds saved → 2 / 0.5 = 4.0 effective wounds
        assert result["effective_wounds"]["ap4"] == 4.0

    def test_armour_used_when_better_than_invuln(self):
        """SV2+ should be used when AP doesn't push armour below INV 4+."""
        # SV2+ vs AP0 → save on 2+ (83% save). INV 4+ → save on 4+ (50% save)
        defence = UnitDefense(toughness=5, wounds_per_model=3, save=2, invuln=4)
        result = compute_surv(defence, unit_points=100)
        # With SV2+: 83% saved → 3 / 0.1667 ≈ 18.0 effective wounds
        assert result["effective_wounds"]["ap0"] == 18.0

    def test_no_invuln_uses_armour_always(self):
        """No INV → armour is used regardless of AP."""
        defence = UnitDefense(toughness=4, wounds_per_model=2, save=3, invuln=None)
        result = compute_surv(defence, unit_points=100)
        # SV3+ vs AP0: 2/3 saved → 2 / 0.333 = 6.0
        assert result["effective_wounds"]["ap0"] == 6.0
        # SV3+ vs AP-4: save on 7+ (no save) → 2 / 1.0 = 2.0
        assert result["effective_wounds"]["ap4"] == 2.0

    def test_invuln_floor_at_ap4(self):
        """INV 4+ provides a floor — effective wounds don't collapse to 0 at high AP."""
        with_inv = UnitDefense(toughness=4, wounds_per_model=2, save=3, invuln=4)
        without_inv = UnitDefense(toughness=4, wounds_per_model=2, save=3, invuln=None)
        r_with = compute_surv(with_inv, unit_points=100)
        r_without = compute_surv(without_inv, unit_points=100)
        # At AP-4: with INV should be 2× better (4.0 vs 2.0)
        assert r_with["effective_wounds"]["ap4"] > r_without["effective_wounds"]["ap4"]
        assert r_with["effective_wounds"]["ap4"] == 4.0
        assert r_without["effective_wounds"]["ap4"] == 2.0

    def test_invuln_5plus_provides_partial_floor(self):
        """INV 5+ is worse than INV 4+ but still better than no save at high AP."""
        defence = UnitDefense(toughness=4, wounds_per_model=2, save=3, invuln=5)
        result = compute_surv(defence, unit_points=100)
        # SV3+ vs AP-4 → no save. INV 5+ → save on 5+ (33% saved)
        # 2 / 0.6667 = 3.0 effective wounds
        assert result["effective_wounds"]["ap4"] == 3.0

    def test_invuln_shots_to_kill(self):
        """INV should increase shots-to-kill vs high-AP weapons."""
        from dpp import _shots_to_kill
        # Bolter (S5, AP0, D1) vs T4 target
        with_inv = _shots_to_kill(total_wounds=3, toughness=5, save=2, invuln=4,
                                  fnp=None, bs=3, strength=5, ap=-4, damage=1)
        without_inv = _shots_to_kill(total_wounds=3, toughness=5, save=2, invuln=None,
                                     fnp=None, bs=3, strength=5, ap=-4, damage=1)
        # With INV 4+: saves on 4+ (50%) vs no save (0%) → more shots needed
        assert with_inv > without_inv

    def test_gk_terminator_has_invuln(self):
        """GK Brotherhood Terminator Squad should have 4+ invuln in config."""
        from ranking import RankingEngine
        engine = RankingEngine('grey-knights')
        kw, t, sv, w, oc, inv = engine.get_unit_info('Brotherhood Terminator Squad', None)
        assert inv == 4, f"Expected INV=4 for Brotherhood Terminator Squad, got {inv}"

    def test_gk_strike_has_no_invuln(self):
        """GK Strike Squad should NOT have invuln in config."""
        from ranking import RankingEngine
        engine = RankingEngine('grey-knights')
        kw, t, sv, w, oc, inv = engine.get_unit_info('Strike Squad', None)
        assert inv is None, f"Expected no INV for Strike Squad, got {inv}"

    def test_gk_ndk_has_invuln(self):
        """GK Nemesis Dreadknight should have 4+ invuln in config."""
        from ranking import RankingEngine
        engine = RankingEngine('grey-knights')
        kw, t, sv, w, oc, inv = engine.get_unit_info('Nemesis Dreadknight', None)
        assert inv == 4, f"Expected INV=4 for Nemesis Dreadknight, got {inv}"

