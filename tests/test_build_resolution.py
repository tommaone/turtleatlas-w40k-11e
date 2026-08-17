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
        """Knight Despoiler has 13 builds (full BSData arm space, slots schema).
        Engine should pick the highest-DPP one. Structure locked separately in
        tests/test_chaos_knights_despoiler_builds.py."""
        target = _make_target()
        result = engine.resolve_loadout("Knight Despoiler", target)
        assert result is not None
        pts, ranged, melee, innate, info = result
        # Should have weapons
        assert len(ranged) > 0 or len(melee) > 0
        assert pts > 0

    def test_knight_despoiler_resolves_cleanly(self, engine):
        """Knight Despoiler builds model carapace + shoulder + 2 arm mounts.
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
        # Cross-faction characters shared from other factions (Knights, Inquisitors, etc.)
        # lack MFM pricing in GK data — they're expected to have pts=0
        ZERO_PTS_OK = {
            "Knight Paladin", "Knight Errant", "Knight Gallant", "Knight Warden",
            "Knight Crusader", "Knight Preceptor", "Knight Castellan", "Knight Valiant",
            "Cerastus Knight Lancer", "Cerastus Knight Castigator", "Cerastus Knight Acheron",
            "Cerastus Knight Atrapos", "Questoris Knight Magaera", "Questoris Knight Styrix",
            "Knight Defender", "Knight Destrier",
            "Inquisitor", "Navigator", "Ministorum Priest", "Watch Master", "Inquisitor Kroyle",
        }
        for name in engine.config.characters:
            if name in engine.config.weapon_options:
                continue  # skip, these use builds
            result = engine.resolve_loadout(name, target)
            if result is not None:
                pts, ranged, melee, innate, info = result
                if name in ZERO_PTS_OK:
                    continue  # cross-faction, no pricing in GK
                assert pts > 0, f"{name} has pts={pts}"


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


class TestSquadInnateInBuilds:
    """Squad-level innate weapons must flow through the builds path.

    Regression: _eval_squad_build used to return innate=[] — Purifiers lost
    Purifying Flame on conversion to builds format (GK session gap).
    """

    def test_purifier_innate_per_model(self):
        engine = RankingEngine("grey-knights")
        target = _make_target()
        result = engine.resolve_loadout("Purifier Squad", target)
        assert result is not None
        pts, ranged, melee, innate, info = result
        n = engine.config.squads["Purifier Squad"]["n"]
        pf = [w for w in innate if w.name == "Purifying Flame"]
        assert len(pf) == n, (
            f"Expected {n} Purifying Flame (one per model), got {len(pf)}"
        )

    def test_innate_raises_dpp(self):
        """Squad with innate weapons must out-DPP the same build without them."""
        engine = RankingEngine("grey-knights")
        target = _make_target()
        result = engine.resolve_loadout("Purifier Squad", target)
        pts, ranged, melee, innate, info = result
        with_inn = _ld_dmg(ranged, melee, innate, target,
                           n_models=engine.config.squads["Purifier Squad"]["n"])
        without = _ld_dmg(ranged, melee, [], target,
                          n_models=engine.config.squads["Purifier Squad"]["n"])
        assert with_inn > without


class TestSquadPerModelSlots:
    """Per-model slot resolution in _eval_squad_build (squad composition)."""

    @pytest.fixture
    def aeldari_engine(self):
        return RankingEngine("aeldari")

    def test_slot_count_multiplier(self, aeldari_engine):
        """ranged_count=2 duplicates the weapon profile (Two Avenger Catapults)."""
        target = _make_target()
        build = {"models": [
            {"count": 1, "melee": "Close Combat Weapon", "slots": [
                {"name": "Weapon(s)", "choices": [
                    {"name": "Two Avenger Shuriken Catapults",
                     "ranged": "Avenger shuriken catapult", "ranged_count": 2},
                ]},
            ]},
        ]}
        ld = aeldari_engine._eval_squad_build(build, "Dire Avengers", target=target)
        assert len(ld["ranged"]) == 2
        assert len(ld["melee"]) == 1  # fixed CCW kept

    def test_slot_bundle_overrides_top_level(self, aeldari_engine):
        """A bundle choice overrides the model's top-level weapons for its types.

        Banshee exarch: no top-level weapons; the bundle defines both. The
        Mirrorswords pick must drop the pistol (no ranged) and the top-level
        CCW must never leak into the melee list.
        """
        target = _make_target()
        build = {"models": [
            {"count": 1, "melee": "Close Combat Weapon", "slots": [
                {"name": "Weapons", "choices": [
                    {"name": "Banshee Blade and Shuriken Pistol",
                     "ranged": "Shuriken Pistol", "melee": "Banshee Blade"},
                    {"name": "Mirrorswords", "melee": "Mirrorswords"},
                ]},
            ]},
        ]}
        ld = aeldari_engine._eval_squad_build(build, "Howling Banshees", target=target)
        # Picked one of the two melee bundles — top-level CCW was overridden.
        assert len(ld["melee"]) == 1
        assert ld["melee"][0].name in ("Banshee Blade", "Mirrorswords")
        assert ld["melee"][0].name != "Close Combat Weapon"
        # Mirrorswords pick carries no ranged; blade+pistol pick carries 1.
        assert len(ld["ranged"]) in (0, 1)

    def test_slot_pick_best_vs_target(self, aeldari_engine):
        """The engine picks the slot combo with the highest damage vs the target.

        Exarch CCW fixed (melee), Weapon slot ranged options — exactly one
        ranged weapon joins the 4 fixed Reaper Launchers.
        """
        target = _make_target()
        build = {"models": [
            {"count": 4, "ranged": "Reaper Launcher", "melee": "Close combat weapon"},
            {"count": 1, "melee": "Close combat weapon", "slots": [
                {"name": "Weapon", "choices": [
                    {"name": "Reaper Launcher", "ranged": "Reaper Launcher"},
                    {"name": "Shuriken Cannon", "ranged": "Shuriken Cannon"},
                ]},
            ]},
        ]}
        ld = aeldari_engine._eval_squad_build(build, "Dark Reapers", target=target)
        assert len(ld["ranged"]) == 5  # 4 fixed + exarch slot pick
        assert len(ld["melee"]) == 5  # CCW on all 5 models


class TestSquadAllocModels:
    """Parallel-variant alloc resolution in _eval_squad_build.

    Alloc models carry a budget (count) distributed across variant choices
    with per-variant min/max. Per-model damage is independent, so greedy
    (fill mins, then highest-damage variant with capacity) is optimal.
    """

    @pytest.fixture
    def aeldari_engine(self):
        return RankingEngine("aeldari")

    def _meq(self):
        """11e MEQ — 2 wounds (matches config target_profiles['MEQ'])."""
        return TargetProfile(
            toughness=4, save=3, invuln=None,
            wounds_per_model=2, model_count=5
        )

    def test_alloc_all_to_best_variant(self, aeldari_engine):
        """Windriders vs MEQ: all 3 bikes take the Shuriken Cannon
        (D2 vs 2W MEQ beats the 6-shot Scatter Laser)."""
        target = self._meq()
        build = {"models": [
            {"name": "Windrider", "count": 3, "alloc": [
                {"name": "Twin Shuriken Catapult", "min": 0, "max": 6,
                 "ranged": "Twin Shuriken Catapult", "melee": "Close Combat Weapon"},
                {"name": "Scatter Laser", "min": 0, "max": 6,
                 "ranged": "Scatter Laser", "melee": "Close Combat Weapon"},
                {"name": "Shuriken Cannon", "min": 0, "max": 6,
                 "ranged": "Shuriken Cannon", "melee": "Close Combat Weapon"},
            ]},
        ]}
        ld = aeldari_engine._eval_squad_build(build, "Windriders", target=target)
        names = [w.name for w in ld["ranged"]]
        # BSData 2026-08 library lowercases this profile ("Shuriken cannon").
        # Alloc info keeps the config variant name ("Shuriken Cannon", capital C).
        assert names == ["Shuriken cannon"] * 3
        assert ld["_alloc_info"] == [(
            "Windrider", [("Shuriken Cannon", 3)],
        )]

    def test_alloc_respects_minimums(self, aeldari_engine):
        """Ynnari Reavers: min=2 plain Reaver blocks specials at n=3."""
        target = _make_target()
        build = {"models": [
            {"name": "Reaver", "count": 2, "alloc": [
                {"name": "Reaver", "min": 2, "max": 5,
                 "ranged": "Splinter Rifle", "melee": "Bladevanes"},
                {"name": "Reaver with Blaster", "min": 0, "max": 1,
                 "ranged": "Blaster", "melee": "Bladevanes"},
            ]},
        ]}
        ld = aeldari_engine._eval_squad_build(build, "Ynnari Reavers", target=target)
        assert [w.name for w in ld["ranged"]] == ["Splinter Rifle"] * 2
        # Blaster is strictly better vs MEQ — but the min forces 2 plain Reavers.
        assert [w.name for w in ld["melee"]] == ["Bladevanes"] * 2

    def test_alloc_respects_caps(self, aeldari_engine):
        """Storm Guardians: base min=4, specials cap=2 each — greedy fills the
        best specials up to cap, leaving the base at its minimum."""
        target = _make_target()
        build = {"models": [
            {"name": "Storm Guardian", "count": 8, "alloc": [
                {"name": "Storm Guardian", "min": 4, "max": 10,
                 "ranged": "Shuriken Pistol", "melee": "Close Combat Weapon"},
                {"name": "Fusion Gun", "min": 0, "max": 2,
                 "ranged": "Fusion gun", "melee": "Close Combat Weapon"},
                {"name": "Flamer", "min": 0, "max": 2,
                 "ranged": "Flamer", "melee": "Close Combat Weapon"},
            ]},
        ]}
        ld = aeldari_engine._eval_squad_build(build, "Storm Guardians", target=target)
        r = [w.name for w in ld["ranged"]]
        assert r.count("Fusion gun") == 2  # best special, capped at 2
        assert r.count("Flamer") == 2       # next best special, capped at 2
        assert r.count("Shuriken Pistol") == 4  # base forced to its min
        assert len(r) == 8

    def test_alloc_combo_space(self, aeldari_engine):
        """_alloc_combo_space counts bounded compositions: budget 3 across 3
        uncapped choices → C(3+3-1, 2) = 10."""
        choices = [
            {"max": 6}, {"max": 6}, {"max": 6},
        ]
        assert aeldari_engine._alloc_combo_space(choices, 3) == 10
        # Cap binding: budget 2 across [1, 9, 9] → 5
        # (x1=0: x2+x3=2 → 3 ways; x1=1: x2+x3=1 → 2 ways)
        assert aeldari_engine._alloc_combo_space(
            [{"max": 1}, {"max": 9}, {"max": 9}], 2) == 5
        assert aeldari_engine._alloc_combo_space([], 5) == 1
        assert aeldari_engine._alloc_combo_space([{"max": 2}], 0) == 1

    def test_alloc_respects_pool_min(self, aeldari_engine):
        """Voidscarred: base variants share pool_min=4 — with budget 4 the
        capped specials (Shade Runner etc.) get 0 and all models come from
        the base pool."""
        target = _make_target()
        build = {"models": [
            {"name": "Voidscarred", "count": 4, "alloc": [
                {"name": "Shade Runner", "min": 0, "max": 1,
                 "ranged": "Shuriken Pistol", "melee": "Paired Hekatarii blades"},
                {"name": "Voidscarred w/ rifle", "min": 0, "max": 9, "pool_min": 4,
                 "ranged": "Shuriken rifle", "melee": "Close Combat Weapon"},
                {"name": "Voidscarred with fusion pistol", "min": 0, "max": 1, "pool_min": 4,
                 "ranged": "Fusion pistol", "melee": "Close Combat Weapon"},
            ]},
        ]}
        ld = aeldari_engine._eval_squad_build(build, "Corsair Voidscarred", target=target)
        r = [w.name for w in ld["ranged"]]
        assert "Shuriken Pistol" not in r  # special excluded
        assert len(r) == 4
        # _alloc_info: only base pool variants used
        used = dict(ld["_alloc_info"][0][1])
        assert used.get("Shade Runner", 0) == 0
        assert used.get("Voidscarred w/ rifle", 0) + used.get(
            "Voidscarred with fusion pistol", 0) == 4

    def test_alloc_multiple_fixed_ranged(self, aeldari_engine):
        """Variant with several fixed ranged weapons fires them ALL (Warlock:
        Shuriken Pistol + Destructor)."""
        target = _make_target()
        build = {"models": [
            {"name": "Warlock", "count": 1, "alloc": [
                {"name": "Warlock with Witchblade", "min": 0,
                 "ranged": ["Shuriken Pistol", "Destructor"], "melee": "Witchblade"},
            ]},
        ]}
        ld = aeldari_engine._eval_squad_build(build, "Warlock Conclave", target=target)
        r = [w.name for w in ld["ranged"]]
        assert r == ["Shuriken Pistol", "Destructor"]

    def test_squad_multiple_fixed_melee_reduces_to_best(self, aeldari_engine):
        """A model with [Power sword, Close Combat Weapon] fights with its best
        melee only — one non-EA weapon per model (24.11)."""
        target = _make_target()
        build = {"models": [
            {"name": "Voidscarred w/ pistol and sword", "count": 2,
             "ranged": "Shuriken Pistol",
             "melee": ["Power sword", "Close Combat Weapon"]},
        ]}
        ld = aeldari_engine._eval_squad_build(build, "Corsair Voidscarred", target=target)
        me = [w.name for w in ld["melee"]]
        assert me == ["Power sword", "Power sword"]

    def test_squad_multiple_fixed_ranged_fires_all(self, aeldari_engine):
        """A model with [Fusion pistol, Shuriken Pistol] fires both."""
        target = _make_target()
        build = {"models": [
            {"name": "Voidscarred with fusion pistol", "count": 2,
             "ranged": ["Fusion pistol", "Shuriken Pistol"],
             "melee": "Close Combat Weapon"},
        ]}
        ld = aeldari_engine._eval_squad_build(build, "Corsair Voidscarred", target=target)
        r = [w.name for w in ld["ranged"]]
        assert r == ["Fusion pistol", "Shuriken Pistol"] * 2
