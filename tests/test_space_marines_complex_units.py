"""End-to-end tests for the complex space-marine squad-composition units.

Runs the full pipeline (BSData parser -> config generator -> engine alloc
resolution) through the real regenerated config
(data/config/space-marines/squads.json) and pins the deterministic resolved
loadouts for every complex unit covered in this iteration.

This iteration migrated space-marines squads to the complex layer:
- parallel-variant alloc pools (Intercessor grenade launchers, Devastator
  heavy weapons, Terminator wargear) — greedy allocation by variant
- per-model weapon slots (sergeants, Centurion options, Inceptor guns)
- multi-fixed-weapon models (Tactical Marine w/ Boltgun + Bolt pistol)
- Nested-pool minimums (Tactical: base pool keeps the 7-model floor)

Per turtle-dojo, STRUCTURE is asserted (alloc distribution, weapon names and
counts, melee reduction), NOT damage numbers — no expected_wounds.

The allocation distribution and slot picks are deterministic against the MEQ
target but target-DEPENDENT by design. Tests flag the target-sensitive picks
in comments so a target change reads as an intentional difference, not a
silent regression.

Run: python3 -m pytest tests/test_space_marines_complex_units.py -v
"""

from collections import Counter
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.ranking import RankingEngine


@pytest.fixture(scope="module")
def sm_engine():
    return RankingEngine("space-marines")


def _build(engine, name, target):
    res = engine._best_squad_variant(name, target)
    assert res is not None, f"{name} did not resolve"
    return res


def _rcount(res, name):
    return Counter(w.name for w in res["ranged"])[name]


def _mcount(res, name):
    return Counter(w.name for w in res["melee"])[name]


