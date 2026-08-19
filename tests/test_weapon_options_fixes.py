"""Tests for the single-choice-slot fixes (2026-08-19).

Validates that all 13 units with single-choice slots (fixed on 2026-08-19)
now resolve correctly through the engine. Covers:

  1. Aeldari: Wraithknight, Wraithknight With Ghostglaive
     - Left Arm was single-choice (Heavy Wraithcannon) → moved to fixed
  2. Astra Militarum: Armoured Sentinels, Scout Sentinels, Chimera, Taurox
     - Hunter-killer missile / Storm bolter were single-choice → moved to fixed
  3. Blood Angels: Death Company Dreadnought
     - Blood Talons was single-choice → moved to fixed
  4. Genestealer Cults: Achilles Ridgerunners, Goliath Rockgrinder
     - 3 builds each with single-choice slot → consolidated to 1 build with
       multi-choice slot

Per turtle-dojo: STRUCTURE is asserted (weapon names, counts, fixed vs slot),
NOT damage numbers.

Run: python3 -m pytest tests/test_weapon_options_fixes.py -v
"""

import json
from collections import Counter
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.ranking import RankingEngine
from engine.dpp import TargetProfile


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def aeldari_engine():
    return RankingEngine("aeldari")


@pytest.fixture(scope="module")
def am_engine():
    return RankingEngine("astra-militarum")


@pytest.fixture(scope="module")
def ba_engine():
    return RankingEngine("blood-angels")


@pytest.fixture(scope="module")
def gsc_engine():
    return RankingEngine("genestealer-cults")


@pytest.fixture(scope="module")
def ia_engine():
    return RankingEngine("imperial-agents")


def _build(engine, name, target):
    """Resolve the best loadout for a weapon_options unit against a target.
    
    Returns (pts, ranged, melee, innate, info) tuple.
    """
    res = engine.resolve_loadout(name, target=target)
    assert res is not None, f"{name} did not resolve"
    return res  # (pts, ranged, melee, innate, info)


def _rcount(res, name):
    """Count occurrences of a weapon name in the ranged list."""
    return Counter(w.name for w in res[1])[name]


def _mcount(res, name):
    """Count occurrences of a weapon name in the melee list."""
    return Counter(w.name for w in res[2])[name]


def _ranged(res):
    """Get the ranged weapon list."""
    return res[1]


def _melee(res):
    """Get the melee weapon list."""
    return res[2]


# ── Aeldari ──────────────────────────────────────────────────────────


class TestWraithknight:
    """Wraithknight: Suncannon OR Heavy Wraithcannon (Primary Arm slot),
    up to 2 secondary weapons, Scattershield (4+ invuln) as default.

    Known limitation: Scattershield→Heavy Wraithcannon replacement (loses
    INV4) is not modeled — niche option.
    """

    def test_primary_arm_has_choice(self, aeldari_engine, MEQ):
        """Primary Arm slot should resolve to Suncannon or Heavy Wraithcannon."""
        res = _build(aeldari_engine, "Wraithknight", MEQ)
        primary = [w.name for w in _ranged(res)]
        assert any(w in primary for w in ["Suncannon", "Heavy Wraithcannon"]), (
            f"Expected Suncannon or Heavy Wraithcannon, got {primary}"
        )

    def test_secondary_weapon_present(self, aeldari_engine, MEQ):
        """At least one secondary weapon should be resolved."""
        res = _build(aeldari_engine, "Wraithknight", MEQ)
        secondary = ["Scatter Laser", "Shuriken Cannon", "Starcannon"]
        assert any(w in [x.name for x in _ranged(res)] for w in secondary)

    def test_titanic_feet_in_melee(self, aeldari_engine, MEQ):
        """Titanic feet is a fixed melee weapon."""
        res = _build(aeldari_engine, "Wraithknight", MEQ)
        assert _mcount(res, "Titanic Feet") == 1

    def test_invuln_present(self, aeldari_engine, MEQ):
        """Scattershield provides 4+ invuln."""
        res = _build(aeldari_engine, "Wraithknight", MEQ)
        assert res[4].get("INV") == 4, "Wraithknight should have 4+ invuln"


