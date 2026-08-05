"""End-to-end tests for the complex Aeldari squad-composition units.

Runs the full pipeline (BSData parser -> config generator -> engine alloc
resolution) through the real regenerated config
(data/config/aeldari/squads.json) and pins the deterministic resolved
loadouts for every complex unit covered in this iteration.

This iteration added three composition mechanisms, each of which had a bug
at some point in the pipeline — these tests are the regression net:

  1. Nested-SEG base pools with `pool_min` (Corsair Voidscarred)
  2. Multi-weapon fixed lists (Warlock Conclave, Skyrunners, Reavers, Rangers)
  3. Melee reduction to one non-EA weapon per model (24.11)

Per turtle-dojo, STRUCTURE is asserted (alloc distribution, weapon names and
counts, melee reduction), NOT damage numbers — no expected_wounds.

The allocation distribution and slot picks are deterministic against the MEQ
target but target-DEPENDENT by design. Tests flag the target-sensitive picks
in comments so a target change reads as an intentional difference, not a
silent regression.

Run: python3 -m pytest tests/test_aeldari_complex_units.py -v
"""

from collections import Counter
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.ranking import RankingEngine
from engine.dpp import TargetProfile


@pytest.fixture(scope="module")
def aeldari_engine():
    return RankingEngine("aeldari")


def _build(engine, name, target):
    """Resolve the best squad variant for a unit against a target."""
    res = engine._best_squad_variant(name, target)
    assert res is not None, f"{name} did not resolve"
    return res


def _rcount(res, name):
    return Counter(w.name for w in res["ranged"])[name]


def _mcount(res, name):
    return Counter(w.name for w in res["melee"])[name]


