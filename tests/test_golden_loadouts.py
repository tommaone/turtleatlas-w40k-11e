"""Golden loadout locks — datasheet-verified equipment structures.

Source of truth: workspace/golden_loadouts/gk-csm-pilot.json
(Wahapedia 11ed, fetched 2026-08-24, confidence high).

These pins exist because curated multi-build configs were silently
flattened by an audit sweep (GMNDK lost weapons) and illegal combos
slipped through (Defiler 2x electroscourge) without any test failing.

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

GOLDEN = Path(__file__).resolve().parent.parent / "workspace" / "golden_loadouts" / "gk-csm-pilot.json"


@pytest.fixture(scope="module")
def gk_engine():
    return RankingEngine("grey-knights")


@pytest.fixture(scope="module")
def csm_engine():
    return RankingEngine("chaos-space-marines")


class TestGrandMasterNemesisDreadknight:
    """Golden: fragstorm fixed + TWO DISTINCT ranged + one melee."""

    def test_two_distinct_ranged_plus_fragstorm(self, gk_engine, MEQ):
        res = gk_engine.resolve_loadout("Grand Master In Nemesis Dreadknight", MEQ)
        assert res is not None
        _pts, ranged, melee, _innate, _info = res
        names = [w.name for w in ranged]
        assert "Fragstorm grenade launcher" in names
        non_frag = [n for n in names if n != "Fragstorm grenade launcher"]
        assert len(non_frag) == 2, f"expected exactly 2 pooled ranged, got {non_frag}"
        assert len(set(non_frag)) == 2, "ranged pool weapons must be distinct"

    def test_melee_present(self, gk_engine, MEQ):
        res = gk_engine.resolve_loadout("Grand Master In Nemesis Dreadknight", MEQ)
        _pts, _r, melee, _i, _info = res
        assert len(melee) >= 1


class TestNemesisDreadknight:
    """Golden: up to two distinct ranged; melee always present."""

    def test_ranged_capped_at_two_distinct(self, gk_engine, MEQ):
        res = gk_engine.resolve_loadout("Nemesis Dreadknight", MEQ)
        assert res is not None
        _pts, ranged, _melee, _i, _info = res
        names = [w.name for w in ranged]
        assert len(names) <= 2, f"max 2 ranged, got {names}"
        assert len(set(names)) == len(names), "no duplicates allowed"

    def test_melee_present(self, gk_engine, MEQ):
        res = gk_engine.resolve_loadout("Nemesis Dreadknight", MEQ)
        _pts, _r, melee, _i, _info = res
        assert len(melee) >= 1


class TestDefiler:
    """Golden: electroscourge capped at ONE model-wide; lascannon/reaper uncapped."""

    def test_electroscourge_max_one(self, csm_engine, MEQ):
        res = csm_engine.compute_ranking(mission="Purge the Foe",
                                         meta_name="all-comers")
        df = [x for x in res if x["name"] == "Defiler"][0]
        detail = df["loadout_detail"]
        assert detail.count("Electroscourge") <= 1

    def test_double_lascannon_is_legal(self, csm_engine, MEQ):
        """RAW verdict: hades lascannon has no cap — both arms may take it.

        Duplicate picks WITHOUT max_count must survive resolution (regression
        guard against the earlier blanket no_duplicates fix).
        """
        build = {
            "fixed": [],
            "slots": [
                {"name": "A", "choices": [{"name": "Hades lascannon", "type": "ranged"}]},
                {"name": "B", "choices": [{"name": "Hades lascannon", "type": "ranged"}]},
            ],
        }
        resolved = csm_engine._resolve_slots_build(build, "Defiler", MEQ)
        assert resolved is not None
        ranged = resolved[0]
        assert [w.name for w in ranged].count("Hades lascannon") == 2

    def test_electroscourge_combo_skipped(self, csm_engine, MEQ):
        """The 2x electroscourge combo must not be selectable."""
        build = {
            "fixed": [],
            "slots": [
                {"name": "A", "choices": [{"name": "Heavy baleflamer", "type": "ranged"},
                                          {"name": "Electroscourge", "type": "melee", "max_count": 1}]},
                {"name": "B", "choices": [{"name": "Heavy missile launcher", "type": "ranged"},
                                          {"name": "Electroscourge", "type": "melee", "max_count": 1}]},
            ],
        }
        resolved = csm_engine._resolve_slots_build(build, "Defiler", MEQ)
        assert resolved is not None
        ranged, melee, _n = resolved[0], resolved[1], resolved[2]
        total_scourge = ([w.name for w in ranged] + [w.name for w in melee]) \
            .count("Electroscourge")
        assert total_scourge <= 1


def test_golden_source_file_exists():
    """The golden corpus must be present and carry sources."""
    data = json.loads(GOLDEN.read_text())
    for u in data["units"]:
        assert u.get("_source"), f"{u['unit']}: golden entry without source"


class TestCsmVehicleCounts:
    """Golden follow-ups (2026-08-24): datasheet weapon counts on CSM vehicles.

    Sources: wahapedia.ru 11ed Chaos Land Raider / Venomcrawler datasheets.
    Root cause of both defects: 'count' was ignored on FIXED entries.
    """

    def test_land_raider_two_soulshatter(self, csm_engine, MEQ):
        res = csm_engine.resolve_loadout("Chaos Land Raider", MEQ)
        _pts, ranged, _m, _i, _info = res
        names = [w.name for w in ranged]
        assert names.count("Soulshatter lascannon") == 2, (
            f"datasheet: 2 soulshatter lascannons, got {names}")

    def test_venomcrawler_two_excruciators(self, csm_engine, MEQ):
        res = csm_engine.resolve_loadout("Venomcrawler", MEQ)
        _pts, ranged, _m, _i, _info = res
        names = [w.name for w in ranged]
        assert names.count("Excruciator cannon") == 2

    def test_predator_sponsons_resolve(self, csm_engine, MEQ):
        """'2 lascannons' literal name was unresolvable — sponsons vanished."""
        cfg = json.load(open(Path(__file__).resolve().parent.parent
                             / "data/config/chaos-space-marines/weapon_options.json"))
        b = cfg["Chaos Predator Destructor"]["builds"][0]
        sponsons = [s for s in b["slots"] if s["name"] == "Sponsons"][0]
        for c in sponsons["choices"]:
            assert "count" in c, f"sponson choice {c['name']} lacks count"
            assert c["count"] == 2
            # catalogue-exact singular must resolve
            csm_engine.W(c["name"], unit_name="Defiler", category=c.get("type"))