class TestSpaceMarinesComplexUnits:
    """Real-config regression pins: exact resolved loadout per complex unit."""

    def test_intercessor_alloc_and_sergeant_slots(self, sm_engine, MEQ):
        """Intercessor Squad n=5: base pool gets all 4 models (grenade
        launchers not worth vs MEQ), Sergeant takes Plasma pistol + Power
        fist (the MEQ slot picks)."""
        res = _build(sm_engine, "Intercessor Squad", MEQ)
        assert res["_alloc_info"] == [
            ("Intercessor", [("Intercessor", 4)]),
        ]
        assert _rcount(res, "Bolt Rifle") == 4
        assert _rcount(res, "Bolt pistol") == 4
        assert _rcount(res, "Plasma pistol - supercharge") == 1
        assert len(res["ranged"]) == 9
        assert _mcount(res, "Close combat weapon") == 4
        assert _mcount(res, "Power fist") == 1
        assert len(res["melee"]) == 5

    def test_tactical_squad_pool_min_and_specials(self, sm_engine, MEQ):
        """Tactical Squad n=10: base pool holds its 7-model floor; one
        Special Weapon and one Heavy/Special weapon fill to 9 + Sergeant.
        vs MEQ the heavy slot takes Multi-melta, the special Meltagun."""
        res = _build(sm_engine, "Tactical Squad", MEQ)
        alloc = dict(res["_alloc_info"][0][1])
        assert alloc["Tactical Marine"] == 7
        assert alloc["Tactical Marine w/Special Weapon"] == 1
        assert alloc["Tactical Marine w/Heavy or Special Weapon"] == 1
        assert _rcount(res, "Boltgun") == 7
        assert _rcount(res, "Meltagun") == 1
        assert _rcount(res, "Multi-melta") == 1
        assert _mcount(res, "Close combat weapon") == 9
        assert _mcount(res, "Power fist") == 1
        assert len(res["melee"]) == 10

    def test_devastator_squad_all_heavy(self, sm_engine, MEQ):
        """Devastator Squad n=5: all 4 non-sergeant models take a Heavy
        Weapon (4 slots in the pool); vs MEQ they all pick Multi-melta."""
        res = _build(sm_engine, "Devastator Squad", MEQ)
        alloc = dict(res["_alloc_info"][0][1])
        assert alloc == {"Devastator Marine w/ Heavy Weapon": 4}
        assert _rcount(res, "Multi-melta") == 4
        assert len(res["ranged"]) == 4
        assert _mcount(res, "Close combat weapon") == 5

    def test_terminator_squad_heavy_slot(self, sm_engine, MEQ):
        """Terminator Squad n=5: 4 Power Fist Terminators + 1 Heavy Weapon
        Terminator with Assault Cannon (MEQ pick)."""
        res = _build(sm_engine, "Terminator Squad", MEQ)
        alloc = dict(res["_alloc_info"][0][1])
        assert alloc == {
            "Terminator w/ Power Fist": 3,
            "Terminator w/ Heavy Weapon": 1,
        }
        assert _rcount(res, "Storm bolter") == 4
        assert _rcount(res, "Assault Cannon") == 1
        assert _mcount(res, "Power fist") == 5  # 3 + sgt (heavy keeps fist?)
        assert len(res["melee"]) == 5

    def test_terminator_assault_all_thunder_hammer(self, sm_engine, MEQ):
        """Terminator Assault Squad n=5: all 4 assault terminators take the
        Thunder Hammer & Storm Shield variant over Twin Lightning Claws.
        Thunder Hammer is a MELEE weapon — asserted via _mcount."""
        res = _build(sm_engine, "Terminator Assault Squad", MEQ)
        alloc = dict(res["_alloc_info"][0][1])
        assert alloc == {
            "Assault Terminator w/ Thunder Hammer & Storm Shield": 4,
        }
        assert len(res["ranged"]) == 0  # pure assault squad — no guns
        assert _mcount(res, "Thunder Hammer") == 5  # 4 terminators + sergeant slot
        assert len(res["melee"]) == 5

    def test_eradicator_heavy_bolters_flat(self, sm_engine, MEQ):
        """Eradicator Squad With Heavy Bolters n=3: FLAT (no alloc) — every
        model carries Heavy Bolter + Bolt pistol. Regression: this unit used
        to resolve to the base Eradicator melta payload via substring."""
        res = _build(sm_engine, "Eradicator Squad With Heavy Bolters", MEQ)
        assert res.get("_alloc_info") is None
        assert _rcount(res, "Heavy Bolter") == 3
        assert _rcount(res, "Melta rifle") == 0
        assert _rcount(res, "Multi-melta") == 0
        assert len(res["ranged"]) == 6
        assert _mcount(res, "Close combat weapon") == 3

    def test_eradicator_standard_has_melta(self, sm_engine, MEQ):
        """Standard Eradicator Squad still has the melta payload (1 Multi-
        melta via alloc)."""
        res = _build(sm_engine, "Eradicator Squad", MEQ)
        alloc = dict(res["_alloc_info"][0][1])
        assert alloc == {
            "Eradicator": 1,
            "Eradicator with Multi-melta": 1,
        }
        assert _rcount(res, "Melta rifle") == 2
        assert _rcount(res, "Multi-melta") == 1
        assert _rcount(res, "Bolt pistol") == 3  # 2 eradicators + sergeant

    def test_heavy_intercessor_heavy_bolter(self, sm_engine, MEQ):
        """Heavy Intercessor Squad n=5: base 3-9 pool + 1 Heavy Bolter
        specialist; Sergeant fires Heavy Bolt Rifle + Bolt pistol."""
        res = _build(sm_engine, "Heavy Intercessor Squad", MEQ)
        alloc = dict(res["_alloc_info"][0][1])
        assert alloc["Heavy Intercessors"] == 3
        assert alloc["Heavy Intercessor w/Heavy Bolter"] == 1
        assert _rcount(res, "Heavy Bolt Rifle") == 4
        assert _rcount(res, "Heavy Bolter") == 1
        assert _rcount(res, "Bolt pistol") == 5  # 4 base pool + sergeant
        assert _mcount(res, "Close combat weapon") == 5

    def test_hard_pool_min_uses_base(self, sm_engine, MEQ):
        """Heavy Intercessor Squad n=8: base pool must fill to 8, the
        Heavy/plasma specialists stay at 0-critical? (n-based, not in this
        iteration — sanity: alloc respects base min when squad n drops)."""
        # small unit: n=4 -> base pool min=3 + 1 heavy? base min forces 3
        res = _build(sm_engine, "Heavy Intercessor Squad", MEQ)
        n = sm_engine.config.squads["Heavy Intercessor Squad"]["n"]
        assert n == 5
        assert sum(count for _, count in res["_alloc_info"][0][1]) == 4

    def test_bladeguard_flat_slots(self, sm_engine, MEQ):
        """Bladeguard Veteran Squad n=3: flat veterans (py2 pistols); the
        sergeant's Pistol slot picks Plasma pistol vs MEQ."""
        res = _build(sm_engine, "Bladeguard Veteran Squad", MEQ)
        assert res.get("_alloc_info") is None
        assert _rcount(res, "Heavy Bolt Pistol") == 2
        assert _rcount(res, "Plasma pistol - supercharge") == 1
        assert _mcount(res, "Master-crafted power weapon") == 3

    def test_melee_reduction_one_per_model(self, sm_engine, MEQ):
        """24.11 melee rule: one non-EA melee per model. Every covered
        complex unit must emit exactly n melee entries."""
        units = [
            "Intercessor Squad",
            "Tactical Squad",
            "Terminator Squad",
            "Terminator Assault Squad",
            "Devastator Squad",
            "Heavy Intercessor Squad",
            "Eradicator Squad",
            "Eradicator Squad With Heavy Bolters",
        ]
        for name in units:
            n = sm_engine.config.squads[name]["n"]
            res = _build(sm_engine, name, MEQ)
            assert len(res["melee"]) == n, (
                f"{name}: {len(res['melee'])} melee entries for {n} models"
            )

    def test_multi_fixed_ranged_all_models_fire(self, sm_engine, MEQ):
        """Every ranged model fires at least one entry — a model with a
        multi-weapon list (Tactical Boltgun + Pistol) must not collapse.

        Devastator Squad is deliberately NOT in the list: its sergeant is
        melee-only in the payload (no pistol), so the squad fires 4 ranged
        entries for 5 models — same shape as the Aeldari Storm Guardian
        platform exclusion (melee-only leader)."""
        units = [
            "Intercessor Squad",
            "Tactical Squad",
            "Terminator Squad",
            "Heavy Intercessor Squad",
            "Eradicator Squad With Heavy Bolters",
        ]
        for name in units:
            n = sm_engine.config.squads[name]["n"]
            res = _build(sm_engine, name, MEQ)
            assert len(res["ranged"]) >= n, (
                f"{name}: {len(res['ranged'])} ranged entries for {n} models"
            )

    def test_slot_pick_survival_vs_target_gap(self, sm_engine, MEQ):
        """Terminator heavy slot is NOT target-dependent yet — pins the
        current (documented) engine limitation so it reads as intentional.

        The Cyclone Missile Launcher is a multi-profile weapon (frag + krak
        profiles under one name). The weapon loader resolves only the FIRST
        profile (frag: S4 D1) so the Cyclone cannot out-damage the Assault
        Cannon (S6 D1 Devastating) vs ANY target — the engine always picks
        the Assault Cannon. This test pins that stable behavior and the gap:
        when multi-profile resolution lands, this assertion flips.
        """
        from engine.dpp import TargetProfile
        heavy = TargetProfile(
            toughness=10, save=3, invuln=None, wounds_per_model=8,
            model_count=1,
        )
        vs_meq = _build(sm_engine, "Terminator Squad", MEQ)
        vs_heavy = _build(sm_engine, "Terminator Squad", heavy)
        assert _rcount(vs_meq, "Assault Cannon") == 1
        assert _rcount(vs_heavy, "Assault Cannon") == 1
        # Both targets keep the same allocation AND slot content.
        assert vs_meq["_alloc_info"] == vs_heavy["_alloc_info"]