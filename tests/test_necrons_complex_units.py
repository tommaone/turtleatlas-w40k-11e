"""Regression locks for the Necrons squad slot migration.

Locks the regenerated Necrons squads to the BSData truth (verified
2026-08-19 via gen_squad_composition --faction necrons):

Regenerated squads (16, all from flat -> composition builds):
- Alloc parallel variants: Canoptek Macrocytes (atomiser/scalpel/tesla/
  mandible alloc), Canoptek Wraiths (claws/beamer/caster/coils variants),
  Lokhust Heavy Destroyers (enmitic/gauss alloc), Necron Warriors
  (flayer/reaper alloc)
- Per-model slots: Canoptek Tomb Crawlers (Weapon choice), Immortals
  (Weapons), Lychguard (Weapons), Tomb Blades (Weapon), Triarch
  Praetorians (Weapons)
- Flat (single base model, no variants): Canoptek Scarab Swarms,
  Cryptothralls, Deathmarks, Flayed Ones, Lokhust Destroyers,
  Ophydian Destroyers, Skorpekh Destroyers

STRUCTURE ONLY — no damage values. The engine is the single source of
computation; this test locks the config shape and resolvability, not math.

Run: python3 -m pytest tests/test_necrons_complex_units.py -v
"""

import json
import sys
from pathlib import Path
from collections import Counter

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.ranking import RankingEngine

CONFIG_DIR = Path(__file__).resolve().parent.parent / "data" / "config"
SQUADS_PATH = CONFIG_DIR / "necrons" / "squads.json"

TARGET_SAMPLES = ["GEQ", "MEQ", "TEQ"]


@pytest.fixture(scope="module")
def necrons_engine():
    return RankingEngine("necrons")


@pytest.fixture(scope="module")
def squads():
    return json.load(open(SQUADS_PATH))


def _build(engine, name, target):
    res = engine._best_squad_variant(name, target)
    assert res is not None, f"{name} did not resolve against {target}"
    return res


def _rcount(res, name):
    return Counter(w.name for w in res["ranged"])[name]


def _mcount(res, name):
    return Counter(w.name for w in res["melee"])[name]


def _model(squads, unit, model_name) -> dict:
    build = squads[unit]["builds"][0]
    return next(m for m in build["models"] if m["name"] == model_name)


def _alloc(squads, unit, model_name):
    m = _model(squads, unit, model_name)
    return {a["name"]: a for a in m["alloc"]}


class TestAllocSquads:
    """Squads with parallel-variant alloc pools."""

    def test_canoptek_macrocytes_alloc(self, squads):
        m = _model(squads, "Canoptek Macrocytes", "Canoptek Macrocyte")
        assert m["count"] == 5
        alloc = _alloc(squads, "Canoptek Macrocytes", "Canoptek Macrocyte")
        # MEQ picks gauss scalpel (S6 D2), TEQ picks tesla caster (S7 D2)
        assert alloc["Canoptek Macrocyte w/ gauss scalpel"]["max"] == 5
        assert alloc["Canoptek Macrocyte w/ tesla caster"]["max"] == 5
        assert alloc["Canoptek Macrocyte w/ atomiser beam"]["max"] == 1
        assert alloc["Canoptek Macrocyte w/ accelerator mandible"]["max"] == 1

    def test_canoptek_wraiths_alloc(self, squads):
        m = _model(squads, "Canoptek Wraiths", "Wraith")
        assert m["count"] == 3
        alloc = _alloc(squads, "Canoptek Wraiths", "Wraith")
        # GEQ picks coils, MEQ picks claws/caster, TEQ picks claws/caster
        assert alloc["Wraith w/ claws and particle caster"]["max"] == 3
        assert alloc["Wraith w/ coils and particle caster"]["max"] == 3
        assert alloc["Wraith w/ claws"]["max"] == 3
        assert alloc["Wraith w/ coils"]["max"] == 3

    def test_lokhust_heavy_destroyers_alloc(self, squads):
        m = _model(squads, "Lokhust Heavy Destroyers", "Destroyer")
        assert m["count"] == 1
        alloc = _alloc(squads, "Lokhust Heavy Destroyers", "Destroyer")
        assert alloc["Destroyer w/ gauss destructor"]["max"] == 1
        assert alloc["Destroyer w/ enmitic exterminator"]["max"] == 1

    def test_necron_warriors_alloc(self, squads):
        m = _model(squads, "Necron Warriors", "Warrior")
        assert m["count"] == 10
        alloc = _alloc(squads, "Necron Warriors", "Warrior")
        assert alloc["Warrior w/ gauss flayer"]["max"] == 10
        assert alloc["Warrior w/ gauss reaper"]["max"] == 10


