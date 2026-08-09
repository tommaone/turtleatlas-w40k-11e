"""End-to-end tests for the complex space-wolves squad-composition units.

Runs the full pipeline (BSData parser -> config generator -> engine alloc
resolution) through the real regenerated config
(data/config/space-wolves/squads.json) and pins the deterministic resolved
loadouts for the SW-specific complex units covered in this iteration.

This iteration migrated space-wolves squads to the complex layer:
- parallel-variant alloc pools (Wolf Guard Terminators, Wulfen, Thunderwolf
  Cavalry) — greedy allocation by variant
- per-model weapon slots (Blood Claws / Grey Hunters Pack Leaders, Wolf
  Guard Terminator Pack Leader)
- shared SM squads (Intercessor etc.) ride the same payloads already pinned
  in test_space_marines_complex_units.py — here we pin the SW-specific units
  plus the SW-catalogue variants.

SW catalogue note: the SW merged BSData lists the 'Plasma pistol' dual
profiles standard-first, so the engine resolves the bare name to
'Plasma pistol - standard' (S7 AP-2 D1) — unlike SM/DA which resolve it to
'Plasma pistol - supercharge' (S8 AP-3 D2). Consequence pinned below: the
SW Intercessor Sergeant slot picks Hand flamer over the (standard-profile)
Plasma pistol, while the SM/DA Sergeant picks Plasma pistol - supercharge.
This is deterministic and data-order dependent — if SW BSData reorders the
plasma profiles, this pin must be revisited.

Data-coverage note: 'Long Fangs' and 'Wolf Guard' have NO entry in the SW
merged BSData (not even [Legends]), so they are absent from config. That is
a data gap, not a rule outcome, so it is documented here but NOT asserted.

Per turtle-dojo, STRUCTURE is asserted (alloc distribution, weapon names and
counts, melee reduction), NOT damage numbers — no expected_wounds.

The allocation distribution and slot picks are deterministic against the MEQ
target but target-DEPENDENT by design. Tests flag the target-sensitive picks
in comments so a target change reads as an intentional difference, not a
silent regression.

Run: python3 -m pytest tests/test_space_wolves_complex_units.py -v
"""

from collections import Counter
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.ranking import RankingEngine


@pytest.fixture(scope="module")
def sw_engine():
    return RankingEngine("space-wolves")


def _build(engine, name, target):
    res = engine._best_squad_variant(name, target)
    assert res is not None, f"{name} did not resolve"
    return res


def _rcount(res, name):
    return Counter(w.name for w in res["ranged"])[name]


def _mcount(res, name):
    return Counter(w.name for w in res["melee"])[name]


