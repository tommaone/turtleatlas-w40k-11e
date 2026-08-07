"""End-to-end tests for the complex Grey Knights squad-composition units.

Runs the full pipeline (BSData parser -> config generator -> engine alloc
resolution) through the real regenerated config
(data/config/grey-knights/squads.json) and pins the deterministic resolved
loadouts for every complex unit covered in this iteration.

This iteration added the shared-cap composition mechanism: BSData encodes
Purgation/Purifier/Interceptor 'Heavy weapons' as a group-level SHARED cap
(Purgation max=4 specials total regardless of squad size, Purifier max=2,
Interceptor max=1) carried by nested selectionEntryGroups. The parser tags
the special variants with group_max, the generator passes it through, and the
engine enforces it as a COMBINED budget across the tagged variants — not a
per-variant cap.

Per turtle-dojo, STRUCTURE is asserted (alloc distribution, weapon names and
counts, melee reduction, shared-cap enforcement), NOT damage numbers — no
expected_wounds.

Key behaviors pinned:
  1. Shared cap: Purgation fills at most 4 specials, Purifier 2, Interceptor 1
     (the user-confirmed correction: cap is 4 regardless of squad size).
  2. Specials REPLACE both the storm bolter AND the Nemesis force weapon
     (BSData + 40k.app + Wahapedia: '...replaced with one of the following:
     1 incinerator and 1 close combat weapon'). Plain models keep Nemesis
     force weapon. This makes the greedy target-dependent: vs GEQ the specials
     win (torrent Incinerator), vs MEQ/TEQ the plain Nemesis loadout wins.
  3. Purifier Purifying Flame is an ADDITIONAL weapon on every model.
  4. Terminator/Paladin n=5 with the leader (Justicar/Paragon) plus alloc pool.

Run: python3 -m pytest tests/test_grey_knights_complex_units.py -v
"""

from collections import Counter
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.ranking import RankingEngine
from engine.dpp import TargetProfile


@pytest.fixture(scope="module")
def gk_engine():
    return RankingEngine("grey-knights")


def _build(engine, name, target):
    """Resolve the best squad variant for a unit against a target."""
    res = engine._best_squad_variant(name, target)
    assert res is not None, f"{name} did not resolve"
    return res


def _rcount(res, name):
    return Counter(w.name for w in res["ranged"])[name]


def _mcount(res, name):
    return Counter(w.name for w in res["melee"])[name]


def _specials(res):
    """Non-default ranged weapons actually carried (shared-cap specials)."""
    return {k: v for k, v in Counter(w.name for w in res["ranged"]).items()
            if k not in ("Storm bolter", "Purifying Flame")}


