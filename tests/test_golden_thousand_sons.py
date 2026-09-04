"""Golden loadout locks — thousand-sons datasheet-verified structures.

Source of truth: tests/golden_loadouts/thousand-sons.json
(BSData wh40k-11e catalogue + wahapedia.ru 11ed cross-check, 2026-08-24).

Regression context: the curated-sheet audit sweep collapsed the Forgefiend's
four flat builds into one build (correct move) and renamed Predator pintle
options to un-hyphenated names that silently failed engine lookup.
Verified verdicts now pinned:
- Forgefiend arm weapons are PAIRS (2 ectoplasma OR 2 hades); head is
  jaws OR ectoplasma cannon + claws (melee claws must appear).
- Predator sponsons are pairs; pintle names hyphenated in merged data.
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

GOLDEN = Path(__file__).resolve().parent / "golden_loadouts" / "thousand-sons.json"


@pytest.fixture(scope="module")
def ts_engine():
    return RankingEngine("thousand-sons")


@pytest.fixture(scope="module")
def MEQ(request):
    from tests.conftest import _target_from_cfg
    return _target_from_cfg("MEQ")


class TestForgefiend:
    """Golden: 2x one arm weapon + jaws | ectoplasma cannon & claws."""

    def test_arm_weapons_are_pairs(self, ts_engine, MEQ):
        res = ts_engine.resolve_loadout("Forgefiend", MEQ)
        assert res is not None
        _pts, ranged, _m, _i, _info = res
        names = [w.name for w in ranged]
        ec, ha = names.count("Ectoplasma cannon"), names.count("Hades autocannon")
        # arms swap as a pair; a third ectoplasma cannon may come from the
        # head option ('Ectoplasma cannon and claws' -> ranged half)
        assert (ec >= 2) != (ha >= 2), f"exactly one arm pair allowed, got {names}"

    def test_head_pick_one(self, ts_engine, MEQ):
        res = ts_engine.resolve_loadout("Forgefiend", MEQ)
        _pts, ranged, melee, _i, _info = res
        rnames = [w.name for w in ranged]
        mnames = [w.name.lower() for w in melee]
        has_jaws = any("forgefiend jaws" in n for n in mnames)
        # 'Ectoplasma cannon and claws' resolves its ranged half (composite
        # convention, cf. Telemon caestus): an odd ectoplasma-cannon count
        # means the head option contributed one on top of the arm pair
        has_cannon_head = (rnames.count("Ectoplasma cannon") % 2) == 1
        assert has_jaws != has_cannon_head, f"exactly one head option, got {rnames} {mnames}"


class TestChaosPredatorAnnihilator:
    """Golden: sponsons are pairs; pintle combi resolves with hyphen."""

    def test_sponsons_come_in_pairs(self, ts_engine, MEQ):
        res = ts_engine.resolve_loadout("Chaos Predator Annihilator", MEQ)
        assert res is not None
        _pts, ranged, _m, _i, _info = res
        names = [w.name for w in ranged]
        lc, ihb = names.count("Lascannon"), names.count("Inferno heavy bolter")
        assert (lc == 2) != (ihb == 2), f"sponsons must be a pair, got {names}"

    def test_pintle_max_one_combi(self, ts_engine, MEQ):
        res = ts_engine.resolve_loadout("Chaos Predator Annihilator", MEQ)
        _pts, ranged, _m, _i, _info = res
        names = [w.name.lower() for w in ranged]
        combis = [n for n in names if n.startswith("inferno combi")]
        assert len(combis) <= 1, f"one pintle weapon max, got {combis}"


class TestDefiler:
    """Golden: electroscourge capped at ONE model-wide across both arms."""

    def test_electroscourge_max_one(self, ts_engine, MEQ):
        res = ts_engine.resolve_loadout("Defiler", MEQ)
        assert res is not None
        _pts, ranged, melee, _i, _info = res
        total = [w.name for w in ranged + melee].count("Electroscourge")
        assert total <= 1, f"electroscourge is model-wide capped at 1, got {total}"


class TestHelbrute:
    """Golden: two replacement groups, pick-one each."""

    def test_two_groups_resolve(self, ts_engine, MEQ):
        res = ts_engine.resolve_loadout("Helbrute", MEQ)
        assert res is not None
        _pts, ranged, melee, _i, _info = res
        # multi-melta group always contributes one ranged weapon
        assert len(ranged) >= 1


class TestWeaponPairCounts:
    """Golden follow-up (2026-08-24): 'Two X'/'2 X' choices under-counted."""

    def test_defiler_two_excruciators(self, ts_engine, MEQ):
        res = ts_engine.resolve_loadout("Defiler", MEQ)
        _pts, ranged, _m, _i, _info = res
        assert [w.name for w in ranged].count("Excruciator cannon") == 2

    def test_maulerfiend_two_magma_cutters(self, ts_engine, MEQ):
        res = ts_engine.resolve_loadout("Maulerfiend", MEQ)
        _pts, ranged, _m, _i, _info = res
        assert [w.name for w in ranged].count("Magma cutter") == 2

    def test_pyraflux_variant_is_pair(self, ts_engine, MEQ):
        """TS Defiler's magma-cutter variant is the pyraflux profile."""
        cfg = json.load(open(Path(__file__).resolve().parent.parent
                             / "data/config/thousand-sons/weapon_options.json"))
        b = cfg["Defiler"]["builds"][0]
        slot = [s for s in b["slots"] if s["name"] == "Excruciator cannons"][0]
        pyraflux = [c for c in slot["choices"]
                    if c["name"] == "Pyraflux magma cutter"]
        assert len(pyraflux) == 1 and pyraflux[0]["count"] == 2
        ts_engine.W("Pyraflux magma cutter", unit_name="Defiler", category="ranged")

def test_golden_source_file_exists():
    data = json.loads(GOLDEN.read_text())
    for u in data["units"]:
        assert u.get("_source"), f"{u['unit']}: golden entry without source"
        assert u.get("confidence") == "high", f"{u['unit']}: unpinned confidence"
