"""Golden loadout locks — death-guard datasheet-verified structures.

Source of truth: workspace/golden_loadouts/death-guard.json
(BSData wh40k-11e catalogue + wahapedia.ru 11ed cross-check, 2026-08-24).

Regression context: the curated-sheet audit sweep flattened these entries.
Verified verdicts now pinned:
- Foetid Bloat-Drone is a pick-one (fleshmower OR 2 plaguespitters); the
  pre-sweep config wrongly fixed BOTH weapons at once.
- Predator sponsons are PAIRS — count=2 choices must resolve (literal
  '2 lascannons' names silently failed engine lookup).
- Destructor pintle names are hyphenated ('Combi-bolter') in merged data;
  un-hyphenated names were silently skipped.
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

GOLDEN = Path(__file__).resolve().parent.parent / "workspace" / "golden_loadouts" / "death-guard.json"


@pytest.fixture(scope="module")
def dg_engine():
    return RankingEngine("death-guard")


@pytest.fixture(scope="module")
def MEQ(request):
    from tests.conftest import _target_from_cfg
    return _target_from_cfg("MEQ")


class TestFoetidBloatDrone:
    """Golden: fleshmower OR two plaguespitters — never both."""

    def test_pick_one_weapon_set(self, dg_engine, MEQ):
        res = dg_engine.resolve_loadout("Foetid Bloat-Drone", MEQ)
        assert res is not None
        _pts, ranged, melee, _i, _info = res
        names = [w.name.lower() for w in ranged + melee]
        has_spitters = any("plaguespitter" in n for n in names)
        has_mower = "fleshmower" in names
        assert has_spitters != has_mower, f"exactly one of plaguespitters/fleshmower, got {names}"

    def test_plague_probe_always_present(self, dg_engine, MEQ):
        res = dg_engine.resolve_loadout("Foetid Bloat-Drone", MEQ)
        _pts, _r, melee, _i, _info = res
        assert any("plague probe" in w.name.lower() for w in melee)


class TestChaosPredatorDestructor:
    """Golden: sponsons are pairs; pintle is one combi max."""

    def test_sponsons_come_in_pairs(self, dg_engine, MEQ):
        res = dg_engine.resolve_loadout("Chaos Predator Destructor", MEQ)
        assert res is not None
        _pts, ranged, _m, _i, _info = res
        names = [w.name for w in ranged]
        lc, hb = names.count("Lascannon"), names.count("Heavy bolter")
        assert (lc == 2) != (hb == 2), f"sponsons must be exactly 2 lascannons or 2 heavy bolters, got {names}"

    def test_pintle_max_one_combi(self, dg_engine, MEQ):
        res = dg_engine.resolve_loadout("Chaos Predator Destructor", MEQ)
        _pts, ranged, _m, _i, _info = res
        names = [w.name for w in ranged]
        combis = [n for n in names if n.startswith("Combi")]
        assert len(combis) <= 1, f"one pintle weapon max, got {combis}"


class TestDefiler:
    """Golden: electroscourge capped at ONE model-wide across both arms."""

    def test_electroscourge_max_one(self, dg_engine, MEQ):
        res = dg_engine.resolve_loadout("Defiler", MEQ)
        assert res is not None
        _pts, ranged, melee, _i, _info = res
        total = [w.name for w in ranged + melee].count("Electroscourge")
        assert total <= 1, f"electroscourge is model-wide capped at 1, got {total}"


class TestHelbrute:
    """Golden: two replacement groups, pick-one each."""

    def test_two_groups_resolve(self, dg_engine, MEQ):
        res = dg_engine.resolve_loadout("Helbrute", MEQ)
        assert res is not None
        _pts, ranged, melee, _i, _info = res
        # multi-melta group always contributes one ranged weapon
        assert len(ranged) >= 1


class TestWeaponPairCounts:
    """Golden follow-up (2026-08-24): 'Two X'/'2 X' choices under-counted.

    BSData models these as N selections of the per-instance profile
    (min=max=2 constraints on the selection entry), confirmed against
    wahapedia 11ed unit composition lines ('equipped with 2 ...').
    Config now uses catalogue-exact singulars + "count": 2.
    """

    def test_defiler_two_excruciators(self, dg_engine, MEQ):
        res = dg_engine.resolve_loadout("Defiler", MEQ)
        assert res is not None
        _pts, ranged, melee, _i, _info = res
        assert [w.name for w in ranged].count("Excruciator cannon") == 2

    def test_pbc_sponsons_are_pairs(self, dg_engine, MEQ):
        res = dg_engine.resolve_loadout("Plagueburst Crawler", MEQ)
        _pts, ranged, _m, _i, _info = res
        pairs = {"Entropy cannon": 2, "Plaguespitter": 2}
        found = {n: [w.name for w in ranged].count(n)
                 for n in pairs if any(w.name == n for w in ranged)}
        assert all(v == 2 for v in found.values()), f"sponsons must be pairs, got {found}"

    def test_bloat_drone_spitters_double(self, dg_engine, MEQ):
        """Plaguespitter branch appends TWO profiles even when Fleshmower wins DPP."""
        cfg = json.load(open(Path(__file__).resolve().parent.parent
                             / "data/config/death-guard/weapon_options.json"))
        import itertools
        for key in ("Foetid Bloat-Drone", "Foetid Bloat Drone"):
            build = cfg[key]["builds"][0]
            hit = False
            for combo in itertools.product(*[s["choices"] for s in build["slots"]]):
                names = [c["name"] for c in combo]
                if "Plaguespitter" not in names:
                    continue
                hit = True
                for c in combo:
                    p = dg_engine.W(c["name"], unit_name=key, category=c.get("type"))
                    assert c.get("count") == 2, f"{key}: Plaguespitter choice lacks count=2"
                    assert p.attacks * 2 == 7.0  # 2 x D6 avg
            assert hit, f"{key}: plaguespitter branch missing"

def test_golden_source_file_exists():
    data = json.loads(GOLDEN.read_text())
    for u in data["units"]:
        assert u.get("_source"), f"{u['unit']}: golden entry without source"
        assert u.get("confidence") == "high", f"{u['unit']}: unpinned confidence"