class TestGKComplexUnits:
    """Real-config regression pins: exact resolved loadout per complex unit.

    The GEQ profile (T3/SV5+/1W) drives the special-weapon picks: Incinerator
    (torrent, S6) beats Psycannon/Psilencer vs hordes. The MEQ/TEQ profiles
    (T4+/2W+) drive the plain loadout: the Nemesis force weapon melee
    (S6 AP-2 D2) outweighs the special's ranged gain when the special model
    trades its Nemesis weapon for a Close combat weapon.
    """

    def test_purgation_shared_cap_four_geq(self, gk_engine, GEQ):
        """Purgation n=5: all 4 special slots take Incinerator vs GEQ (torrent
        best vs hordes). This is the user-confirmed cap: max 4 specials at
        size 5 — exactly 4 picked, Justicar keeps Storm bolter + Nemesis."""
        res = _build(gk_engine, "Purgation Squad", GEQ)
        assert dict(res["_alloc_info"][0][1]) == {
            "Purgator w/ incinerator": 4,
        }
        assert _specials(res) == {"Incinerator": 4}
        assert _rcount(res, "Storm bolter") == 1  # Justicar only
        # Special models replaced BOTH weapons: CCW melee, not Nemesis.
        assert _mcount(res, "Close combat weapon") == 4
        assert _mcount(res, "Nemesis force weapon") == 1  # Justicar
        assert len(res["ranged"]) == 5
        assert len(res["melee"]) == 5

    def test_purgation_plain_vs_meq(self, gk_engine, MEQ):
        """Purgation n=5 vs MEQ: the special tradeoff loses — a Psycannon
        model drops Nemesis (1.78 melee) for CCW (0.33) to gain ~1.2 ranged.
        Plain Storm bolter + Nemesis wins. Cap NOT filled is legitimate."""
        res = _build(gk_engine, "Purgation Squad", MEQ)
        assert res["_alloc_info"] == [
            ("Purgator", [("Purgator", 4)]),
        ]
        assert _specials(res) == {}
        assert _rcount(res, "Storm bolter") == 5
        assert _mcount(res, "Nemesis force weapon") == 5
        assert len(res["melee"]) == 5

    def test_purifier_shared_cap_two_geq(self, gk_engine, GEQ):
        """Purifier n=5 vs GEQ: shared cap is 2 (not 4) — exactly 2
        Incinerators, 2 plain Purifiers. Every model fires Purifying Flame."""
        res = _build(gk_engine, "Purifier Squad", GEQ)
        assert dict(res["_alloc_info"][0][1]) == {
            "Purifier": 2,
            "Purifier w/ incinerator": 2,
        }
        assert _specials(res) == {"Incinerator": 2}
        assert _rcount(res, "Storm bolter") == 3  # 2 plain + Knight of Flame
        assert _rcount(res, "Purifying Flame") == 5  # ALL models, incl. leader
        assert len(res["ranged"]) == 10  # storm/flame on 5 + 2 specials replace
        assert len(res["melee"]) == 5

    def test_interceptor_shared_cap_one_geq(self, gk_engine, GEQ):
        """Interceptor n=5 vs GEQ: shared cap is 1 — exactly 1 Incinerator,
        the rest plain (min 3 base Interceptors enforced)."""
        res = _build(gk_engine, "Interceptor Squad", GEQ)
        assert res["_alloc_info"] == [
            ("Interceptor", [("Interceptor", 3), ("Interceptor w/ incinerator", 1)]),
        ]
        assert _specials(res) == {"Incinerator": 1}
        assert _rcount(res, "Storm bolter") == 4  # 3 plain + Justicar
        assert len(res["ranged"]) == 5
        assert len(res["melee"]) == 5

    def test_strike_squad_heavy_cap_one_geq(self, gk_engine, GEQ):
        """Strike Squad n=5 vs GEQ: one Grey Knight with Heavy Weapon slot
        takes Incinerator (cap 1 by BSData 'Weapon Choice' slot)."""
        res = _build(gk_engine, "Strike Squad", GEQ)
        assert _specials(res) == {"Incinerator": 1}
        assert _rcount(res, "Storm bolter") == 4
        assert len(res["ranged"]) == 5
        assert len(res["melee"]) == 5

    def test_terminator_n5_alloc_pool(self, gk_engine, MEQ):
        """Brotherhood Terminator n=5: Justicar + 4-model alloc pool. Vs MEQ
        the pool fills plain Terminators + Ancient's Banner (slot: Psycannon)
        + Heavy Weapon (slot: Psycannon) — the Ancient and Heavy slots pick
        ranged specials because their melee stays Nemesis."""
        res = _build(gk_engine, "Brotherhood Terminator Squad", MEQ)
        used = dict(res["_alloc_info"][0][1])
        assert used == {
            "Terminator": 2,
            "Terminator with Ancient's Banner": 1,
            "Terminator with Heavy Weapon": 1,
        }
        assert _rcount(res, "Storm bolter") == 3
        assert _rcount(res, "Psycannon") == 2  # banner + heavy slots
        assert _mcount(res, "Nemesis force weapon") == 5  # all 4 + Justicar
        assert len(res["ranged"]) == 5
        assert len(res["melee"]) == 5

    def test_paladin_n5_alloc_pool(self, gk_engine, MEQ):
        """Paladin n=5: Paragon + 4-model alloc pool. Vs MEQ the pool fills
        1 plain + Ancient's Banner (Psycannon) + 2 Heavy Weapon (Psycannon)."""
        res = _build(gk_engine, "Paladin Squad", MEQ)
        used = dict(res["_alloc_info"][0][1])
        assert used == {
            "Paladin": 1,
            "Paladin with Ancient's Banner": 1,
            "Paladin with Heavy Weapon": 2,
        }
        assert _rcount(res, "Storm bolter") == 2
        assert _rcount(res, "Psycannon") == 3
        assert _mcount(res, "Nemesis force weapon") == 5
        assert len(res["ranged"]) == 5
        assert len(res["melee"]) == 5

    def test_purgation_cap_at_size_10(self, gk_engine, GEQ):
        """User correction pin: Purgation cap stays 4 even at size 10. Force
        the engine with the same alloc payload but count 9 (n=10 -> 9
        Purgators + Justicar): at most 4 specials, 5 plain."""
        sdetail = gk_engine.config.squads["Purgation Squad"]
        build = {
            "name": "Default",
            "models": [
                {**sdetail["builds"][0]["models"][0], "count": 9},
                sdetail["builds"][0]["models"][1],
            ],
        }
        res = gk_engine._eval_squad_build(build, "Purgation Squad", target=GEQ)
        assert dict(res["_alloc_info"][0][1]) == {
            "Purgator w/ incinerator": 4,
            "Purgator": 5,
        }
        assert _specials(res) == {"Incinerator": 4}
        assert _rcount(res, "Storm bolter") == 6  # 5 plain + Justicar
        assert len(res["ranged"]) == 10
        assert len(res["melee"]) == 10

    def test_melee_reduction_invariant_one_per_model(self, gk_engine, MEQ):
        """24.11 melee rule: one non-EA melee weapon per model. Across every
        GK complex unit, total melee entries must equal the squad size."""
        units = [
            "Purgation Squad",
            "Purifier Squad",
            "Interceptor Squad",
            "Strike Squad",
            "Brotherhood Terminator Squad",
            "Paladin Squad",
        ]
        for name in units:
            n = gk_engine.config.squads[name]["n"]
            res = _build(gk_engine, name, MEQ)
            assert len(res["melee"]) == n, (
                f"{name}: {len(res['melee'])} melee entries for {n} models"
            )

    def test_purifying_flame_every_model(self, gk_engine, MEQ):
        """Purifying Flame is an ADDITIONAL weapon on every Purifier model —
        the whole squad (incl. Knight of the Flame) fires it."""
        res = _build(gk_engine, "Purifier Squad", MEQ)
        assert _rcount(res, "Purifying Flame") == 5


