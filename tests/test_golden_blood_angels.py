"""Golden loadout locks — blood-angels datasheet-verified structures.

Source of truth: tests/golden_loadouts/blood-angels.json
(Wahapedia 11ed, fetched 2026-08-24, confidence high).

Covers the curated-regression flags for Death Company Dreadnought /
Baal Predator / Death Company Captain With Jump Pack. STRUCTURE + COUNT
assertions only — damage values stay engine-derived.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from engine.ranking import RankingEngine

GOLDEN = (
    Path(__file__).resolve().parent / "golden_loadouts" / "blood-angels.json"
)


@pytest.fixture(scope="module")
def engine():
    return RankingEngine("blood-angels")


def _names(ws):
    return sorted(w.name for w in ws)


class TestDeathCompanyDreadnought:
    """Golden: icarus stubber fixed; talons OR fists+rifles; HB OR multi-melta."""

    def test_fixed_icarus_and_one_ranged_pick(self, engine, MEQ):
        res = engine.resolve_loadout("Death Company Dreadnought", MEQ)
        _pts, ranged, melee, _i, _info = res
        r = _names(ranged)
        assert r.count("Twin Icarus ironhail heavy stubber") == 1
        picks = [n for n in r if n in ("Twin heavy bolter", "Twin multi-melta")]
        assert len(picks) == 1, f"one ranged pick, got {r}"

    def test_melee_is_talons_or_fists(self, engine, MEQ):
        res = engine.resolve_loadout("Death Company Dreadnought", MEQ)
        _pts, _r, melee, _i, _info = res
        m = _names(melee)
        assert len(m) == 1
        assert m[0].startswith(("Blood Talons", "Blood Fists")), f"got {m}"


class TestBaalPredator:
    """Golden: turret pick-1; sponsons count-2; storm bolter + HKM add-ons; tracks melee."""

    def test_turret_pick_one(self, engine, MEQ):
        res = engine.resolve_loadout("Baal Predator", MEQ)
        _pts, ranged, melee, _i, _info = res
        r = _names(ranged)
        turrets = [n for n in r if n in ("Baal Flamestorm Cannon", "Twin assault cannon")]
        assert len(turrets) == 1, f"exactly one turret gun, got {r}"

    def test_sponsons_come_in_pairs(self, engine, MEQ):
        res = engine.resolve_loadout("Baal Predator", MEQ)
        _pts, ranged, _m, _i, _info = res
        r = _names(ranged)
        hb, hf = r.count("Heavy Bolter"), r.count("Heavy Flamer")
        assert (hb, hf) in [(2, 0), (0, 2)], f"sponsons must be 2-of-a-kind, got {r}"
        # the spurious fixed Heavy Flamer from the regression must stay gone
        assert not (hb and hf)

    def test_addons_and_tracks(self, engine, MEQ):
        res = engine.resolve_loadout("Baal Predator", MEQ)
        _pts, ranged, melee, _i, _info = res
        r = _names(ranged)
        assert "Storm bolter" in r
        assert "Hunter-killer missile" in r
        assert _names(melee) == ["Armoured Tracks"]


class TestDeathCompanyCaptainJumpPack:
    """Golden: one melee swap + one pistol swap; nothing else."""

    def test_swap_structure(self, engine, MEQ):
        res = engine.resolve_loadout("Death Company Captain With Jump Pack", MEQ)
        _pts, ranged, melee, _i, _info = res
        assert len(ranged) == 1
        assert ranged[0].name in ("Heavy Bolt Pistol", "Hand flamer",
                                  "Plasma pistol - standard")
        assert len(melee) == 1
        assert melee[0].name in ("Power fist", "Relic Weapon", "Astartes Chainsword")


def test_golden_source_file_exists():
    data = json.loads(GOLDEN.read_text())
    for u in data["units"]:
        assert u.get("_source"), f"{u['unit']}: golden entry without source"
