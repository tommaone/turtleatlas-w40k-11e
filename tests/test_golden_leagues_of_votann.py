"""Golden loadout locks — leagues-of-votann.

Source of truth: workspace/golden_loadouts/leagues-of-votann.json
(Wahapedia 11ed, fetched 2026-08-24, confidence high).

Verdicts applied (regression report lines 50-52):
- Einhyr Champion / Kahl: pure slot renames ("Melee weapon 1" -> "Melee
  weapon") and reordering — structurally identical to the verified
  5d21b52 state. KEPT.
- Hekaton Land Fortress: the regenerated single "Sponson weapons" slot
  UNDER-equipped (datasheet has TWO independent sponsons) and parked the
  Hekaton warhead behind an unresolvable 'Pan spectral scanner' choice.
  FIXED: two sponson slots (duplicates legal), warhead forced fixed.

STRUCTURE + COUNT assertions only — damage values stay engine-derived.
"""

import json
import sys
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from engine.ranking import RankingEngine

GOLDEN = Path(__file__).resolve().parent.parent / "workspace" / "golden_loadouts" / "leagues-of-votann.json"


@pytest.fixture(scope="module")
def engine():
    return RankingEngine("leagues-of-votann")


class TestEinhyrChampion:
    """Golden: combi-bolter fixed + mass hammer OR darkstar axe."""

    def test_combi_bolter_fixed(self, engine, MEQ):
        res = engine.resolve_loadout("Einhyr Champion", MEQ)
        assert res is not None
        _pts, ranged, _m, _i, _info = res
        assert any(w.name == "Autoch-pattern combi-bolter" for w in ranged)

    def test_melee_choice(self, engine, MEQ):
        res = engine.resolve_loadout("Einhyr Champion", MEQ)
        _pts, _r, melee, _i, _info = res
        assert melee[0].name in ("Mass hammer", "Darkstar axe")


class TestKahl:
    """Golden: one ranged (combi | volkanite) + one melee (gauntlet | plasma axe)."""

    def test_ranged_choice(self, engine, MEQ):
        res = engine.resolve_loadout("K\u00e2hl", MEQ)
        assert res is not None
        _pts, ranged, _m, _i, _info = res
        guns = [w.name for w in ranged]
        assert len(guns) == 1
        assert guns[0] in ("Autoch-pattern combi-bolter", "Volkanite disintegrator")

    def test_melee_choice(self, engine, MEQ):
        res = engine.resolve_loadout("K\u00e2hl", MEQ)
        _pts, _r, melee, _i, _info = res
        assert melee[0].name in ("Mass gauntlet", "Forgewrought plasma axe")


class TestHekatonLandFortress:
    """Golden: TWO sponsons (any bolt/ion mix); warhead always present."""

    def test_sponsons_exactly_two(self, engine, MEQ):
        res = engine.resolve_loadout("Hekaton Land Fortress", MEQ)
        assert res is not None
        _pts, ranged, _m, _i, _info = res
        counts = Counter(w.name for w in ranged)
        sponsons = counts["Twin bolt cannon"] + counts["Twin ion beamer"]
        assert sponsons == 2, f"exactly two sponson weapons, got {sponsons}"

    def test_main_weapon_one_of_three(self, engine, MEQ):
        res = engine.resolve_loadout("Hekaton Land Fortress", MEQ)
        _pts, ranged, _m, _i, _info = res
        mains = [w.name for w in ranged if w.name in (
            "SP heavy conversion beamer", "Heavy magna-rail cannon",
            "Cyclic ion cannon")]
        assert len(mains) == 1

    def test_warhead_and_matr_fixed(self, engine, MEQ):
        res = engine.resolve_loadout("Hekaton Land Fortress", MEQ)
        _pts, ranged, _m, _i, _info = res
        names = [w.name for w in ranged]
        assert "Hekaton warhead" in names, "warhead is max-legal fixed"
        assert "MATR autocannon" in names

    def test_no_dead_scanner_entry(self, engine, MEQ):
        """'Pan spectral scanner' resolves to nothing — must never leak into
        a scored loadout."""
        res = engine.resolve_loadout("Hekaton Land Fortress", MEQ)
        _pts, ranged, _m, _i, _info = res
        assert all(w.name != "Pan spectral scanner" for w in ranged)


def test_golden_source_file_exists():
    data = json.loads(GOLDEN.read_text())
    for u in data["units"]:
        assert u.get("_source"), f"{u['unit']}: golden entry without source"