class TestSlotSquads:
    """Squads with per-model weapon slots."""

    def test_canoptek_tomb_crawlers_slots(self, squads):
        build = squads["Canoptek Tomb Crawlers"]["builds"][0]
        # Two models: one fixed (no slots), one with the weapon choice slot
        slotted = [m for m in build["models"] if "slots" in m]
        assert len(slotted) == 1
        slot = {s["name"]: {c["name"] for c in s["choices"]}
                for s in slotted[0]["slots"]}
        assert slot["Weapon choice"] == {"Twin gauss reaper", "Dimensional isolator"}

    def test_immortals_weapon_slot(self, squads):
        m = _model(squads, "Immortals", "Immortal")
        slot = {s["name"]: {c["name"] for c in s["choices"]}
                for s in m["slots"]}
        assert slot["Weapons"] == {"Gauss blaster", "Tesla carbine"}

    def test_lychguard_weapon_slot(self, squads):
        m = _model(squads, "Lychguard", "Lychguard")
        slot = {s["name"]: {c["name"] for c in s["choices"]}
                for s in m["slots"]}
        assert slot["Weapons"] == {"Warscythe", "Hyperphase sword and dispersion shield"}

    def test_tomb_blades_weapon_slot(self, squads):
        m = _model(squads, "Tomb Blades", "Tomb Blade")
        slot = {s["name"]: {c["name"] for c in s["choices"]}
                for s in m["slots"]}
        assert slot["Weapon"] == {"Twin gauss blaster", "Particle beamer", "Twin tesla carbine"}

    def test_triarch_praetorians_weapon_slot(self, squads):
        m = _model(squads, "Triarch Praetorians", "Triarch Praetorian")
        slot = {s["name"]: {c["name"] for c in s["choices"]}
                for s in m["slots"]}
        assert slot["Weapons"] == {"Rod of covenant", "Particle caster and voidblade"}


