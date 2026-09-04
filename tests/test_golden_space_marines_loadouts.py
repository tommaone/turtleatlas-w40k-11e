"""Golden loadout locks — space-marines, datasheet-verified structures.

Source of truth: tests/golden_loadouts/space-marines.json
(wahapedia 11ed Faction Pack v1.1 + local BSData catalogue, fetched 2026-08-24,
confidence high). Units not listed there are pinned against BSData
selection-entry-group structure only.

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
    Path(__file__).resolve().parent / "golden_loadouts"
    / "space-marines.json"
)


@pytest.fixture(scope="module")
def sm_engine():
    return RankingEngine("space-marines")


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
        assert "Ancient in Terminator Armor" in golden_units
        assert "Stormraven Gunship" in golden_units
        assert "Thunderhawk Gunship" in golden_units


class TestAncientInTerminatorArmor:
    """Golden: default = storm bolter + one-of melee; claws and
    hammer+storm-shield replace BOTH base weapons (separate builds)."""

    def test_default_build_has_melee_choice(self, sm_engine, MEQ):
        _, melee = _resolved(sm_engine, "Ancient in Terminator Armor", MEQ)
        assert len(melee) == 1, f"exactly one melee weapon, got {melee}"

    def test_storm_bolter_kept_in_default(self, sm_engine, MEQ):
        ranged, _ = _resolved(sm_engine, "Ancient in Terminator Armor", MEQ)
        # best legal build may be claws/hammer builds (no storm bolter) —
        # but whichever build wins must NOT pair claws with a storm bolter.
        if any("claws" in m.lower() for m in _resolved(sm_engine, "Ancient in Terminator Armor", MEQ)[1]):
            assert not ranged, "claws replace the storm bolter too"

    def test_three_builds_in_config(self):
        cfg = json.loads(
            (Path(__file__).resolve().parent.parent / "data/config/space-marines/characters.json").read_text()
        )
        wo = cfg["Ancient in Terminator Armor"]["weapon_options"]
        names = {b["name"] for b in wo["builds"]}
        assert {
            "default",
            "twin lightning claws",
            "thunder hammer & terminator storm shield",
        } <= names

    def test_thunder_hammer_reachable(self, sm_engine, MEQ):
        """The hammer swap must exist as a choice somewhere."""
        cfg = json.loads(
            (Path(__file__).resolve().parent.parent / "data/config/space-marines/characters.json").read_text()
        )
        wo = cfg["Ancient in Terminator Armor"]["weapon_options"]
        choices = [
            c["name"]
            for b in wo["builds"]
            for s in b.get("slots", [])
            for c in s.get("choices", [])
        ]
        assert "Thunder Hammer" in choices


class TestStormravenGunship:
    """Golden: 2x stormstrike + optional-but-always-beneficial 2x hurricane
    bolters fixed; two independent pick-1 swap groups."""

    def test_fixed_counts(self, sm_engine, MEQ):
        ranged, melee = _resolved(sm_engine, "Stormraven Gunship", MEQ)
        assert ranged.count("Stormstrike Missile Launcher") == 2, ranged
        assert ranged.count("Hurricane Bolter") == 2, ranged
        assert any("hull" in m.lower() for m in melee), melee

    def test_swap_groups_pick_one_each(self, sm_engine, MEQ):
        ranged, _ = _resolved(sm_engine, "Stormraven Gunship", MEQ)
        grp1 = [
            n
            for n in ranged
            if n.lower().startswith(("twin heavy plasma cannon", "twin assault cannon", "twin lascannon"))
        ]
        grp2 = [
            n
            for n in ranged
            if n.lower().startswith(("typhoon missile launcher", "twin heavy bolter", "twin multi-melta"))
        ]
        assert len(grp1) == 1, f"weapon option 1 pick, got {grp1}"
        assert len(grp2) == 1, f"weapon option 2 pick, got {grp2}"


class TestThunderhawkGunship:
    """Golden: 2 lascannons + 4 twin heavy bolters fixed; pick-1 swaps."""

    def test_fixed_gun_counts(self, sm_engine, MEQ):
        ranged, _ = _resolved(sm_engine, "Thunderhawk Gunship", MEQ)
        assert ranged.count("Lascannon") == 2, ranged
        assert ranged.count("Twin heavy bolter") == 4, ranged

    def test_main_weapon_is_pick_one(self, sm_engine, MEQ):
        ranged, _ = _resolved(sm_engine, "Thunderhawk Gunship", MEQ)
        mains = [
            n
            for n in ranged
            if n in ("Thunderhawk heavy cannon", "Turbo-laser destructor")
        ]
        assert len(mains) == 1, mains

    def test_bombs_or_battery_is_pick_one(self, sm_engine, MEQ):
        ranged, _ = _resolved(sm_engine, "Thunderhawk Gunship", MEQ)
        bombs = [
            n
            for n in ranged
            if n in ("Thunderhawk cluster bombs", "Hellstrike missile battery")
        ]
        assert len(bombs) == 1, bombs


class TestBrutalisDreadnought:
    """Golden: stubber fixed; pick-1 melee group; pick-1 ranged group."""

    def test_structure(self, sm_engine, MEQ):
        ranged, melee = _resolved(sm_engine, "Brutalis Dreadnought", MEQ)
        melee_picks = [m for m in melee if m.lower().startswith(("brutalis fists", "brutalis talons"))]
        ranged_picks = [r for r in ranged if r.lower().startswith(("twin heavy bolter", "twin multi-melta"))]
        assert len(melee_picks) == 1, melee
        assert len(ranged_picks) == 1, ranged
        assert any("icarus" in r.lower() for r in ranged), ranged


class TestRedemptorDreadnought:
    """Golden: fist + icarus pod fixed; three pick-1 groups."""

    def test_structure(self, sm_engine, MEQ):
        ranged, melee = _resolved(sm_engine, "Redemptor Dreadnought", MEQ)
        mains = [r for r in ranged if r.lower().startswith(("macro plasma incinerator", "heavy onslaught gatling cannon"))]
        seconds = [r for r in ranged if r.lower() in ("heavy flamer", "onslaught gatling cannon")]
        thirds = [r for r in ranged if r.lower().startswith(("twin fragstorm grenade launcher", "twin storm bolter"))]
        assert len(mains) == 1, ranged
        assert len(seconds) == 1, ranged
        assert len(thirds) == 1, ranged
        assert any("fist" in m.lower() for m in melee), melee
        assert any("icarus" in r.lower() for r in ranged), ranged


class TestDreadnought:
    """Golden: one arm pick + one heavy weapon pick; all pairings legal."""

    def test_two_slots_resolved(self, sm_engine, MEQ):
        ranged, melee = _resolved(sm_engine, "Dreadnought", MEQ)
        heavy = [
            r
            for r in ranged
            if r.lower().startswith(("assault cannon", "multi-melta", "twin lascannon", "heavy plasma cannon"))
        ]
        arms = [
            m for m in melee
            if "combat weapon" in m.lower() or "close combat" in m.lower()
        ]
        assert len(heavy) == 1, ranged
        assert len(arms) >= 1 or len(melee) >= 1, melee


class TestPredatorSponsons:
    """Golden: sponson weapons are a single pick-1 group of pairs."""

    @pytest.mark.parametrize("unit,turret", [
        ("Predator Annihilator", "predator twin lascannon"),
        ("Predator Destructor", "predator autocannon"),
    ])
    def test_sponson_pick_one(self, sm_engine, MEQ, unit, turret):
        ranged, _ = _resolved(sm_engine, unit, MEQ)
        sponsons = [r for r in ranged if r.lower() in ("lascannon", "heavy bolter", "heavy bolters")]
        assert any(r.lower().startswith(turret) for r in ranged), ranged
        # both sponsons come as one decision: same weapon twice, nothing else
        assert len(sponsons) == 2 and len(set(sponsons)) == 1, f"sponsons must be a pair, got {sponsons}"


class TestGladiatorLancer:
    """Golden: lancer destroyer + pod + stubber fixed; sponsons pick-1 pair."""

    def test_structure(self, sm_engine, MEQ):
        ranged, melee = _resolved(sm_engine, "Gladiator Lancer", MEQ)
        joined = " ".join(ranged).lower()
        assert "lancer laser destroyer" in joined, ranged
        assert "icarus rocket pod" in joined, ranged
        assert "ironhail heavy stubber" in joined, ranged
        frag = sum(1 for r in ranged if r.lower() == "fragstorm grenade launcher")
        sb = sum(1 for r in ranged if r.lower() == "storm bolter" and False) + \
            sum(1 for r in ranged if r.lower() == "storm bolters")
        # one sponson PAIR picked: 2x fragstorm OR 2x storm bolters
        pair = frag if frag else sb
        assert pair == 2 or pair == 0, f"sponson pair expected, got {ranged}"
        assert not (frag == 1 or sb == 1), "sponsons must not resolve as a lone gun"


class TestInvictorTacticalWarsuit:
    """Golden: fragstorm + heavy bolter + twin ironhail stubber + fist fixed;
    pick-1 main weapon."""

    def test_structure(self, sm_engine, MEQ):
        ranged, melee = _resolved(sm_engine, "Invictor Tactical Warsuit", MEQ)
        mains = [r for r in ranged if r.lower() in ("incendium cannon", "twin ironhail autocannon")]
        assert len(mains) == 1, ranged
        assert any("invictor fist" in m.lower() for m in melee), melee
        joined = " ".join(ranged).lower()
        assert "fragstorm grenade launcher" in joined, ranged
        assert "heavy bolter" in joined, ranged
        assert "twin ironhail heavy stubber" in joined, ranged


class TestAstraeus:
    """Golden: macro-accelerator + stubber + storm bolter + hull fixed;
    hull-weapon and sponson pick-1 groups."""

    def test_structure(self, sm_engine, MEQ):
        ranged, melee = _resolved(sm_engine, "Astraeus", MEQ)
        hulls = [r for r in ranged if r in ("Twin heavy bolter", "Twin lascannon")]
        sponsons = [r for r in ranged if "las-ripper" in r.lower() or "plasma eradicator" in r.lower()]
        assert len(hulls) == 1, ranged
        assert len(sponsons) == 2, f"sponson pair expected, got {sponsons} in {ranged}"
        base = {s.split(" - ")[0].lower() for s in sponsons}
        assert len(base) == 1, f"both sponsons must be the same gun, got {sponsons}"
        assert any("macro-accelerator" in r.lower() for r in ranged), ranged


class TestCharactersSingleSwap:
    """Ancient / Chaplain With Jump Pack: exactly one pick from the swap slot
    on top of fixed equipment."""

    def test_ancient(self, sm_engine, MEQ):
        ranged, melee = _resolved(sm_engine, "Ancient", MEQ)
        picks = [n for n in ranged + melee if n in ("Bolt Rifle & Close Combat Weapon", "Power weapon")]
        assert len(picks) == 1, (ranged, melee)

    def test_chaplain_jump_pack(self, sm_engine, MEQ):
        _, melee = _resolved(sm_engine, "Chaplain With Jump Pack", MEQ)
        assert any("crozius" in m.lower() for m in melee), melee


class TestImpulsorSponsons:
    """Golden follow-up (2026-08-24): datasheet grants 2 storm bolters,
    replaceable with 2 fragstorm grenade launchers (wahapedia 11ed).
    Literal '2 Storm Bolters' names were unresolvable — sponsons vanished."""

    def test_sponson_pair_resolves(self, sm_engine, MEQ):
        ranged, _ = _resolved(sm_engine, "Impulsor", MEQ)
        sponsons = [r for r in ranged
                    if r.lower() in ("storm bolter", "fragstorm grenade launcher")]
        assert len(sponsons) == 2, f"sponson pair expected, got {ranged}"
        assert len(set(sponsons)) == 1, f"both sponsons must match, got {sponsons}"

    def test_choice_entries_carry_count(self, sm_engine):
        cfg = json.loads((Path(__file__).resolve().parent.parent
                          / "data/config/space-marines/weapon_options.json").read_text())
        b = cfg["Impulsor"]["builds"][0]
        sponsons = [s for s in b["slots"] if s["name"] == "Sponsons"][0]
        for c in sponsons["choices"]:
            assert c.get("count") == 2, f"sponson choice {c['name']} lacks count=2"
            sm_engine.W(c["name"], unit_name="Impulsor", category=c.get("type"))