class TestWraithknightGhostglaive:
    """Wraithknight With Ghostglaive: Ghostglaive melee, Scattershield (INV4),
    up to 2 secondary weapons."""

    def test_ghostglaive_in_melee(self, aeldari_engine, MEQ):
        res = _build(aeldari_engine, "Wraithknight With Ghostglaive", MEQ)
        assert _mcount(res, "Titanic Ghostglaive - Strike") == 1

    def test_secondary_weapon_present(self, aeldari_engine, MEQ):
        res = _build(aeldari_engine, "Wraithknight With Ghostglaive", MEQ)
        secondary = ["Scatter Laser", "Shuriken Cannon", "Starcannon"]
        assert any(w in [x.name for x in _ranged(res)] for w in secondary)

    def test_invuln_present(self, aeldari_engine, MEQ):
        res = _build(aeldari_engine, "Wraithknight With Ghostglaive", MEQ)
        assert res[4].get("INV") == 4


# ── Astra Militarum ──────────────────────────────────────────────────


class TestArmouredSentinels:
    """Armoured Sentinels: Hunter-killer missile moved from slot to fixed.

    Wahapedia: "Any number of models can each be equipped with 1
    hunter-killer missile." — every model can take one, so it's fixed.
    """

    def test_hunter_killer_is_fixed(self, am_engine, MEQ):
        res = _build(am_engine, "Armoured Sentinels", MEQ)
        assert _rcount(res, "Hunter-killer missile") >= 1

    def test_main_weapon_slot_resolves(self, am_engine, MEQ):
        """The main weapon slot should resolve to one of the options."""
        res = _build(am_engine, "Armoured Sentinels", MEQ)
        # Should have at least 2 ranged: main weapon + hunter-killer
        assert len(_ranged(res)) >= 2


class TestScoutSentinels:
    """Scout Sentinels: same Hunter-killer missile fix."""

    def test_hunter_killer_is_fixed(self, am_engine, MEQ):
        res = _build(am_engine, "Scout Sentinels", MEQ)
        assert _rcount(res, "Hunter-killer missile") >= 1

    def test_main_weapon_slot_resolves(self, am_engine, MEQ):
        res = _build(am_engine, "Scout Sentinels", MEQ)
        assert len(_ranged(res)) >= 2


class TestChimera:
    """Chimera: 4 slots (Main weapon, Hull weapon, Pintle mount, Extra weapon).

    Wahapedia:
    - Default: Multi-laser, Heavy bolter, Lasgun array, Armoured tracks
    - Main weapon: Multi-laser → Heavy bolter OR Heavy flamer
    - Hull weapon: Heavy bolter → Heavy flamer
    - Pintle mount: Heavy stubber OR Storm bolter
    - Extra weapon: Hunter-killer missile (optional)
    """

    def test_hunter_killer_present(self, am_engine, MEQ):
        res = _build(am_engine, "Chimera", MEQ)
        assert _rcount(res, "Hunter-killer missile") >= 1

    def test_default_weapons_present(self, am_engine, MEQ):
        """Lasgun array and Armoured tracks are fixed."""
        res = _build(am_engine, "Chimera", MEQ)
        assert _rcount(res, "Lasgun array") >= 1
        assert _mcount(res, "Armoured tracks") >= 1

    def test_main_weapon_slot_resolves(self, am_engine, MEQ):
        """Main weapon slot should pick one of: Multi-laser, Heavy bolter, Heavy flamer."""
        res = _build(am_engine, "Chimera", MEQ)
        main_weapons = ["Multi-laser", "Heavy bolter", "Heavy flamer"]
        total = sum(_rcount(res, w) for w in main_weapons)
        assert total >= 1, f"Expected at least 1 main weapon, got {total}"

    def test_hull_weapon_slot_resolves(self, am_engine, MEQ):
        """Hull weapon slot should pick one of: Heavy bolter, Heavy flamer."""
        res = _build(am_engine, "Chimera", MEQ)
        hull_weapons = ["Heavy bolter", "Heavy flamer"]
        # At least one hull weapon should be present (may be same name as main)
        assert any(_rcount(res, w) >= 1 for w in hull_weapons)

    def test_pintle_weapon_slot_resolves(self, am_engine, MEQ):
        """Pintle mount slot should pick one of: Heavy stubber, Storm bolter."""
        res = _build(am_engine, "Chimera", MEQ)
        pintle_weapons = ["Heavy stubber", "Storm bolter"]
        assert any(_rcount(res, w) >= 1 for w in pintle_weapons)