class TestResolvedLoadouts:
    """Pin exact resolved loadouts against MEQ target."""

    def test_macrocytes_meq(self, necrons_engine, MEQ):
        res = _build(necrons_engine, "Canoptek Macrocytes", MEQ)
        assert _rcount(res, "Gauss scalpel") == 4
        assert _rcount(res, "Atomiser beam") == 1
        assert _mcount(res, "Claws") == 5
        assert len(res["ranged"]) == 5
        assert len(res["melee"]) == 5

    def test_wraiths_meq(self, necrons_engine, MEQ):
        res = _build(necrons_engine, "Canoptek Wraiths", MEQ)
        assert _rcount(res, "Particle caster") == 3
        assert _mcount(res, "Vicious claws") == 3
        assert len(res["ranged"]) == 3
        assert len(res["melee"]) == 3

    def test_warriors_meq(self, necrons_engine, MEQ):
        res = _build(necrons_engine, "Necron Warriors", MEQ)
        assert _rcount(res, "Gauss reaper") == 10
        assert _mcount(res, "Close combat weapon") == 10
        assert len(res["ranged"]) == 10
        assert len(res["melee"]) == 10

    def test_immortals_meq(self, necrons_engine, MEQ):
        res = _build(necrons_engine, "Immortals", MEQ)
        assert _rcount(res, "Gauss blaster") == 5
        assert _mcount(res, "Close combat weapon") == 5

    def test_lychguard_meq(self, necrons_engine, MEQ):
        res = _build(necrons_engine, "Lychguard", MEQ)
        assert _mcount(res, "Warscythe") == 5
        assert len(res["ranged"]) == 0  # melee-only
        assert len(res["melee"]) == 5

    def test_tomb_blades_meq(self, necrons_engine, MEQ):
        res = _build(necrons_engine, "Tomb Blades", MEQ)
        assert _rcount(res, "Particle beamer") == 3
        assert _mcount(res, "Close combat weapon") == 3

    def test_triarch_praetorians_meq(self, necrons_engine, MEQ):
        res = _build(necrons_engine, "Triarch Praetorians", MEQ)
        assert _rcount(res, "Rod of covenant") == 5
        assert _mcount(res, "Rod of covenant") == 5
        assert len(res["ranged"]) == 5
        assert len(res["melee"]) == 5

    def test_deathmarks_meq(self, necrons_engine, MEQ):
        res = _build(necrons_engine, "Deathmarks", MEQ)
        assert _rcount(res, "Synaptic disintegrator") == 5
        assert _mcount(res, "Close combat weapon") == 5

    def test_flayed_ones_meq(self, necrons_engine, MEQ):
        res = _build(necrons_engine, "Flayed Ones", MEQ)
        assert len(res["ranged"]) == 0  # melee-only
        assert _mcount(res, "Flayer claws") == 5
        assert len(res["melee"]) == 5

    def test_scarab_swarms_meq(self, necrons_engine, MEQ):
        res = _build(necrons_engine, "Canoptek Scarab Swarms", MEQ)
        assert len(res["ranged"]) == 0
        assert _mcount(res, "Feeder mandibles") == 3
        assert len(res["melee"]) == 3

    def test_cryptothralls_meq(self, necrons_engine, MEQ):
        res = _build(necrons_engine, "Cryptothralls", MEQ)
        assert _rcount(res, "Scouring eye") == 2
        assert _mcount(res, "Scythed limbs") == 2

    def test_lokhust_destroyers_meq(self, necrons_engine, MEQ):
        res = _build(necrons_engine, "Lokhust Destroyers", MEQ)
        assert _rcount(res, "Gauss cannon") == 1
        assert _mcount(res, "Close combat weapon") == 1

    def test_lokhust_heavy_meq(self, necrons_engine, MEQ):
        res = _build(necrons_engine, "Lokhust Heavy Destroyers", MEQ)
        assert _rcount(res, "Enmitic exterminator") == 1
        assert _mcount(res, "Close combat weapon") == 1

    def test_ophydian_destroyers_meq(self, necrons_engine, MEQ):
        res = _build(necrons_engine, "Ophydian Destroyers", MEQ)
        assert len(res["ranged"]) == 0
        assert _mcount(res, "Ophydian hyperphase weapons") == 3

    def test_skorpekh_destroyers_meq(self, necrons_engine, MEQ):
        res = _build(necrons_engine, "Skorpekh Destroyers", MEQ)
        assert len(res["ranged"]) == 0
        assert _mcount(res, "Skorpekh hyperphase weapons") == 3


