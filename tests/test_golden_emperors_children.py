"""Golden loadout locks — emperors-children datasheet-verified structures.

Source of truth: workspace/golden_loadouts/emperors-children.json
(BSData wh40k-11e catalogue + wahapedia.ru 11ed cross-check, 2026-08-24).

Regression context: the curated-sheet audit sweep restructured these entries.
Verified verdicts now pinned:
- Chaos Land Raider equips TWO soulshatter lascannons and may carry at most
  ONE pintle combi (pre-fix config carried two fixed combi bolters).
- Keeper of Secrets fixed trio (phantasmagoria / snapping claws /
  witstealer sword) + optional wargear pick-one.
- Lord Exultant two independent pick-one groups.
- Defiler electroscourge capped at ONE model-wide (golden CSM verdict).

STRUCTURE + COUNT assertions only — damage values stay engine-derived.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from engine.ranking import RankingEngine

GOLDEN = Path(__file__).resolve().parent.parent / "workspace" / "golden_loadouts" / "emperors-children.json"


@pytest.fixture(scope="module")
def ec_engine():
    return RankingEngine("emperors-children")


@pytest.fixture(scope="module")
def MEQ(request):
    from tests.conftest import _target_from_cfg
    return _target_from_cfg("MEQ")


class TestChaosLandRaider:
    """Golden: 2x soulshatter lascannon + twin hb + ONE pintle combi max."""

    def test_two_soulshatter_lascannons(self, ec_engine, MEQ):
        res = ec_engine.resolve_loadout("Chaos Land Raider", MEQ)
        assert res is not None
        _pts, ranged, _m, _i, _info = res
        names = [w.name for w in ranged]
        assert names.count("Soulshatter lascannon") == 2, \
            f"datasheet equips 2 soulshatter lascannons, got {names}"

    def test_pintle_combi_max_one(self, ec_engine, MEQ):
        res = ec_engine.resolve_loadout("Chaos Land Raider", MEQ)
        _pts, ranged, _m, _i, _info = res
        names = [w.name.lower() for w in ranged]
        combis = [n for n in names if n.startswith("combi")]
        assert len(combis) <= 1, f"one pintle weapon max, got {combis}"

    def test_twin_heavy_bolter_present(self, ec_engine, MEQ):
        res = ec_engine.resolve_loadout("Chaos Land Raider", MEQ)
        _pts, ranged, _m, _i, _info = res
        assert any(w.name.lower() == "twin heavy bolter" for w in ranged)


class TestChaosRhino:
    """Golden: combi-bolter equipped; pintle/havoc add-ons resolve."""

    def test_equipped_combi_bolter_resolves(self, ec_engine, MEQ):
        res = ec_engine.resolve_loadout("Chaos Rhino", MEQ)
        assert res is not None
        _pts, ranged, _m, _i, _info = res
        names = [w.name for w in ranged]
        assert "Combi-bolter" in names, "equipped combi-bolter must resolve"


class TestKeeperOfSecrets:
    """Golden: phantasmagoria + snapping claws + witstealer sword fixed."""

    def test_fixed_trio_present(self, ec_engine, MEQ):
        res = ec_engine.resolve_loadout("Keeper Of Secrets", MEQ)
        assert res is not None
        _pts, ranged, melee, _i, _info = res
        rnames = [w.name.lower() for w in ranged]
        mnames = [w.name.lower() for w in melee]
        assert any("phantasmagoria" in n for n in rnames), rnames
        assert any("snapping claws" in n for n in mnames), mnames
        assert any("witstealer sword" in n for n in mnames), mnames


class TestLordExultant:
    """Golden: ccw + bolt pistol fixed, two pick-one groups on top."""

    def test_structure_resolves(self, ec_engine, MEQ):
        res = ec_engine.resolve_loadout("Lord Exultant", MEQ)
        assert res is not None
        _pts, ranged, melee, _i, _info = res
        assert len(melee) >= 2  # close combat weapon + group melee pick
        assert len(ranged) >= 1  # bolt pistol or screamer/plasma pick


class TestDefiler:
    """Golden: electroscourge capped at ONE model-wide across both arms."""

    def test_electroscourge_max_one(self, ec_engine, MEQ):
        res = ec_engine.resolve_loadout("Defiler", MEQ)
        assert res is not None
        _pts, ranged, melee, _i, _info = res
        total = [w.name for w in ranged + melee].count("Electroscourge")
        assert total <= 1, f"electroscourge is model-wide capped at 1, got {total}"


class TestWeaponPairCounts:
    """Golden follow-up (2026-08-24): 'Two X'/'2 X' choices under-counted."""

    def test_defiler_two_excruciators(self, ec_engine, MEQ):
        res = ec_engine.resolve_loadout("Defiler", MEQ)
        _pts, ranged, _m, _i, _info = res
        assert [w.name for w in ranged].count("Excruciator cannon") == 2

    def test_maulerfiend_two_magma_cutters(self, ec_engine, MEQ):
        res = ec_engine.resolve_loadout("Maulerfiend", MEQ)
        _pts, ranged, _m, _i, _info = res
        assert [w.name for w in ranged].count("Magma cutter") == 2

def test_golden_source_file_exists():
    data = json.loads(GOLDEN.read_text())
    for u in data["units"]:
        assert u.get("_source"), f"{u['unit']}: golden entry without source"
        assert u.get("confidence") == "high", f"{u['unit']}: unpinned confidence"
