"""Golden loadout locks — black-templars.

Source of truth: tests/golden_loadouts/black-templars.json
(Wahapedia 11ed, fetched 2026-08-24, confidence high).

Verdicts applied (regression report lines 20-21):
- Marshal: slot Ranged weapon 1 -> Ranged Weapon was a pure rename; structure
  matches the datasheet (plasma pistol -> combi-weapon). KEPT.
- Repulsor Executioner: 5d21b52 had ONLY the defensive array fixed (245pts,
  badly under-equipped). The regenerated config carries the full equipped
  list + pintle + turret slots per the BT datasheet. KEPT.

STRUCTURE + COUNT assertions only — damage values stay engine-derived.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from engine.ranking import RankingEngine

GOLDEN = Path(__file__).resolve().parent / "golden_loadouts" / "black-templars.json"


def _base(name):
    """Strip choice-profile suffixes ('Plasma Pistol - Standard') for identity."""
    return name.split(" - ")[0].lower()


@pytest.fixture(scope="module")
def engine():
    return RankingEngine("black-templars")


class TestMarshal:
    """Golden: master-crafted power weapon melee + one of plasma pistol / combi-weapon."""

    def test_melee_power_weapon(self, engine, MEQ):
        res = engine.resolve_loadout("Marshal", MEQ)
        assert res is not None
        _pts, _r, melee, _i, _info = res
        assert any("power weapon" in w.name.lower() for w in melee)

    def test_exactly_one_ranged_choice(self, engine, MEQ):
        res = engine.resolve_loadout("Marshal", MEQ)
        _pts, ranged, _melee, _i, _info = res
        guns = [_base(w.name) for w in ranged]
        assert len(guns) == 1, f"exactly one pistol/combi, got {guns}"
        assert guns[0] in ("plasma pistol", "combi-weapon")


class TestRepulsorExecutioner:
    """Golden: full defensive array; turret is laser destroyer OR macro plasma;
    exactly one pintle gun; icarus rocket pod max-legal fixed."""

    def test_defensive_array_present(self, engine, MEQ):
        res = engine.resolve_loadout("Repulsor Executioner", MEQ)
        assert res is not None
        _pts, ranged, _m, _i, _info = res
        names = [w.name.lower() for w in ranged]
        assert "repulsor executioner defensive array" in names

    def test_gatling_and_hull_fixed(self, engine, MEQ):
        res = engine.resolve_loadout("Repulsor Executioner", MEQ)
        _pts, ranged, _m, _i, _info = res
        names = [w.name.lower() for w in ranged]
        assert "heavy onslaught gatling cannon" in names
        assert "twin heavy bolter" in names
        assert "twin icarus ironhail heavy stubber" in names

    def test_turret_one_of_two(self, engine, MEQ):
        res = engine.resolve_loadout("Repulsor Executioner", MEQ)
        _pts, ranged, _m, _i, _info = res
        names = [w.name.lower() for w in ranged]
        turrets = [_base(n) for n in names if _base(n) in (
            "heavy laser destroyer", "macro plasma incinerator")]
        assert len(turrets) == 1, f"exactly one turret weapon, got {turrets}"

    def test_pintle_one_of_two(self, engine, MEQ):
        res = engine.resolve_loadout("Repulsor Executioner", MEQ)
        _pts, ranged, _m, _i, _info = res
        names = [w.name.lower() for w in ranged]
        pintles = [n for n in names if _base(n) in (
            "ironhail heavy stubber", "multi-melta")]
        assert len(pintles) <= 1, f"max one pintle gun, got {pintles}"



class TestSponsonPairs:
    """Golden follow-up (2026-08-24): datasheet grants 2 storm bolters,
    replaceable with 2 fragstorm grenade launchers (wahapedia 11ed).
    Literal '2 Fragstorm Grenade Launchers' names were unresolvable."""

    @pytest.mark.parametrize("unit,slot", [
        ("Gladiator Lancer", "Sponson Weapons"),
        ("Impulsor", "Sponsons"),
    ])
    def test_sponson_pair_resolves(self, engine, MEQ, unit, slot):
        res = engine.resolve_loadout(unit, MEQ)
        assert res is not None
        _pts, ranged, _m, _i, _info = res
        names = [w.name.lower() for w in ranged]
        sponsons = [r for r in names
                    if r in ("storm bolter", "fragstorm grenade launcher")]
        assert len(sponsons) == 2, f"{unit}: pair expected, got {names}"
        assert len(set(sponsons)) == 1, f"{unit}: both must match, got {sponsons}"


def test_golden_source_file_exists():
    data = json.loads(GOLDEN.read_text())
    for u in data["units"]:
        assert u.get("_source"), f"{u['unit']}: golden entry without source"