class TestSpaceWolvesComplexUnits:
    """Real-config regression pins: exact resolved loadout per complex unit."""

    def test_intercessor_alloc_and_sergeant_slots(self, sw_engine, MEQ):
        """Intercessor Squad n=5: base pool gets all 4 models (grenade
        launchers not worth vs MEQ). SW-catalogue variant: the bare 'Plasma
        pistol' resolves to STANDARD (S7 AP-2 D1) in SW, so the Sergeant
        picks Hand flamer + Power fist — unlike SM/DA where plasma resolves
        to supercharge and wins the slot."""
        res = _build(sw_engine, "Intercessor Squad", MEQ)
        assert res["_alloc_info"] == [
            ("Intercessor", [("Intercessor", 4)]),
        ]
        assert _rcount(res, "Bolt Rifle") == 4
        assert _rcount(res, "Bolt pistol") == 4
        assert _rcount(res, "Hand flamer") == 1
        assert len(res["ranged"]) == 9
        assert _mcount(res, "Close combat weapon") == 4
        assert _mcount(res, "Power fist") == 1
        assert len(res["melee"]) == 5

    def test_blood_claws_pack_leader_slots(self, sw_engine, MEQ):
        """Blood Claws n=10: 9 fixed Bolt pistol + Chainsword bodies; the
        Pack Leader's two slots pick Plasma pistol - standard + Power weapon
        vs MEQ. (Plasma resolves to standard in the SW catalogue.)"""
        res = _build(sw_engine, "Blood Claws", MEQ)
        assert _rcount(res, "Bolt pistol") == 9
        assert _rcount(res, "Plasma pistol - standard") == 1
        assert len(res["ranged"]) == 10
        assert _mcount(res, "Astartes Chainsword") == 9
        assert _mcount(res, "Power weapon") == 1
        assert len(res["melee"]) == 10

    def test_grey_hunters_pack_leader_slots(self, sw_engine, MEQ):
        """Grey Hunters n=10: 9 fixed Bolt pistol + Carbine + Chainsword
        bodies; the Pack Leader's 'Replace Chainsword' slot picks Power fist
        vs MEQ and keeps the Bolt Carbine (plasma-as-standard not worth the
        swap)."""
        res = _build(sw_engine, "Grey Hunters", MEQ)
        assert _rcount(res, "Bolt Carbine") == 10
        assert _rcount(res, "Bolt pistol") == 9
        assert _mcount(res, "Astartes Chainsword") == 9
        assert _mcount(res, "Power fist") == 1
        assert len(res["melee"]) == 10

    def test_wolf_guard_terminators_alloc_and_pack_leader(self, sw_engine, MEQ):
        """Wolf Guard Terminators n=5: 4 models split across the alloc pool
        (2 storm bolter / 2 Assault Cannon vs MEQ — the cannon variant maxes
        at 2); the Pack Leader slot picks Twin Lightning Claws."""
        res = _build(sw_engine, "Wolf Guard Terminators", MEQ)
        assert res["_alloc_info"] == [
            ("Wolf Guard Terminator", [
                ("Wolf Guard Terminator w/ storm bolter", 2),
                ("Wolf Guard Terminator w/ Assault Cannon", 2),
            ]),
        ]
        assert _rcount(res, "Storm Bolter") == 2
        assert _rcount(res, "Assault Cannon") == 2
        assert _mcount(res, "Master-crafted Power Weapon") == 2
        assert _mcount(res, "Power fist") == 2
        assert _mcount(res, "Twin lightning claws") == 1
        assert len(res["melee"]) == 5

    def test_wulfen_alloc_all_auto_launcher(self, sw_engine, MEQ):
        """Wulfen n=5: the Death Totem variant never beats Stormfrag
        auto-launcher vs MEQ — all 5 models allocate to the launcher."""
        res = _build(sw_engine, "Wulfen", MEQ)
        assert res["_alloc_info"] == [
            ("Wulfen", [("Wulfen w/Auto-launcher", 5)]),
        ]
        assert _rcount(res, "Stormfrag auto-launcher") == 5
        assert _mcount(res, "Wulfen Weapons") == 5

    def test_wulfen_with_storm_shields_alloc(self, sw_engine, MEQ):
        """Wulfen With Storm Shields n=5: same alloc outcome as Wulfen —
        all 5 take the auto-launcher; the storm shield body carries a
        Thunder Hammer."""
        res = _build(sw_engine, "Wulfen With Storm Shields", MEQ)
        assert res["_alloc_info"] == [
            ("Wulfen", [("Wulfen w/Auto-launcher", 5)]),
        ]
        assert _rcount(res, "Stormfrag auto-launcher") == 5
        assert _mcount(res, "Thunder Hammer") == 5

    def test_thunderwolf_cavalry_alloc_plasma(self, sw_engine, MEQ):
        """Thunderwolf Cavalry n=3: all 3 allocate to the plasma pistol
        variant vs MEQ (resolves to Plasma pistol - standard in SW)."""
        res = _build(sw_engine, "Thunderwolf Cavalry", MEQ)
        assert res["_alloc_info"] == [
            ("Thunderwolf", [("Thunderwolf w/ plasma pistol", 3)]),
        ]
        assert _rcount(res, "Plasma pistol - standard") == 3
        assert _mcount(res, "Wolf Guard Weapon") == 3
        assert _mcount(res, "Crushing teeth and claws") == 3
        assert len(res["melee"]) == 6
