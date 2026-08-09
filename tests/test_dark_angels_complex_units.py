"""End-to-end tests for the complex dark-angels squad-composition units.

Runs the full pipeline (BSData parser -> config generator -> engine alloc
resolution) through the real regenerated config
(data/config/dark-angels/squads.json) and pins the deterministic resolved
loadouts for the DA-specific complex units covered in this iteration.

This iteration migrated dark-angels squads to the complex layer:
- alloc pools (Deathwing Terminator heavy weapons, Ravenwing Black Knight
  plasma talons)
- per-model weapon slots (Deathwing Knight Master, Huntmaster)
- fixed multi-weapon models (Inner Circle Companions)
- shared SM squads (Intercessor/Terminator/Devastator etc.) ride the same
  payloads already pinned in test_space_marines_complex_units.py — here we
  pin the DA-specific units plus the DA-catalogue variants.

Also encodes the No-Legends rule outcome: config units whose only BSData
entry is [Legends] are REMOVED from config, not populated with a Legends
payload (Deathwing Command Squad was removed this iteration).

Per turtle-dojo, STRUCTURE is asserted (alloc distribution, weapon names and
counts, melee reduction), NOT damage numbers — no expected_wounds.

Run: python3 -m pytest tests/test_dark_angels_complex_units.py -v
"""

from collections import Counter
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.ranking import RankingEngine


@pytest.fixture(scope="module")
def da_engine():
    return RankingEngine("dark-angels")


def _build(engine, name, target):
    res = engine._best_squad_variant(name, target)
    assert res is not None, f"{name} did not resolve"
    return res


def _rcount(res, name):
    return Counter(w.name for w in res["ranged"])[name]


def _mcount(res, name):
    return Counter(w.name for w in res["melee"])[name]


class TestDarkAngelsComplexUnits:
    """Real-config regression pins: exact resolved loadout per complex unit."""

    def test_deathwing_knights_slots(self, da_engine, MEQ):
        """Deathwing Knights n=5: 4 Knights + 1 Knight Master. Knight slot
        (Unit Weapon Options) picks the DA melee loadout; Master slot takes
        the Great Weapon. No ranged weapons — pure melee squad."""
        res = _build(da_engine, "Deathwing Knights", MEQ)
        assert len(res["ranged"]) == 0
        assert _mcount(res, "Power Weapon") == 4
        assert _mcount(res, "Great Weapon of the Unforgiven") == 1
        assert len(res["melee"]) == 5

    def test_deathwing_terminator_alloc(self, da_engine, MEQ):
        """Deathwing Terminator Squad n=5: 3 stock Terminators + 1 Heavy
        Weapon variant (Assault Cannon vs MEQ) + 1 Sergeant. Storm bolters
        on the 4 non-sergeant bodies."""
        res = _build(da_engine, "Deathwing Terminator Squad", MEQ)
        alloc = dict(res["_alloc_info"][0][1])
        assert alloc == {
            "Deathwing Terminator": 3,
            "Deathwing Terminator w/ Heavy Weapon": 1,
        }
        assert _rcount(res, "Storm Bolter") == 4
        assert _rcount(res, "Assault cannon") == 1
        assert _mcount(res, "Power Fist") == 4
        assert _mcount(res, "Power Weapon") == 1
        assert len(res["melee"]) == 5

    def test_inner_circle_companions_fixed(self, da_engine, MEQ):
        """Inner Circle Companions n=3: flat model entry — every companion
        carries Heavy Bolt Pistol + Calibanite Greatsword (strike profile)."""
        res = _build(da_engine, "Inner Circle Companions", MEQ)
        assert res.get("_alloc_info") is None
        assert _rcount(res, "Heavy Bolt Pistol") == 3
        assert _mcount(res, "Calibanite Greatsword - Strike") == 3
        assert len(res["ranged"]) == 3
        assert len(res["melee"]) == 3

    def test_ravenwing_black_knights_alloc(self, da_engine, MEQ):
        """Ravenwing Black Knights n=3: 2 Knights in the alloc pool (Plasma
        talon - Standard) + 1 Huntmaster with Bolt Pistol + slot (combat
        weapon)."""
        res = _build(da_engine, "Ravenwing Black Knights", MEQ)
        alloc = dict(res["_alloc_info"][0][1])
        assert alloc == {"Ravenwing Black Knight": 2}
        assert _rcount(res, "Plasma talon - Standard") == 3
        assert _rcount(res, "Bolt Pistol") == 2
        assert _mcount(res, "Black Knight combat weapon") == 3
        assert len(res["melee"]) == 3

    def test_no_legends_unit_removed_from_config(self):
        """No-Legends rule outcome: Deathwing Command Squad only exists as
        '[Legends]' in BSData — it was REMOVED from config rather than
        populated with a Legends payload."""
        import json
        cfg = json.loads(
            (Path(__file__).resolve().parent.parent
             / "data/config/dark-angels/squads.json").read_text(encoding="utf-8")
        )
        assert "Deathwing Command Squad" not in cfg
        assert not any("Legends" in k for k in cfg)

    def test_shared_sm_squad_rides_da_payload(self, da_engine, MEQ):
        """A shared SM squad (Intercessor) resolves through the DA config the
        same way it does in SM — grenade launcher not worth vs MEQ, Sergeant
        takes Plasma pistol + Power fist."""
        res = _build(da_engine, "Intercessor Squad", MEQ)
        alloc = dict(res["_alloc_info"][0][1])
        assert alloc == {"Intercessor": 4}
        assert _rcount(res, "Bolt Rifle") == 4
        assert _rcount(res, "Plasma pistol - supercharge") == 1
        assert _mcount(res, "Power fist") == 1
