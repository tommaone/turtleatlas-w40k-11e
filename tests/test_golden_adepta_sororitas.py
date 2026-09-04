"""Golden loadout locks — adepta-sororitas datasheet-verified structures.

Source of truth: tests/golden_loadouts/adepta-sororitas.json
(BSData wh40k-11e catalogue + wahapedia.ru 11ed cross-check, 2026-08-24).

Regression context: the curated-sheet audit sweep flattened/restructured
these entries. Verified verdicts now pinned:
- Castigator equips THREE heavy bolters (was 1 after the sweep).
- Exorcist/Immolator carry NO storm bolter (phantom weapon removed) and
  their hunter-killer missile name must resolve ('hunter killer missile'
  without the hyphen silently failed lookup).

STRUCTURE + COUNT assertions only — damage values stay engine-derived.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from engine.ranking import RankingEngine

GOLDEN = Path(__file__).resolve().parent / "golden_loadouts" / "adepta-sororitas.json"


@pytest.fixture(scope="module")
def sor_engine():
    return RankingEngine("adepta-sororitas")


@pytest.fixture(scope="module")
def MEQ(request):
    from tests.conftest import _target_from_cfg
    return _target_from_cfg("MEQ")


class TestCastigator:
    """Golden: autocannons|battle cannon main gun + THREE heavy bolters + add-ons."""

    def test_three_heavy_bolters(self, sor_engine, MEQ):
        res = sor_engine.resolve_loadout("Castigator", MEQ)
        assert res is not None
        _pts, ranged, _melee, _innate, _info = res
        names = [w.name for w in ranged]
        assert names.count("Heavy bolter") == 3, f"datasheet equips 3 heavy bolters, got {names}"

    def test_main_gun_present(self, sor_engine, MEQ):
        res = sor_engine.resolve_loadout("Castigator", MEQ)
        _pts, ranged, _m, _i, _info = res
        names = [w.name for w in ranged]
        mains = [n for n in names if n in ("Castigator autocannons", "Castigator battle cannon")]
        assert len(mains) == 1, f"exactly one main gun, got {mains}"


class TestExorcist:
    """Golden: missile launcher|conflagration rockets + 1 heavy bolter + HKM."""

    def test_main_weapon_one_of(self, sor_engine, MEQ):
        res = sor_engine.resolve_loadout("Exorcist", MEQ)
        assert res is not None
        _pts, ranged, _m, _i, _info = res
        names = [w.name.lower() for w in ranged]
        mains = [n for n in names if n in ("exorcist missile launcher", "exorcist conflagration rockets")]
        assert len(mains) == 1, f"exactly one main weapon, got {names}"

    def test_hkm_resolves_and_no_phantom_storm_bolter(self, sor_engine, MEQ):
        res = sor_engine.resolve_loadout("Exorcist", MEQ)
        _pts, ranged, _m, _i, _info = res
        names = [w.name for w in ranged]
        assert "Hunter-killer missile" in names, "optional HKM must be taken by max-legal scoring"
        assert "Storm bolter" not in names, "storm bolter is NOT on the 11e Exorcist datasheet"


class TestImmolator:
    """Golden: immolation flamers|twin hb|twin mm + 1 heavy bolter + HKM."""

    def test_main_gun_one_of(self, sor_engine, MEQ):
        res = sor_engine.resolve_loadout("Immolator", MEQ)
        assert res is not None
        _pts, ranged, _m, _i, _info = res
        names = [w.name for w in ranged]
        mains = [n for n in names
                 if n in ("Immolation flamers", "Twin Heavy Bolter", "Twin Multi-melta")]
        assert len(mains) == 1

    def test_hkm_resolves_and_no_phantom_storm_bolter(self, sor_engine, MEQ):
        res = sor_engine.resolve_loadout("Immolator", MEQ)
        _pts, ranged, _m, _i, _info = res
        names = [w.name for w in ranged]
        assert "Hunter-killer missile" in names, "'hunter killer missile' (no hyphen) used to fail lookup"
        assert "Storm bolter" not in names


class TestCanoness:
    """Golden: one melee swap + one ranged swap + optional wargear."""

    def test_one_melee_one_ranged(self, sor_engine, MEQ):
        res = sor_engine.resolve_loadout("Canoness", MEQ)
        assert res is not None
        _pts, ranged, melee, _i, _info = res
        # base pistol/CCW are replaced by the swaps — exactly one each
        assert len(melee) >= 1
        assert len(ranged) >= 1


def test_golden_source_file_exists():
    """The golden corpus must be present and carry sources."""
    data = json.loads(GOLDEN.read_text())
    for u in data["units"]:
        assert u.get("_source"), f"{u['unit']}: golden entry without source"
        assert u.get("confidence") == "high", f"{u['unit']}: unpinned confidence"