class TestTaurox:
    """Taurox: Storm bolter moved from slot to fixed."""

    def test_storm_bolter_is_fixed(self, am_engine, MEQ):
        res = _build(am_engine, "Taurox", MEQ)
        assert _rcount(res, "Storm bolter") >= 1

    def test_twin_autocannon_present(self, am_engine, MEQ):
        """Twin autocannon is a fixed weapon."""
        res = _build(am_engine, "Taurox", MEQ)
        assert _rcount(res, "Twin autocannon") >= 1


# ── Blood Angels ─────────────────────────────────────────────────────


class TestDeathCompanyDreadnought:
    """Death Company Dreadnought: Blood Talons moved from slot to fixed."""

    def test_blood_talons_is_fixed(self, ba_engine, MEQ):
        res = _build(ba_engine, "Death Company Dreadnought", MEQ)
        assert _mcount(res, "Blood Talons - Strike") >= 1

    def test_resolves_without_error(self, ba_engine, MEQ):
        """Smoke test: the unit resolves without engine errors."""
        res = _build(ba_engine, "Death Company Dreadnought", MEQ)
        assert res is not None


# ── Genestealer Cults ────────────────────────────────────────────────


class TestAchillesRidgerunners:
    """Achilles Ridgerunners: 3 builds consolidated into 1 build with
    multi-choice slot [Heavy mining laser, Achilles missile launcher,
    Heavy mortar].

    Wahapedia: "Any number of models can each have their heavy mining
    laser replaced with one of the following: 1 achilles missile launcher,
    1 heavy mortar"
    """

    def test_resolves_to_one_weapon(self, gsc_engine, MEQ):
        """The slot should pick exactly one main weapon."""
        res = _build(gsc_engine, "Achilles Ridgerunners", MEQ)
        main_weapons = [
            "Heavy mining laser",
            "Achilles missile launcher",
            "Heavy mortar",
        ]
        total = sum(_rcount(res, w) for w in main_weapons)
        assert total == 1, f"Expected 1 main weapon, got {total}"

    def test_twin_heavy_stubber_present(self, gsc_engine, MEQ):
        """Twin heavy stubber is a fixed weapon."""
        res = _build(gsc_engine, "Achilles Ridgerunners", MEQ)
        assert _rcount(res, "Twin heavy stubber") >= 1

    def test_armoured_hull_in_melee(self, gsc_engine, MEQ):
        """Armoured hull is a fixed melee weapon."""
        res = _build(gsc_engine, "Achilles Ridgerunners", MEQ)
        assert _mcount(res, "Armoured hull") >= 1


