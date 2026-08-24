"""Golden loadout locks — space-wolves datasheet-verified structures.

Source of truth: workspace/golden_loadouts/space-wolves.json
(Wahapedia 11ed, fetched 2026-08-24, confidence high).

The Venerable Dreadnought pins target the CHAPTER-LOCAL datasheet
(wahapedia 'Venerable-Dreadnought-1', 125pts) — NOT the generic SM one.
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
    / "workspace" / "golden_loadouts" / "space-wolves.json"
)


@pytest.fixture(scope="module")
def engine():
    return RankingEngine("space-wolves")


def _names(ws):
    return sorted(w.name for w in ws)


class TestVenerableDreadnought:
    """Golden (SW sheet): DCW + AC/helfrost/MM + SB/HF; greataxe combo build."""

    def test_default_build(self, engine, MEQ):
        res = engine.resolve_loadout("Venerable Dreadnought", MEQ)
        _pts, ranged, melee, _i, _info = res
        r = _names(ranged)
        hull = [n for n in r if n.startswith(("Assault cannon", "Helfrost cannon",
                                              "Multi-melta"))]
        assert len(hull) == 1, f"one hull gun pick, got {r}"
        front = [n for n in r if n in ("Storm bolter", "Heavy Flamer")]
        assert len(front) == 1, f"one front gun pick, got {r}"
        assert len(melee) == 1
        assert melee[0].name == "Dreadnought Combat Weapon"

    def test_greataxe_build_exists(self, engine, MEQ):
        res = engine.resolve_loadout(
            "Venerable Dreadnought", MEQ,
            mode="Fenrisian great axe and blizzard shield")
        assert res is not None, "greataxe build missing — regression not fixed"
        _pts, ranged, melee, _i, info = res
        assert any(n.startswith("Fenrisian great axe") for n in _names(melee)), \
            f"greataxe melee missing, got {_names(melee)}"
        front = [n for n in _names(ranged)
                 if n in ("Storm bolter", "Heavy Flamer")]
        assert len(front) == 1, f"greataxe keeps one front gun, got {_names(ranged)}"

    def test_no_generic_sm_options(self, engine, MEQ):
        """Chapter-local sheet: inferno cannon / twin-lascannon swaps are the
        GENERIC SM Venerable Dreadnought's options, never legal here."""
        res = engine.resolve_loadout("Venerable Dreadnought", MEQ)
        all_w = _names(res[1]) + _names(res[2])
        assert not any("inferno" in n.lower() for n in all_w), f"got {all_w}"
        pts = res[0]
        assert pts == 125, f"SW chapter points, got {pts}"


class TestWolfGuardBattleLeader:
    """Golden: mc power weapon OR thunder hammer; one wargear/ranged swap."""

    def test_swap_structure(self, engine, MEQ):
        res = engine.resolve_loadout("Wolf Guard Battle Leader", MEQ)
        _pts, ranged, melee, _i, _info = res
        assert len(ranged) == 1
        assert ranged[0].name in ("Master-crafted bolt carbine",
                                  "Master-crafted Heavy Bolt Pistol",
                                  "Plasma pistol - standard"), \
            f"got {ranged[0].name}"
        assert len(melee) == 1
        assert melee[0].name in ("Master-crafted Power Weapon", "Thunder Hammer")

    def test_no_phantom_storm_shield_profile(self, engine, MEQ):
        """Storm shield has no damage profile; bare-name lookup used to
        fuzzy-fall back to a phantom Thunder Hammer ranged profile."""
        res = engine.resolve_loadout("Wolf Guard Battle Leader", MEQ)
        names = [w.name for w in res[1]]
        assert "Thunder Hammer" not in names, \
            f"phantom storm-shield profile leaked into ranged: {names}"


def test_golden_source_file_exists():
    data = json.loads(GOLDEN.read_text())
    for u in data["units"]:
        assert u.get("_source"), f"{u['unit']}: golden entry without source"