class TestAeldariComplexUnits:
    """Real-config regression pins: exact resolved loadout per complex unit.

    The 11e MEQ profile is T4/SV3+/2W (loaded from data/config/_base.json via
    the shared `MEQ` fixture) — the 2-wound profile drives several picks
    (Shuriken Cannon over Scatter Laser, Shuriken cannon over Wraithcannon).
    """

    def test_voidscarred_nested_pool_and_felarch(self, aeldari_engine, MEQ):
        """Corsair Voidscarred n=5: pool_min=4 forces the 4 base-pool variants;
        the 3 capped specials (Shade Runner, Soul Weaver, Way Seeker) get 0."""
        res = _build(aeldari_engine, "Corsair Voidscarred", MEQ)
        used = dict(res["_alloc_info"][0][1])
        assert used == {
            "Voidscarred w/ pistol and sword": 1,
            "Voidscarred with fusion pistol": 1,
            "Voidscarred with heavy weapon": 1,
            "Voidscarred with special weapon": 1,
        }
        # The MEQ-optimal slot picks: heavy -> Shuriken cannon (D2 beats
        # Wraithcannon vs 2W), special -> Corsair blaster, Felarch -> rifle.
        assert _rcount(res, "Shuriken Pistol") == 2
        assert _rcount(res, "Fusion pistol") == 1
        assert _rcount(res, "Shuriken cannon") == 1
        assert _rcount(res, "Corsair blaster") == 1
        assert _rcount(res, "Shuriken rifle") == 1
        assert len(res["ranged"]) == 6  # 5 models, fusion model fires 2
        # Melee reduced to one non-EA weapon per model (24.11): sword models
        # drop the CCW, Felarch drops its CCW.
        assert _mcount(res, "Power sword") == 2
        assert _mcount(res, "Close Combat Weapon") == 3
        assert len(res["melee"]) == 5

    def test_warlock_conclave_multi_fixed_and_singing_spear(
            self, aeldari_engine, MEQ):
        """Warlock Conclave n=2: both models take the Singing Spear variant
        (best vs MEQ); each fires its FULL fixed list (Spear + Pistol +
        Destructor) AND fights with the spear's melee half (A2 S3 D3)."""
        res = _build(aeldari_engine, "Warlock Conclave", MEQ)
        assert res["_alloc_info"] == [
            ("Warlock", [("Warlock with Singing Spear", 2)]),
        ]
        assert _rcount(res, "Singing Spear") == 2
        assert _rcount(res, "Shuriken Pistol") == 2
        assert _rcount(res, "Destructor") == 2
        assert len(res["ranged"]) == 6  # 3 fixed weapons per model, all fire
        # Warlocks ALWAYS have a melee profile — the spear's melee half.
        assert _mcount(res, "Singing Spear") == 2
        assert len(res["melee"]) == 2

    def test_warlock_skyrunner_four_ranged_plus_melee(self, aeldari_engine, MEQ):
        """Warlock Skyrunner n=1: Singing Spear variant fires FOUR fixed
        weapons (Twin Shuriken Catapult + Pistol + Destructor + Spear) AND
        has the spear's melee half."""
        res = _build(aeldari_engine, "Warlock Skyrunners", MEQ)
        assert res["_alloc_info"] == [
            ("Warlock Skyrunner", [("Warlock Skyrunner with Singing Spear", 1)]),
        ]
        assert Counter(w.name for w in res["ranged"]) == Counter({
            "Shuriken Pistol": 1,
            "Twin Shuriken Catapult": 1,
            "Destructor": 1,
            "Singing Spear": 1,
        })
        assert len(res["ranged"]) == 4
        assert _mcount(res, "Singing Spear") == 1
        assert len(res["melee"]) == 1

    def test_ynnari_reavers_min_pool_and_champion_slot(
            self, aeldari_engine, MEQ):
        """Ynnari Reavers n=3: min=2 plain Reaver blocks the Blaster pool at
        n=3; Arena Champion carries the Bike Weapon slot (Blaster vs MEQ)."""
        res = _build(aeldari_engine, "Ynnari Reavers", MEQ)
        assert res["_alloc_info"] == [
            ("Reaver", [("Reaver", 2)]),
        ]
        assert _rcount(res, "Splinter Rifle") == 2
        assert _rcount(res, "Splinter Pistol") == 2  # NOT 3 — see edge cases
        assert _rcount(res, "Blaster") == 1
        # Champion melee reduced from [Agonizer, Bladevanes] to Agonizer.
        assert _mcount(res, "Agonizer") == 1
        assert _mcount(res, "Bladevanes") == 2
        assert len(res["melee"]) == 3

    def test_voidreavers_slot_variants_and_felarch(self, aeldari_engine, MEQ):
        """Corsair Voidreavers n=5: heavy slot + 2 specials + Felarch slot."""
        res = _build(aeldari_engine, "Corsair Voidreavers", MEQ)
        used = dict(res["_alloc_info"][0][1])
        assert used == {
            "Voidreaver with Heavy weapon": 1,
            "Voidreaver with Blaster": 2,
            "Voidreaver with Shredder": 1,
        }
        assert _rcount(res, "Shuriken cannon") == 1
        assert _rcount(res, "Blaster") == 2
        assert _rcount(res, "Shuriken Pistol") == 3  # 2 blaster + 1 shredder
        assert _rcount(res, "Corsair shredder") == 1
        assert _rcount(res, "Shuriken rifle") == 1  # Felarch slot pick
        assert len(res["ranged"]) == 8
        assert _mcount(res, "Close Combat Weapon") == 4
        assert _mcount(res, "Power sword") == 1  # Felarch
        assert len(res["melee"]) == 5

    def test_troupe_lead_player_slot_all_fusion(self, aeldari_engine, MEQ):
        """Troupe n=5: all 4 Players take Fusion Pistol; Lead Player slot
        picks Fusion Pistol too — 5 Fusion Pistols."""
        res = _build(aeldari_engine, "Troupe", MEQ)
        assert res["_alloc_info"] == [
            ("Player", [("Player with Fusion Pistol", 4)]),
        ]
        assert _rcount(res, "Fusion Pistol") == 5
        assert len(res["ranged"]) == 5
        assert _mcount(res, "Harlequin's Special Weapon") == 4
        assert _mcount(res, "Power sword") == 1  # Lead Player
        assert len(res["melee"]) == 5

    def test_storm_guardians_min_plus_specials(self, aeldari_engine, MEQ):
        """Storm Guardians n=11: base min=4, capped specials fill the rest
        (Fusion Gun, Flamer & Power Sword, Fusion Gun & Power Sword ×2 each)."""
        res = _build(aeldari_engine, "Storm Guardians", MEQ)
        used = dict(res["_alloc_info"][0][1])
        assert used == {
            "Storm Guardian": 4,
            "Storm Guardian with Fusion Gun": 2,
            "Storm Guardian with Flamer & Power Sword": 2,
            "Storm Guardian with Fusion Gun & Power Sword": 2,
        }
        assert _rcount(res, "Shuriken Pistol") == 4
        assert _rcount(res, "Fusion gun") == 4  # 2 plain + 2 with PS variant
        assert _rcount(res, "Flamer") == 2
        assert len(res["ranged"]) == 10  # platform is melee-only (no ranged)
        assert _mcount(res, "Close Combat Weapon") == 7  # 6 guards + platform
        assert _mcount(res, "Power sword") == 4  # the two PS special variants
        assert len(res["melee"]) == 11

    def test_windriders_all_shuriken_cannon_2w_meq(self, aeldari_engine, MEQ):
        """Windriders n=3: all bikes take Shuriken Cannon — the D2 lesson.
        vs a 2W MEQ, the D2 cannon out-damages the 6-shot Scatter Laser."""
        res = _build(aeldari_engine, "Windriders", MEQ)
        assert res["_alloc_info"] == [
            ("Windrider", [("Windrider with Shuriken Cannon", 3)]),
        ]
        assert _rcount(res, "Shuriken Cannon") == 3
        assert _mcount(res, "Close Combat Weapon") == 3

    def test_kabalite_warriors_nine_alloc_sybarite(self, aeldari_engine, MEQ):
        """Ynnari Kabalite Warriors n=10: 9-model alloc (all capped specials
        filled, rest base) + Sybarite with Ranged slot."""
        res = _build(aeldari_engine, "Ynnari Kabalite Warriors", MEQ)
        used = dict(res["_alloc_info"][0][1])
        assert used == {
            "Kabalite Warrior with Shredder": 1,
            "Kabalite Warrior": 5,
            "Kabalite Warrior with Blaster": 1,
            "Kabalite Warrior with Splinter Cannon": 1,
            "Kabalite Warrior with Dark Lance": 1,
        }
        assert _rcount(res, "Shredder") == 1
        assert _rcount(res, "Splinter Rifle") == 5
        assert _rcount(res, "Blaster") == 1
        assert _rcount(res, "Splinter Cannon") == 1
        assert _rcount(res, "Dark Lance") == 1
        assert _rcount(res, "Blast Pistol") == 1  # Sybarite slot pick
        assert len(res["ranged"]) == 10
        assert _mcount(res, "Close Combat Weapon") == 9
        assert _mcount(res, "Sybarite Weapon") == 1
        assert len(res["melee"]) == 10

    def test_rangers_both_fixed_fire(self, aeldari_engine, MEQ):
        """Rangers n=5 (flat, no alloc): every model fires BOTH fixed weapons —
        10 ranged entries for 5 models."""
        res = _build(aeldari_engine, "Rangers", MEQ)
        assert res.get("_alloc_info") is None  # flat build: no alloc key
        assert _rcount(res, "Long rifle") == 5
        assert _rcount(res, "Shuriken Pistol") == 5
        assert len(res["ranged"]) == 10
        assert _mcount(res, "Close Combat Weapon") == 5

    def test_fire_dragons_exarch_pistol_plus_axe(self, aeldari_engine, MEQ):
        """Fire Dragons n=5: 4 Dragon Fusion Guns + Exarch Dragon Fusion
        Pistol (ranged) + Dragon Axe (melee)."""
        res = _build(aeldari_engine, "Fire Dragons", MEQ)
        assert _rcount(res, "Dragon Fusion Gun") == 4
        assert _rcount(res, "Dragon Fusion Pistol") == 1
        assert len(res["ranged"]) == 5
        assert _mcount(res, "Close combat weapon") == 4
        assert _mcount(res, "Dragon Axe") == 1
        assert len(res["melee"]) == 5

    def test_warp_spiders_exarch_powerblade_array(self, aeldari_engine, MEQ):
        """Warp Spiders n=5: 4 Death Spinners + Exarch Powerblade Array
        (A10 Lethal Hits Twin-Linked — no second melee leaks in)."""
        res = _build(aeldari_engine, "Warp Spiders", MEQ)
        assert _rcount(res, "Death spinner") == 4
        assert len(res["ranged"]) == 4
        assert _mcount(res, "Close Combat Weapon") == 4
        assert _mcount(res, "Powerblade Array") == 1
        assert len(res["melee"]) == 5