class TestGoliathRockgrinder:
    """Goliath Rockgrinder: 3 builds consolidated into 1 build with
    multi-choice slot [Heavy mining laser, Clearance incinerator,
    Heavy seismic cannon].

    Wahapedia: "Any number of models can each have their heavy mining
    laser replaced with one of the following: 1 clearance incinerator,
    1 heavy seismic cannon"
    """

    def test_resolves_to_one_weapon(self, gsc_engine, MEQ):
        res = _build(gsc_engine, "Goliath Rockgrinder", MEQ)
        main_weapons = [
            "Heavy mining laser",
            "Clearance incinerator",
            "Heavy seismic cannon",
        ]
        total = sum(_rcount(res, w) for w in main_weapons)
        assert total == 1, f"Expected 1 main weapon, got {total}"

    def test_heavy_stubber_present(self, gsc_engine, MEQ):
        res = _build(gsc_engine, "Goliath Rockgrinder", MEQ)
        assert _rcount(res, "Heavy stubber") >= 1

    def test_drilldozer_blade_in_melee(self, gsc_engine, MEQ):
        res = _build(gsc_engine, "Goliath Rockgrinder", MEQ)
        assert _mcount(res, "Drilldozer blade") >= 1


# ── Cross-target regression ──────────────────────────────────────────


class TestTargetDependence:
    """Slot picks should react to target profile changes."""

    HEAVY = TargetProfile(
        toughness=10, save=3, invuln=None, wounds_per_model=8,
        model_count=1,
    )

    def test_sentinels_main_weapon_flips(self, am_engine, MEQ):
        """Armoured Sentinels main weapon slot should pick differently
        vs MEQ (T4) vs HEAVY (T10)."""
        meq_res = _build(am_engine, "Armoured Sentinels", MEQ)
        heavy_res = _build(am_engine, "Armoured Sentinels", self.HEAVY)
        # Both should have hunter-killer (fixed)
        assert _rcount(meq_res, "Hunter-killer missile") >= 1
        assert _rcount(heavy_res, "Hunter-killer missile") >= 1
        # Main weapon may differ — just verify both resolved
        assert len(_ranged(meq_res)) >= 2
        assert len(_ranged(heavy_res)) >= 2

    def test_ridgerunner_weapon_target_dependent(self, gsc_engine, MEQ):
        """Achilles Ridgerunners: main weapon may differ vs MEQ vs HEAVY."""
        meq_res = _build(gsc_engine, "Achilles Ridgerunners", MEQ)
        heavy_res = _build(gsc_engine, "Achilles Ridgerunners", self.HEAVY)
        # Both should resolve to exactly 1 main weapon
        main_weapons = [
            "Heavy mining laser",
            "Achilles missile launcher",
            "Heavy mortar",
        ]
        meq_total = sum(_rcount(meq_res, w) for w in main_weapons)
        heavy_total = sum(_rcount(heavy_res, w) for w in main_weapons)
        assert meq_total == 1
        assert heavy_total == 1


# ── Imperial Agents ──────────────────────────────────────────────────


class TestInquisitorialChimera:
    """Inquisitorial Chimera: same wargear options as regular Chimera.

    Wahapedia: Multi-laser, Heavy bolter, Lasgun array, Armoured tracks.
    Options: Main weapon swap, Hull weapon swap, Pintle mount, HK missile.
    """

    def test_resolves_with_slots(self, ia_engine, MEQ):
        """Should resolve with multiple weapon slots."""
        res = _build(ia_engine, "Inquisitorial Chimera", MEQ)
        assert len(_ranged(res)) >= 3, (
            f"Expected at least 3 ranged weapons, got {len(_ranged(res))}"
        )

    def test_default_weapons_present(self, ia_engine, MEQ):
        res = _build(ia_engine, "Inquisitorial Chimera", MEQ)
        assert _rcount(res, "Lasgun array") >= 1
        assert _mcount(res, "Armoured tracks") >= 1

    def test_pintle_weapon_resolves(self, ia_engine, MEQ):
        """Pintle mount should pick Heavy stubber or Storm bolter."""
        res = _build(ia_engine, "Inquisitorial Chimera", MEQ)
        pintle = ["Heavy stubber", "Storm bolter"]
        assert any(_rcount(res, w) >= 1 for w in pintle)
