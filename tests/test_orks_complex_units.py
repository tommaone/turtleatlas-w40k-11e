"""Regression locks for the Orks squad slot migration.

Locks the curated Orks squads to the BSData truth (verified 2026-08-13
against the "Orks - Library" catalogue):

Generator fix (this iteration):
- fuzzy_find_composition substring is now ONE-WAY (config name inside
  BSData name). The old reverse direction ('Boyz' in 'Burna Boyz') silently
  matched variant squads to the BASE Boyz composition and would have
  overwritten correct distinct builds. Burna Boyz, Squighog Boyz and
  Boyz (Armageddon) are now KEPT, not rewritten. (Regression tests in
  test_gen_squad_composition.py::test_substring_is_one_way_variants_kept)

Regenerated squads (10):
- alloc pools with min/max + typed weapon payloads (Beast Snagga Boyz,
  Breaka Boyz, Kommandos, Meganobz, Nobz, Tankbustas, Warbikers, Boyz)
- per-model slots with default choices (Boss Nob Wargear Options)

Kept squads (7, no BSData composition — curated manually):
- Burna Boyz (Burna + Cuttin' flames), Squighog Boyz (Squig jaws),
  Boyz (Armageddon) (Shoota/Kombi variants), Gretchin (Slugga +
  Grot-smacka), Gretchin (Armageddon) (Grot blasta), Lootas (Deffgun),
  Wartrakk (Rokkit launcha + Choppas)

STRUCTURE ONLY — no damage values. The engine is the single source of
computation; this test locks the config shape and resolvability, not math.

Run: python3 -m pytest tests/test_orks_complex_units.py -v
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.ranking import RankingEngine

CONFIG_DIR = Path(__file__).resolve().parent.parent / "data" / "config"
SQUADS_PATH = CONFIG_DIR / "orks" / "squads.json"

TARGET_SAMPLES = ["GEQ", "MEQ", "TEQ"]

# Kept units and their canonical first-model weapons (must NOT be overwritten)
KEPT_UNITS = {
    "Burna Boyz": ("Burna", "Cuttin\u2019 flames"),
    "Squighog Boyz": ("Squig jaws", "Slugga"),
    "Boyz (Armageddon)": ("Shoota", "Choppa"),
    "Gretchin": ("Slugga", "Grot-smacka"),
    "Gretchin (Armageddon)": ("Grot blasta", "Close combat weapon"),
    "Lootas": ("Deffgun", "Close combat weapon"),
    "Wartrakk": ("Rokkit launcha", "Choppas"),
}


@pytest.fixture(scope="module")
def ork_engine():
    return RankingEngine("orks")


@pytest.fixture(scope="module")
def squads():
    return json.load(open(SQUADS_PATH))


def _model(squads, unit, model_name) -> dict:
    build = squads[unit]["builds"][0]
    return next(m for m in build["models"] if m["name"] == model_name)


class TestKeptUnits:
    """The 7 no-composition units keep their curated builds."""

    @pytest.mark.parametrize("unit", list(KEPT_UNITS))
    def test_first_model_weapons(self, squads, unit):
        expect_ranged, expect_melee = KEPT_UNITS[unit]
        m = squads[unit]["builds"][0]["models"][0]
        ranged = m.get("ranged")
        ranged_ok = expect_ranged == ranged or (
            isinstance(ranged, list) and expect_ranged in ranged
        )
        assert ranged_ok, f"{unit}: ranged={ranged}, expected {expect_ranged}"
        assert m.get("melee") == expect_melee, f"{unit}: {m.get('melee')}"

    @pytest.mark.parametrize("unit", ["Burna Boyz", "Squighog Boyz", "Boyz (Armageddon)"])
    def test_variant_not_boyz_payload(self, squads, unit):
        """The generator-fix protection: these must NOT carry the base Boyz
        Melee build (Slugga/Choppa) — each keeps its own ranged identity."""
        m = squads[unit]["builds"][0]["models"][0]
        ranged = m.get("ranged")
        if isinstance(ranged, list):
            ranged = " ".join(ranged)
        assert ranged != "Slugga", f"{unit}: leaked base Boyz payload ({ranged})"


class TestRegeneratedSquads:
    def test_beast_snagga_boyz_alloc(self, squads):
        m = _model(squads, "Beast Snagga Boyz", "Beast Snagga Boy")
        assert m["count"] == 9
        alloc = {a["name"]: a for a in m["alloc"]}
        assert alloc["Beast Snagga Boy w/ Thump gun"]["max"] == 1
        assert alloc["Beast Snagga Boy"]["min"] == 8

    def test_breaka_boyz_alloc(self, squads):
        m = _model(squads, "Breaka Boyz", "Breaka Boy")
        assert m["count"] == 5
        alloc = {a["name"]: a for a in m["alloc"]}
        assert alloc["Breaka Boy"]["min"] == 3
        assert alloc["Breaka Boy w/ Tankhammer"]["max"] == 1

    def test_kommandos_alloc(self, squads):
        m = _model(squads, "Kommandos", "Kommandos")
        alloc = {a["name"]: a for a in m["alloc"]}
        assert alloc["Kommandos w/ Breacha ram"]["max"] == 1
        assert alloc["Kommandos w/ Kustom shoota"]["max"] == 2

    def test_tankbustas_alloc(self, squads):
        m = _model(squads, "Tankbustas", "Tankbusta")
        alloc = {a["name"]: a for a in m["alloc"]}
        assert alloc["Tankbusta w/ Rokkit launcha"]["min"] == 4
        assert alloc["Tankbusta w/ Two rokkit launchas"]["max"] == 1

    def test_boyz_alloc(self, squads):
        m = _model(squads, "Boyz", "Boy")
        alloc = {a["name"]: a for a in m["alloc"]}
        # Big shoota and rokkit launcha share a single 1-per-10 budget.
        assert alloc["Boy w/ Big shoota"]["max"] == 1
        assert alloc["Boy w/ Rokkit launcha"]["max"] == 1
        assert alloc["Boy"]["min"] == 0

    def test_boss_nob_slots(self, squads):
        m = _model(squads, "Nobz", "Boss Nob")
        names = {c["name"] for c in m["slots"][0]["choices"]}
        assert "Slugga and big choppa" in names
        assert "Kombi-weapon" in names


class TestAllSquadsResolve:
    def test_every_squad_resolves(self, ork_engine, squads):
        for name in squads:
            if name.startswith("_"):
                continue
            for t in TARGET_SAMPLES:
                res = ork_engine._best_squad_variant(name, ork_engine.resolve_target(t))
                assert res is not None, f"{name} {t}: did not resolve"
                assert res.get("ranged") or res.get("melee"), f"{name} {t}: empty"
