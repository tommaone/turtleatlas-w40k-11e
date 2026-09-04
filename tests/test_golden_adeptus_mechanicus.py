"""Golden loadout locks — adeptus-mechanicus datasheet-verified structures.

Source of truth: tests/golden_loadouts/adeptus-mechanicus.json
(Wahapedia 11ed, fetched 2026-08-24, confidence high).

Covers the curated-regression flags for Stratoraptor / Skorpius
Disintegrator / Sydonian Skatros. STRUCTURE + COUNT assertions only —
damage values stay engine-derived.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from engine.ranking import RankingEngine

GOLDEN = (
    Path(__file__).resolve().parent / "golden_loadouts" / "adeptus-mechanicus.json"
)


@pytest.fixture(scope="module")
def engine():
    return RankingEngine("adeptus-mechanicus")


def _names(ws):
    return sorted(w.name for w in ws)


class TestArchaeopterStratoraptor:
    """Golden: 2 cognis stubbers + 2 phosphor blasters + twin lascannon; hull melee."""

    def test_weapon_multiplicity(self, engine, MEQ):
        res = engine.resolve_loadout("Archaeopter Stratoraptor", MEQ)
        assert res is not None
        _pts, ranged, melee, _i, _info = res
        r = _names(ranged)
        assert r.count("Cognis heavy stubber") == 2, f"got {r}"
        assert r.count("Heavy phosphor blaster") == 2, f"got {r}"
        assert r.count("Twin cognis lascannon") == 1
        # spurious BSData entry must not leak into the loadout
        assert not any("ironhail" in n.lower() for n in r), f"got {r}"
        assert _names(melee) == ["Armoured hull"]

    def test_no_phantom_ranged_from_upgrade_slot(self, engine, MEQ):
        """Chaff launcher / command uplink have no damage profiles."""
        res = engine.resolve_loadout("Archaeopter Stratoraptor", MEQ)
        _pts, ranged, _m, _i, _info = res
        assert len(ranged) == 5


class TestSkorpiusDisintegrator:
    """Golden: 3 cognis stubbers + disruptor missile launcher; belleros OR ferrumite."""

    def test_weapon_multiplicity(self, engine, MEQ):
        res = engine.resolve_loadout("Skorpius Disintegrator", MEQ)
        _pts, ranged, melee, _i, _info = res
        r = _names(ranged)
        assert r.count("Cognis heavy stubber") == 3, f"got {r}"
        assert r.count("Disruptor missile launcher") == 1
        main = [n for n in r if n in ("Belleros energy cannon", "Ferrumite cannon")]
        assert len(main) == 1, f"exactly one main gun, got {r}"
        assert _names(melee) == ["Armoured hull"]


class TestSydonianSkatros:
    """Golden: pistol + jezzail/arquebus ranged; feet melee-only."""

    def test_ranged_structure(self, engine, MEQ):
        res = engine.resolve_loadout("Sydonian Skatros", MEQ)
        _pts, ranged, melee, _i, _info = res
        r = _names(ranged)
        assert "Mechanicus pistol" in r
        mains = [n for n in r if n in ("Radium Jezzail", "Skatros transuranic arquebus")]
        assert len(mains) == 1, f"one rifle pick, got {r}"
        # sydonian feet must sit in the MELEE bucket (melee-profile item)
        assert "Sydonian Feet" not in r
        assert _names(melee) == ["Sydonian Feet"]

    def test_no_fabricated_entries(self, engine, MEQ):
        """'Sydonian legs' / 'TL-409' are not on the datasheet."""
        res = engine.resolve_loadout("Sydonian Skatros", MEQ)
        all_w = _names(res[1]) + _names(res[2])
        assert "Sydonian legs" not in all_w
        assert "TL-409" not in all_w


def test_golden_source_file_exists():
    data = json.loads(GOLDEN.read_text())
    for u in data["units"]:
        assert u.get("_source"), f"{u['unit']}: golden entry without source"


class TestDualEntrySync:
    """Characters.json and weapon_options.json both define Skatros/Manipulus;
    the weapon_options copy SHADOWS the characters one in resolve_loadout.
    Divergence between the copies is silent corruption — pin them in lockstep.
    (Fleet-wide audit is test_golden_vulnerable_units.py's job; other-faction
    dual entries are out of this campaign's scope — tracked separately.)"""

    def _weapon_names(self, entry):
        builds = (entry.get("builds")
                  or entry.get("weapon_options", {}).get("builds", []))
        out = set()
        for b in builds:
            for f in b.get("fixed", []):
                out.add(f["name"].lower())
            for s in b.get("slots", []):
                for c in s.get("choices", []):
                    out.add(c["name"].lower())
        return out

    def test_skatros_copies_match(self):
        base = Path(__file__).resolve().parent.parent / "data" / "config" / "adeptus-mechanicus"
        ch = json.loads((base / "characters.json").read_text())["Sydonian Skatros"]
        wo = json.loads((base / "weapon_options.json").read_text())["Sydonian Skatros"]
        assert self._weapon_names(ch) == self._weapon_names(wo)

    def test_manipulus_copies_match(self):
        base = Path(__file__).resolve().parent.parent / "data" / "config" / "adeptus-mechanicus"
        ch = json.loads((base / "characters.json").read_text())["Tech-Priest Manipulus"]
        wo = json.loads((base / "weapon_options.json").read_text())["Tech-Priest Manipulus"]
        assert self._weapon_names(ch) == self._weapon_names(wo)
