"""Regression locks for the Orks squad slot migration.

Locks the curated Orks squads to the BSData truth (verified 2026-08-13
against the "Orks - Library" catalogue):

Generator fix (this iteration):
- fuzzy_find_composition substring is now ONE-WAY (config name inside
  BSData name). The old reverse direction ('Boyz' in 'Burna Boyz') silently
  matched variant squads to the BASE Boyz composition and would have
  overwritten correct distinct builds. Burna Boyz and Boyz (Armageddon)
  are now KEPT, not rewritten. (Regression tests in
  test_gen_squad_composition.py::test_substring_is_one_way_variants_kept)

Regenerated squads (11, BSData composition found):
- alloc pools with min/max + typed weapon payloads (Beast Snagga Boyz,
  Breaka Boyz, Kommandos, Meganobz, Nobz, Tankbustas, Warbikers, Boyz,
  Squighog Boyz)
- per-model slots with default choices (Boss Nob Wargear Options)

Kept squads (1, no BSData composition — curated manually):
- Gretchin (Slugga + Grot-smacka)

Note: Burna Boyz and Lootas are now Legends in MFM v1.4 and removed from
config (weapon refs Cuttin' flames / Deffgun no longer in merged data).
Wartrakk was dropped by BSData from the 11e catalogue (unit absent from
merged data) and removed from config the same way.
Note (MFM cross-check, 2026-09-19): the (Armageddon) variant squads
(Boyz, Gretchin, Warboss) and old rev-1 buggy datasheets were dropped by
the 11e Orks catalogue rewrite — they no longer exist in MFM or merged,
so their stale config entries were removed. Wartrakks returned in BSData
rev-3 as a Mounted squadron (added to config with Kustom Shoota /
Multi-busta Launcha builds).

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
    "Gretchin": ("Grot Blasta", "Scavenged Shivs"),
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
    """The no-composition unit keeps its curated build."""

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


class TestRegeneratedSquads:
    def test_squighog_boyz_alloc(self, squads):
        m = _model(squads, "Squighog Boyz", "Squighog Boy")
        assert m["count"] == 4
        alloc = {a["name"]: a for a in m["alloc"]}
        # 11e: 1 Nob on Smasha Squig + 3-4 Squighog Boyz.
        assert alloc["Nob on Smasha Squig"]["min"] == 1
        assert alloc["Nob on Smasha Squig"]["max"] == 1
        assert alloc["Squighog Boy"]["min"] == 3
        assert alloc["Squighog Boy"]["max"] == 4

    def test_beast_snagga_boyz_alloc(self, squads):
        m = _model(squads, "Beast Snagga Boyz", "Beast Snagga Boy")
        assert m["count"] == 10
        alloc = {a["name"]: a for a in m["alloc"]}
        assert alloc["Beast Snagga Boy w/ Thump gun"]["max"] == 1
        assert alloc["Beast Snagga Boy"]["min"] == 8
        assert alloc["Nob"]["min"] == 1

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
        assert alloc["Tankbusta w/ Busta Rokkit Launcha"]["min"] == 4
        assert alloc["Tankbusta w/ Two Busta Rokkit Launchas"]["max"] == 1

    def test_boyz_alloc(self, squads):
        m = _model(squads, "Boyz", "Boy")
        alloc = {a["name"]: a for a in m["alloc"]}
        # Big shoota, rokkit launcha and burna share a single 2-per-10 budget
        # (11e: up to two of those options, still one Nob).
        assert alloc["Boy w/ Big shoota"]["max"] == 2
        assert alloc["Boy w/ Rokkit launcha"]["max"] == 2
        assert alloc["Boy"]["min"] == 6
        assert alloc["Nob"]["min"] == 1

    def test_nobz_alloc(self, squads):
        """11e: Boss Nob is folded into the Nob alloc pool — no separate
        Boss Nob model with Wargear slots. Lock the new pool instead."""
        m = _model(squads, "Nobz", "Nob")
        alloc = {a["name"]: a for a in m["alloc"]}
        assert "Nob w/ Kustom Shoota and Kustom Krumpa" in alloc
        assert "Nob w/ Kombi-rokkit and Kustom Krumpa" in alloc
        assert alloc["Nob w/ Big Choppa"]["max"] == 1


class TestAllSquadsResolve:
    def test_every_squad_resolves(self, ork_engine, squads):
        for name in squads:
            if name.startswith("_"):
                continue
            for t in TARGET_SAMPLES:
                res = ork_engine._best_squad_variant(name, ork_engine.resolve_target(t))
                assert res is not None, f"{name} {t}: did not resolve"
                assert res.get("ranged") or res.get("melee"), f"{name} {t}: empty"
