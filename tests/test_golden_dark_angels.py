"""Golden loadout locks — dark-angels datasheet-verified structures.

Source of truth: workspace/golden_loadouts/dark-angels.json
(Wahapedia 11ed, fetched 2026-08-24, confidence high).

Covers the curated-regression flags for Land Speeder Vengeance /
Nephilim Jetfighter / Ravenwing Darkshroud. STRUCTURE + COUNT
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
    Path(__file__).resolve().parent.parent
    / "workspace" / "golden_loadouts" / "dark-angels.json"
)


@pytest.fixture(scope="module")
def engine():
    return RankingEngine("dark-angels")


def _names(ws):
    return sorted(w.name for w in ws)


class TestLandSpeederVengeance:
    """Golden: single plasma storm battery + ccw + one of assault cannon/heavy bolter."""

    def test_structure(self, engine, MEQ):
        res = engine.resolve_loadout("Land Speeder Vengeance", MEQ)
        _pts, ranged, melee, _i, _info = res
        r = _names(ranged)
        # 11ed has ONE plasma storm battery (standard/supercharge are profiles,
        # not two weapons — the pre-sweep config double-counted them)
        assert r.count("Plasma storm battery - standard") <= 1
        assert not any("supercharge" in n for n in r), f"got {r}"
        nose = [n for n in r if n in ("Assault cannon", "Heavy bolter")]
        assert len(nose) == 1, f"one nose gun, got {r}"
        assert _names(melee) == ["Close Combat Weapon"]


class TestNephilimJetfighter:
    """Golden: blacksword missiles + twin HB ranged; avenger OR lascannons; no infernum."""

    def test_fixed_ranged_weapons(self, engine, MEQ):
        res = engine.resolve_loadout("Nephilim Jetfighter", MEQ)
        _pts, ranged, melee, _i, _info = res
        r = _names(ranged)
        assert "Blacksword missiles" in r, f"got {r}"
        assert "Twin heavy bolter" in r, f"got {r}"

    def test_nose_gun_pick_one(self, engine, MEQ):
        res = engine.resolve_loadout("Nephilim Jetfighter", MEQ)
        _pts, ranged, _m, _i, _info = res
        guns = [n for n in _names(ranged)
                if n in ("Avenger mega bolter", "Nephilim lascannons")]
        assert len(guns) == 1, f"one nose gun, got {_names(ranged)}"

    def test_no_infernum_halo_launcher(self, engine, MEQ):
        """Not on the datasheet — regression artefact from the sweep."""
        res = engine.resolve_loadout("Nephilim Jetfighter", MEQ)
        assert "Infernum halo launcher" not in _names(res[1])

    def test_missiles_not_melee(self, engine, MEQ):
        res = engine.resolve_loadout("Nephilim Jetfighter", MEQ)
        assert _names(res[2]) == ["Armoured hull"]


class TestRavenwingDarkshroud:
    """Golden: ccw melee; heavy bolter OR assault cannon; no infernum."""

    def test_structure(self, engine, MEQ):
        res = engine.resolve_loadout("Ravenwing Darkshroud", MEQ)
        _pts, ranged, melee, _i, _info = res
        r = _names(ranged)
        assert len(r) == 1
        assert r[0] in ("Heavy bolter", "Assault cannon"), f"got {r}"
        assert _names(melee) == ["Close Combat Weapon"]
        assert "Infernum halo launcher" not in r


def test_golden_source_file_exists():
    data = json.loads(GOLDEN.read_text())
    for u in data["units"]:
        assert u.get("_source"), f"{u['unit']}: golden entry without source"