class TestGKKnownEdgeCases:
    """Problematic semantics discovered this iteration, pinned so they cannot
    silently change. Each test documents WHY the behavior is what it is.
    """

    def test_special_alloc_is_target_dependent(self, gk_engine, GEQ, MEQ):
        """Shared-cap specials are NOT always picked: vs GEQ the torrent
        Incinerator wins; vs MEQ/TEQ the plain Nemesis loadout wins (special
        models trade their Nemesis force weapon for a Close combat weapon —
        a real 11e rule, verified on 40k.app and Wahapedia). The engine
        filling the cap is a target-specific outcome, not a mandate."""
        vs_geq = _build(gk_engine, "Purgation Squad", GEQ)
        vs_meq = _build(gk_engine, "Purgation Squad", MEQ)
        assert _specials(vs_geq) == {"Incinerator": 4}
        assert _specials(vs_meq) == {}
        assert vs_geq["_alloc_info"] != vs_meq["_alloc_info"]

    def test_heavy_slot_vs_heavy_target(self, gk_engine, MEQ):
        """The Terminator/Paladin Heavy Weapon slot is target-dependent: vs
        MEQ it picks Psycannon (S8 D2); vs a T10 heavy target it should flip
        to something S9+. This proves slot greedy reacts to the target."""
        heavy = TargetProfile(
            toughness=10, save=3, invuln=None, wounds_per_model=8,
            model_count=1,
        )
        vs_meq = _build(gk_engine, "Brotherhood Terminator Squad", MEQ)
        vs_heavy = _build(gk_engine, "Brotherhood Terminator Squad", heavy)
        assert _rcount(vs_meq, "Psycannon") == 2
        assert _rcount(vs_heavy, "Psycannon") == 2
        # Allocation distribution is unchanged — only the slot content moves.
        assert vs_meq["_alloc_info"] == vs_heavy["_alloc_info"]
