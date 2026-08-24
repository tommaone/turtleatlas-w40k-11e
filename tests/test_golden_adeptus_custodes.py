"""Golden loadout locks — adeptus-custodes.

Source of truth: workspace/golden_loadouts/adeptus-custodes.json
(Wahapedia 11ed, fetched 2026-08-24, confidence high).

Verdicts applied (regression report lines 14-15): the 5d21b52 configs were
UNDER-equipped (Allarus SC: balistus fixed with no weapon slot; Jetbike SC:
lance only, ranged gun missing entirely). The regenerated configs match the
11e datasheets — kept and pinned here.

STRUCTURE + COUNT assertions only — damage values stay engine-derived.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from engine.ranking import RankingEngine

GOLDEN = Path(__file__).resolve().parent.parent / "workspace" / "golden_loadouts" / "adeptus-custodes.json"


@pytest.fixture(scope="module")
def engine():
    return RankingEngine("adeptus-custodes")


class TestShieldCaptainAllarus:
    """Golden: balistus grenade launcher ALWAYS present; spear <-> castellan axe."""

    def test_balistus_fixed_ranged(self, engine, MEQ):
        res = engine.resolve_loadout("Shield-Captain In Allarus Terminator Armour", MEQ)
        assert res is not None
        _pts, ranged, _melee, _i, _info = res
        names = [w.name.lower() for w in ranged]
        assert names.count("balistus grenade launcher") == 1

    def test_melee_is_spear_or_axe(self, engine, MEQ):
        res = engine.resolve_loadout("Shield-Captain In Allarus Terminator Armour", MEQ)
        _pts, _r, melee, _i, _info = res
        assert len(melee) >= 1
        assert melee[0].name.lower() in ("guardian spear", "castellan axe")


class TestShieldCaptainJetbike:
    """Golden: interceptor lance melee + exactly ONE of salvo launcher / hurricane bolter."""

    def test_lance_melee(self, engine, MEQ):
        res = engine.resolve_loadout("Shield-Captain On Dawneagle Jetbike", MEQ)
        assert res is not None
        _pts, _r, melee, _i, _info = res
        assert any(w.name.lower() == "interceptor lance" for w in melee)

    def test_exactly_one_ranged_gun(self, engine, MEQ):
        res = engine.resolve_loadout("Shield-Captain On Dawneagle Jetbike", MEQ)
        _pts, ranged, _melee, _i, _info = res
        guns = [w.name.lower() for w in ranged]
        assert len(guns) == 1, f"exactly one ranged gun, got {guns}"
        assert guns[0] in ("salvo launcher", "vertus hurricane bolter")


def test_golden_source_file_exists():
    data = json.loads(GOLDEN.read_text())
    for u in data["units"]:
        assert u.get("_source"), f"{u['unit']}: golden entry without source"
