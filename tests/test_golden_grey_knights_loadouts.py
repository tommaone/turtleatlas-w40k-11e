"""Golden loadout locks — grey-knights, datasheet-verified structures.

Source of truth: workspace/golden_loadouts/grey-knights.json
(wahapedia 11ed Faction Pack v1.1 + local BSData catalogue, fetched 2026-08-24,
confidence high). NDK/GMNDK pins live in test_golden_loadouts.py (pilot corpus).

STRUCTURE + COUNT assertions only — damage values stay engine-derived.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from engine.ranking import RankingEngine

GOLDEN = (
    Path(__file__).resolve().parent.parent
    / "workspace"
    / "golden_loadouts"
    / "grey-knights.json"
)


@pytest.fixture(scope="module")
def gk_engine():
    return RankingEngine("grey-knights")


@pytest.fixture(scope="module")
def golden_units():
    data = json.loads(GOLDEN.read_text())
    for u in data["units"]:
        assert u.get("_source"), f"{u['unit']}: golden entry without source"
    return {u["unit"]: u for u in data["units"]}


def _resolved(engine, name, MEQ):
    res = engine.resolve_loadout(name, MEQ)
    assert res is not None, f"{name}: loadout did not resolve"
    _pts, ranged, melee, _innate, _info = res
    return [w.name for w in ranged], [w.name for w in melee]


class TestGoldenCorpus:
    def test_corpus_exists_with_sources(self, golden_units):
        assert "Venerable Dreadnought" in golden_units
        assert "Grey Knights Thunderhawk Gunship" in golden_units


class TestVenerableDreadnought:
    """Golden: one gun from {AC|HPC|TL} + one from {SB|HF} + combat weapon."""

    def test_exactly_two_ranged_one_melee(self, gk_engine, MEQ):
        ranged, melee = _resolved(gk_engine, "Venerable Dreadnought", MEQ)
        assert len(ranged) == 2, f"expected exactly 2 ranged, got {ranged}"
        assert len(melee) == 1, f"expected exactly the combat weapon, got {melee}"

    def test_combat_weapon_always_present(self, gk_engine, MEQ):
        _, melee = _resolved(gk_engine, "Venerable Dreadnought", MEQ)
        assert any("combat weapon" in m.lower() for m in melee), melee

    def test_ranged_from_distinct_groups(self, gk_engine, MEQ):
        ranged, _ = _resolved(gk_engine, "Venerable Dreadnought", MEQ)
        # combined 'X and combat weapon' entries resolve to their ranged profile
        main = ("assault cannon", "heavy plasma cannon", "twin lascannon")
        secondary = ("storm bolter", "heavy flamer")
        lowered = [n.lower() for n in ranged]
        assert any(n.startswith(main) for n in lowered), ranged
        assert any(n.startswith(secondary) for n in lowered), ranged
        assert len(ranged) == 2, ranged


class TestGreyKnightsThunderhawk:
    """Golden: 2 lascannons + 4 twin heavy bolters fixed; pick-1 swaps."""

    def test_fixed_gun_counts(self, gk_engine, MEQ):
        ranged, _ = _resolved(
            gk_engine, "Grey Knights Thunderhawk Gunship", MEQ
        )
        assert ranged.count("Lascannon") == 2, ranged
        assert ranged.count("Twin heavy bolter") == 4, ranged

    def test_main_weapon_is_pick_one(self, gk_engine, MEQ):
        ranged, _ = _resolved(
            gk_engine, "Grey Knights Thunderhawk Gunship", MEQ
        )
        mains = [
            n
            for n in ranged
            if n in ("Thunderhawk heavy cannon", "Turbo-laser destructor")
        ]
        assert len(mains) == 1, f"exactly one main weapon, got {mains}"

    def test_bombs_or_battery_is_pick_one(self, gk_engine, MEQ):
        ranged, _ = _resolved(
            gk_engine, "Grey Knights Thunderhawk Gunship", MEQ
        )
        bombs = [
            n
            for n in ranged
            if n in ("Thunderhawk cluster bombs", "Hellstrike missile battery")
        ]
        assert len(bombs) == 1, f"exactly one bomb/battery pick, got {bombs}"


class TestStormtalonGunship:
    """Golden: TAC + hull fixed; single pick-1 weapon slot."""

    def test_one_swap_weapon_only(self, gk_engine, MEQ):
        ranged, melee = _resolved(gk_engine, "Stormtalon Gunship", MEQ)
        swaps = [
            n
            for n in ranged
            if n
            in (
                "Twin lascannon",
                "Twin heavy bolter",
                "Typhoon missile launcher",
                "Skyhammer missile launcher",
            )
        ]
        assert len(swaps) == 1, f"exactly one swap weapon, got {swaps}"
        assert "Twin assault cannon" in ranged

    def test_skyhammer_not_double_counted(self, gk_engine, MEQ):
        ranged, _ = _resolved(gk_engine, "Stormtalon Gunship", MEQ)
        assert ranged.count("Skyhammer missile launcher") <= 1


class TestStormhawkInterceptorGK:
    """Golden: two independent pick-1 slots over fixed TAC + hull."""

    def test_one_pick_per_group(self, gk_engine, MEQ):
        ranged, _ = _resolved(gk_engine, "Stormhawk Interceptor", MEQ)
        grp1 = [n for n in ranged if n in ("Las-talon", "Icarus stormcannon")]
        grp2 = [
            n
            for n in ranged
            if n
            in ("Twin heavy bolter", "Typhoon missile launcher", "Skyhammer missile launcher")
        ]
        assert len(grp1) == 1, f"group 1 pick, got {grp1}"
        assert len(grp2) == 1, f"group 2 pick, got {grp2}"
        assert "Twin assault cannon" in ranged


class TestNemesisDreadknightStructure:
    """Pilot-corpus carry-over: max 2 distinct ranged; dreadfists base."""

    def test_ranged_capped_at_two_distinct(self, gk_engine, MEQ):
        ranged, _ = _resolved(gk_engine, "Nemesis Dreadknight", MEQ)
        assert len(ranged) <= 2, ranged
        assert len(set(ranged)) == len(ranged), "no duplicates allowed"

    def test_gmndk_three_ranged_max(self, gk_engine, MEQ):
        ranged, _ = _resolved(
            gk_engine, "Grand Master In Nemesis Dreadknight", MEQ
        )
        non_frag = [n for n in ranged if n != "Fragstorm grenade launcher"]
        assert len(non_frag) == 2, non_frag
        assert len(set(non_frag)) == 2, "ranged pool must be distinct"