class TestTargetDependentPicks:
    """Slot/alloc picks that change based on target."""

    def test_macrocytes_teq_picks_tesla(self, necrons_engine, TEQ):
        """vs TEQ the Tesla caster (S7) beats Gauss scalpel (S6)."""
        res = _build(necrons_engine, "Canoptek Macrocytes", TEQ)
        assert _rcount(res, "Tesla caster") == 4
        assert _rcount(res, "Atomiser beam") == 1

    def test_wraiths_geq_picks_coils(self, necrons_engine, GEQ):
        """vs GEQ the whip coils (extra attacks) win over claws."""
        res = _build(necrons_engine, "Canoptek Wraiths", GEQ)
        assert _mcount(res, "Whip coils") == 3
        assert _mcount(res, "Vicious claws") == 0

    def test_warriors_teq_picks_flayer(self, necrons_engine, TEQ):
        """vs TEQ the gauss flayer (24" range, same S) beats reaper."""
        res = _build(necrons_engine, "Necron Warriors", TEQ)
        assert _rcount(res, "Gauss flayer") == 10

    def test_lychguard_geq_picks_sword(self, necrons_engine, GEQ):
        """vs GEQ the hyperphase sword (more attacks) beats warscythe."""
        res = _build(necrons_engine, "Lychguard", GEQ)
        assert _mcount(res, "Hyperphase sword") == 5

    def test_immortals_geq_picks_tesla(self, necrons_engine, GEQ):
        """vs GEQ the Tesla carbine (sustained hits) wins over gauss."""
        res = _build(necrons_engine, "Immortals", GEQ)
        assert _rcount(res, "Tesla carbine") == 5

    def test_tomb_crawlers_meq_split(self, necrons_engine, MEQ):
        """Tomb Crawlers have 2 models with the same slot; MEQ picks one
        reaper and one isolator (different targets may differ)."""
        res = _build(necrons_engine, "Canoptek Tomb Crawlers", MEQ)
        ranged = Counter(w.name for w in res["ranged"])
        # At least one of each weapon type across 2 crawlers
        assert ranged["Twin gauss reaper"] + ranged["Dimensional isolator"] == 2
        assert _mcount(res, "Claws") == 2


class TestAllSquadsResolve:
    """Every squad resolves against all target samples."""

    def test_every_squad_resolves(self, necrons_engine, squads):
        for name in squads:
            if name.startswith("_"):
                continue
            for t in TARGET_SAMPLES:
                target = necrons_engine.resolve_target(t)
                res = necrons_engine._best_squad_variant(name, target)
                assert res is not None, f"{name} {t}: did not resolve"
                assert res.get("ranged") or res.get("melee"), f"{name} {t}: empty"


class TestMeleeReduction:
    """Melee reduction invariant: one non-EA weapon per model."""

    def test_melee_count_equals_model_count(self, necrons_engine, squads):
        for name in squads:
            if name.startswith("_"):
                continue
            n = squads[name]["n"]
            for t in TARGET_SAMPLES:
                target = necrons_engine.resolve_target(t)
                res = necrons_engine._best_squad_variant(name, target)
                if res is None:
                    continue
                assert len(res["melee"]) == n, (
                    f"{name} {t}: {len(res['melee'])} melee entries for {n} models"
                )


class TestSeraptekHeavyConstruct:
    """Golden follow-up (2026-08-24): datasheet grants 2 singularity
    generators, replaceable with 2 synaptic obliterators AND 2 transdimensional
    projectors (wahapedia 11ed). The old single-slot choices resolved as
    SINGLE profiles; a 4-weapon bundle cannot be one slot choice, so the
    mutually exclusive options are modelled as two builds.

    STRUCTURE + COUNT only."""

    def test_default_build_two_generators(self, necrons_engine, MEQ):
        res = necrons_engine.resolve_loadout("Seraptek Heavy Construct", MEQ,
                                             mode="default")
        assert res is not None
        _pts, ranged, _m, _i, _info = res
        names = Counter(w.name for w in ranged)
        assert names["Singularity generator"] == 2, dict(names)

    def test_swap_build_two_plus_two(self, necrons_engine, MEQ):
        res = necrons_engine.resolve_loadout(
            "Seraptek Heavy Construct", MEQ,
            mode="Synaptic obliterators & transdimensional projectors")
        assert res is not None
        _pts, ranged, _m, _i, _info = res
        names = Counter(w.name for w in ranged)
        assert names["Synaptic obliterator"] == 2, dict(names)
        assert names["Transdimensional projector"] == 2, dict(names)

    def test_best_of_builds_never_single_profile(self, necrons_engine, MEQ):
        res = necrons_engine.resolve_loadout("Seraptek Heavy Construct", MEQ)
        assert res is not None
        _pts, ranged, _m, _i, _info = res
        names = Counter(w.name for w in ranged)
        for n, c in names.items():
            if "generator" in n.lower():
                assert c == 2, f"under-counted {n}: {dict(names)}"
            if "obliterator" in n.lower() or "projector" in n.lower():
                assert c == 2, f"under-counted {n}: {dict(names)}"
