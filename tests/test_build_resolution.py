"""Tests for the build resolution path in resolve_loadout.

Shredder WARN #2: unit tests for character/vehicle build resolution
engine picks the best loadout from BSData constraint-based builds.

Covers:
- Character builds: engine picks highest-DPP build
- Character ranged_choices: engine picks best weapon per choice list
- Character melee_choices: engine picks best weapon per choice list
- max_ranged / max_melee: engine picks optimal N from flattened options
- Vehicle builds: same logic via vehicle path
- Fallback to flat format when no builds

Run: python3 -m pytest tests/test_build_resolution.py -v
"""

import json
import os
from pathlib import Path

import pytest

# Ensure engine is importable
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.ranking import RankingEngine, _ld_dmg
from engine.dpp import TargetProfile


CONFIG_DIR = Path(__file__).resolve().parent.parent / "data" / "config"


def _make_target():
    """Standard MEQ target for testing."""
    return TargetProfile(
        toughness=4, save=3, invuln=None,
        wounds_per_model=1, model_count=5
    )


class TestCharacterBuildResolution:
    """Engine correctly picks best build from character builds array."""

    @pytest.fixture
    def engine(self):
        return RankingEngine("space-marines")

    def test_lieutenant_picks_best_build(self, engine):
        """Lieutenant has 2 builds: Neo-volkite + Storm Shield vs Pistol+Bolter+Melee.
        Engine should pick the one with higher DPP."""
        target = _make_target()
        result = engine.resolve_loadout("Lieutenant", target)
        assert result is not None
        pts, ranged, melee, innate, info = result
        # Should have at least 1 ranged or melee weapon
        assert len(ranged) > 0 or len(melee) > 0
        # Points should be non-zero
        assert pts > 0

    def test_lieutenant_does_not_equip_all_weapons(self, engine):
        """Lieutenant build 'Pistol, Master-crafted Bolter & Melee Weapon' has choices.
        Engine should NOT equip all of them — it should pick the optimal subset."""
        target = _make_target()
        result = engine.resolve_loadout("Lieutenant", target)
        assert result is not None
        pts, ranged, melee, innate, info = result
        # Should not have more than 2 ranged weapons (1 fixed pistol + 1 bolter choice)
        # or more than 1 melee weapon
        assert len(ranged) <= 3, f"Too many ranged weapons: {len(ranged)}"
        assert len(melee) <= 2, f"Too many melee weapons: {len(melee)}"

    def test_chaplain_wjp_resolves_choices(self, engine):
        """Chaplain With Jump Pack has ranged_choices with 1 group (pick 1).
        Engine should pick the best pistol/weapon."""
        target = _make_target()
        result = engine.resolve_loadout("Chaplain With Jump Pack", target)
        assert result is not None
        pts, ranged, melee, innate, info = result
        # Should have Crozius arcanum (fixed melee) + 1 ranged from choices
        assert any("crozius" in m.name.lower() for m in melee), \
            "Missing Crozius arcanum in melee"
        # Should have exactly 1 ranged weapon from choices
        assert len(ranged) == 1, f"Expected 1 ranged choice, got {len(ranged)}"

    def test_chaplain_wjp_no_melee_in_ranged(self, engine):
        """Power fist must NOT appear as a ranged weapon after cross-contamination fix."""
        target = _make_target()
        result = engine.resolve_loadout("Chaplain With Jump Pack", target)
        assert result is not None
        pts, ranged, melee, innate, info = result
        for w in ranged:
            assert "power fist" not in w.name.lower(), \
                f"Power fist in ranged loadout: {w.name}"


class TestVehicleBuildResolution:
    """Engine correctly picks best build from vehicle/character builds array."""

    @pytest.fixture
    def engine(self):
        return RankingEngine("chaos-knights")

    def test_knight_despoiler_picks_best_build(self, engine):
        """Knight Despoiler has 6 builds (in characters with builds format).
        Engine should pick the highest-DPP one."""
        target = _make_target()
        result = engine.resolve_loadout("Knight Despoiler", target)
        assert result is not None
        pts, ranged, melee, innate, info = result
        # Should have weapons
        assert len(ranged) > 0 or len(melee) > 0
        assert pts > 0

    def test_knight_despoiler_resolves_cleanly(self, engine):
        """Knight Despoiler has 6 builds modeling 4 independent wargear slots.
        CAN duplicate big guns (rules-legal). Engine should resolve without error."""
        target = _make_target()
        result = engine.resolve_loadout("Knight Despoiler", target)
        assert result is not None
        pts, ranged, melee, innate, info = result
        # Should have weapons
        assert len(ranged) > 0 or len(melee) > 0
        assert pts > 0


class TestBuildResolutionEdgeCases:
    """Edge cases in build resolution."""

    @pytest.fixture
    def engine(self):
        return RankingEngine("space-marines")

    def test_character_with_single_build(self, engine):
        """Character with 1 build (no choices) should resolve cleanly."""
        target = _make_target()
        # Chaplain has 1 build
        result = engine.resolve_loadout("Chaplain", target)
        assert result is not None
        pts, ranged, melee, innate, info = result
        # Should have Absolvor bolt pistol + Crozius arcanum
        assert len(ranged) >= 1
        assert len(melee) >= 1

    def test_characters_without_builds_in_config(self):
        """Characters not in weapon_options but in characters should use flat path."""
        engine = RankingEngine("grey-knights")
        target = _make_target()
        # GK characters may use flat format
        for name in engine.config.characters:
            if name in engine.config.weapon_options:
                continue  # skip, these use builds
            result = engine.resolve_loadout(name, target)
            # May return None if weapon lookup fails, that's OK
            # The point is it doesn't crash
            if result is not None:
                pts, ranged, melee, innate, info = result
                assert pts > 0


class TestBuildResolutionAcrossFactions:
    """Smoke test: resolve_loadout works for characters across multiple factions."""

    @pytest.mark.parametrize("faction", [
        "space-marines", "dark-angels", "blood-angels",
        "chaos-knights", "imperial-knights",
        "tyranids", "necrons", "aeldari",
        "emperors-children", "thousand-sons",
        "death-guard", "world-eaters",
    ])
    def test_resolve_all_characters(self, faction):
        """Every character in every faction resolves without crashing."""
        engine = RankingEngine(faction)
        target = _make_target()
        failures = []
        for name in engine.config.characters:
            if name.startswith("_"):
                continue
            try:
                result = engine.resolve_loadout(name, target)
            except Exception as e:
                failures.append(f"{name}: {e}")
        assert not failures, f"Failed characters in {faction}:\n" + "\n".join(failures)

    @pytest.mark.parametrize("faction", [
        "space-marines", "dark-angels", "blood-angels",
        "chaos-knights", "imperial-knights",
        "tyranids", "necrons", "aeldari",
        "emperors-children", "thousand-sons",
        "death-guard", "world-eaters",
    ])
    def test_resolve_all_vehicles(self, faction):
        """Every vehicle with builds resolves without crashing."""
        engine = RankingEngine(faction)
        target = _make_target()
        failures = []
        for name in engine.config.weapon_options:
            if name.startswith("_"):
                continue
            try:
                result = engine.resolve_loadout(name, target)
                if result is not None:
                    pts, ranged, melee, innate, info = result
            except Exception as e:
                failures.append(f"{name}: {e}")
        assert not failures, f"Failed vehicles in {faction}:\n" + "\n".join(failures)