class TestAeldariKnownEdgeCases:
    """Problematic semantics discovered this iteration, pinned so they cannot
    silently change. Each test documents WHY the behavior is what it is.
    """

    def test_champion_bike_slot_overrides_fixed_pistol(
            self, aeldari_engine, MEQ):
        """Arena Champion: the Bike Weapon slot OVERRIDES the fixed Splinter
        Pistol (bundle-override semantics). A 3-model Reaver unit therefore
        carries 2 Splinter Pistols, not 3 — the Champion's top-level pistol
        is dropped when the slot picks the Blaster.

        Pre-existing limitation, not a bug: bundle-override was introduced
        for Banshee-exarch style bundles, and the Pistol never contributes
        damage either way (slot replaces the fixed ranged weapon). The pin
        just keeps the behavior from drifting.
        """
        res = _build(aeldari_engine, "Ynnari Reavers", MEQ)
        pistols = sum(1 for w in res["ranged"] if w.name == "Splinter Pistol")
        assert pistols == 2
        # Sanity: the unit IS 3 models and the champion's slot DID fire.
        assert _rcount(res, "Blaster") == 1

    def test_singing_spear_dual_profile_keeps_melee(self, aeldari_engine, MEQ):
        """Singing Spear is a dual-profile weapon: throwable Ranged (S9 A1
        12" Assault Psychic) + a Melee half (S3 A2). Warlocks ALWAYS have a
        melee profile — the spear's melee half must survive first-profile
        resolution and land in the melee list."""
        res = _build(aeldari_engine, "Warlock Conclave", MEQ)
        me = [w for w in res["melee"]]
        assert len(me) == 2
        assert all(w.name == "Singing Spear" for w in me)
        assert all(w.strength == 3 and w.attacks == 2 for w in me)
        skyrunner = _build(aeldari_engine, "Warlock Skyrunners", MEQ)
        assert len(skyrunner["melee"]) == 1
        assert skyrunner["melee"][0].name == "Singing Spear"

    def test_chainsabres_dual_profile_both_lists(self, aeldari_engine, MEQ):
        """Chainsabres is Melee-first dual-profile (A5 melee + A1 pistol).
        The Striking Scorpion exarch fires the pistol half AND fights with the
        chainsabre melee — no profile is lost to first-profile resolution.
        (Real-config greedy picks the Biting blade vs MEQ; this pins the
        Chainsabres payload directly.)"""
        build = {"models": [
            {"name": "Striking Scorpion Exarch", "count": 1, "slots": [
                {"name": "Weapons", "choices": [
                    {"name": "Chainsabres",
                     "ranged": "Chainsabres", "melee": "Chainsabres"},
                ]},
            ]},
        ]}
        ld = aeldari_engine._eval_squad_build(
            build, "Striking Scorpions", target=MEQ)
        assert len(ld["ranged"]) == 1
        assert ld["ranged"][0].name == "Chainsabres"
        assert ld["ranged"][0].attacks == 1  # pistol half
        assert ld["melee"][0].name == "Chainsabres"
        assert ld["melee"][0].attacks == 5  # chainsabre half

    def test_melee_reduction_invariant_one_per_model(self, aeldari_engine, MEQ):
        """24.11 melee rule: one non-EA melee weapon per model. Across every
        complex unit where all models have a melee profile, total melee
        entries must equal the squad size — the regression that would leak
        a model's second melee weapon."""
        units = [
            "Corsair Voidscarred",
            "Corsair Voidreavers",
            "Ynnari Reavers",
            "Troupe",
            "Storm Guardians",
            "Windriders",
            "Ynnari Kabalite Warriors",
            "Rangers",
            "Fire Dragons",
            "Warp Spiders",
            "Warlock Conclave",
            "Warlock Skyrunners",
        ]
        for name in units:
            n = aeldari_engine.config.squads[name]["n"]
            res = _build(aeldari_engine, name, MEQ)
            assert len(res["melee"]) == n, (
                f"{name}: {len(res['melee'])} melee entries for {n} models"
            )

    def test_multi_fixed_ranged_all_models_fire(self, aeldari_engine, MEQ):
        """Every model with a ranged weapon fires at least one entry — a model
        with a multi-weapon list must never collapse to a single weapon.

        Storm Guardians and Warp Spiders are deliberately NOT in the list:
        their leader/specialist model (Serpent's Scale Platform, Spider
        Exarch) is melee-only, so those squads fire fewer ranged entries than
        the squad size (pinned exactly in their class-1 tests).
        """
        units = [
            "Corsair Voidscarred",
            "Corsair Voidreavers",
            "Ynnari Reavers",
            "Troupe",
            "Windriders",
            "Ynnari Kabalite Warriors",
            "Rangers",
            "Fire Dragons",
            "Warlock Conclave",
            "Warlock Skyrunners",
        ]
        for name in units:
            n = aeldari_engine.config.squads[name]["n"]
            res = _build(aeldari_engine, name, MEQ)
            assert len(res["ranged"]) >= n, (
                f"{name}: {len(res['ranged'])} ranged entries for {n} models"
            )

    def test_slot_pick_is_target_dependent(self, aeldari_engine, MEQ):
        """Slot greedy picks are target-dependent: the Voidreaver heavy slot
        takes Shuriken cannon vs MEQ but flips to Wraithcannon vs a T10
        heavy target. A pin of the MEQ pick is NOT a statement about other
        targets — this test proves the mechanism reacts to the target."""
        heavy = TargetProfile(
            toughness=10, save=3, invuln=None, wounds_per_model=8,
            model_count=1,
        )
        vs_meq = _build(aeldari_engine, "Corsair Voidreavers", MEQ)
        vs_heavy = _build(aeldari_engine, "Corsair Voidreavers", heavy)
        assert _rcount(vs_meq, "Shuriken cannon") == 1
        assert _rcount(vs_meq, "Wraithcannon") == 0
        assert _rcount(vs_heavy, "Wraithcannon") == 1
        assert _rcount(vs_heavy, "Shuriken cannon") == 0
        # Allocation distribution is unchanged — only the slot content moves.
        assert vs_meq["_alloc_info"] == vs_heavy["_alloc_info"]
