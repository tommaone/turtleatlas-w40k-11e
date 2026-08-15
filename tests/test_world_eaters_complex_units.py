"""Regression locks for the World Eaters squad slot migration.

Locks the regenerated World Eaters squads to the BSData truth (verified
2026-08-15 via gen_squad_composition --faction world-eaters against the
"Chaos - World Eaters" composition):

Regenerated squads (9, from flat -> composition builds):
- Bloodcrushers (2 base + 1 Bloodhunter), Bloodletters (9 + 1 Bloodreaper),
  Chaos Spawn (2), Eightbound (2 + champion), Exalted Eightbound
  (2 + champion), Flesh Hounds (4 + 1 Gore Hound — only the Gore Hound has
  Burning roar; the old flat build gave it to all 5)
- alloc pools with min/max + typed weapon payloads + shared group_max:
  Chaos Terminators (heavy-weapon pool x4 + champion Weapons slot),
  Goremongers (harpoon/2-pistols/chainblade x7 + Blood Herald),
  Khorne Berzerkers (chainblade base min5 + up to 4 swaps x9 + champion
  Pistol slot)

Kept squad (1, data gap — curated manually):
- Jakhals: BSData composition holds only the 2 Dishonoured variants
  (max 2 each) with no base Jakhal model, so budget 10 is inexpressible.
  Stays flat (Autopistol + Chainblades x10).

STRUCTURE ONLY — no damage values. The engine is the single source of
computation; this test locks the config shape and resolvability, not math.

Run: python3 -m pytest tests/test_world_eaters_complex_units.py -v
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.ranking import RankingEngine

CONFIG_DIR = Path(__file__).resolve().parent.parent / "data" / "config"
SQUADS_PATH = CONFIG_DIR / "world-eaters" / "squads.json"

TARGET_SAMPLES = ["GEQ", "MEQ", "TEQ"]

# Kept units and their canonical first-model weapons (must NOT be overwritten)
KEPT_UNITS = {
    "Jakhals": ("Autopistol", "Chainblades"),
}


@pytest.fixture(scope="module")
def we_engine():
    return RankingEngine("world-eaters")


@pytest.fixture(scope="module")
def squads():
    return json.load(open(SQUADS_PATH))


def _model(squads, unit, model_name) -> dict:
    build = squads[unit]["builds"][0]
    return next(m for m in build["models"] if m["name"] == model_name)


def _alloc(squads, unit, model_name):
    m = _model(squads, unit, model_name)
    return {a["name"]: a for a in m["alloc"]}


class TestKeptUnits:
    """The 1 no-composition unit keeps its curated build."""

    @pytest.mark.parametrize("unit", list(KEPT_UNITS))
    def test_first_model_weapons(self, squads, unit):
        expect_ranged, expect_melee = KEPT_UNITS[unit]
        m = squads[unit]["builds"][0]["models"][0]
        ranged = m.get("ranged")
        ranged_ok = expect_ranged == ranged or (
            isinstance(ranged, list) and expect_ranged in ranged
        )
        assert ranged_ok, f"{unit}: ranged={ranged}, expected {expect_ranged}"
        assert m.get("melee") == expect_melee, f"{unit}: {m.get('melee')}"


class TestRegeneratedSquads:
    def test_bloodcrushers(self, squads):
        base = _model(squads, "Bloodcrushers", "Bloodcrusher")
        assert base["count"] == 2
        # Book-first names: the WE book calls the horn 'Bladed horn' (the
        # daemons catalogue name does not resolve in the WE catalog).
        assert base["melee"] == ["Hellblade", "Bladed horn"]
        champion = _model(squads, "Bloodcrushers", "Bloodhunter")
        assert champion["count"] == 1
        assert champion["melee"] == ["Hellblade", "Bladed horn"]

    def test_bloodletters(self, squads):
        assert _model(squads, "Bloodletters", "Bloodletter")["count"] == 9
        assert _model(squads, "Bloodletters", "Bloodreaper")["count"] == 1

    def test_chaos_spawn(self, squads):
        m = squads["Chaos Spawn"]["builds"][0]["models"][0]
        assert m["count"] == 2 and m["melee"] == "Hideous Mutations"

    def test_terminators_alloc(self, squads):
        m = squads["Chaos Terminators"]["builds"][0]["models"][0]
        assert m["count"] == 4  # n=5: 4 heavy-weapon pool + champion
        alloc = {a["name"]: a for a in m["alloc"]}
        assert alloc["Combi-bolter, accursed weapon"]["max"] == 4
        assert alloc["Combi-weapon, accursed weapon"]["max"] == 4
        # Shared power-fist / chainfist budget: group_max on both combi variants
        assert alloc["Combi-bolter, chainfist"]["max"] == 1
        assert alloc["Combi-bolter, chainfist"]["group_max"] == 1
        assert alloc["Combi-weapon, chainfist"]["max"] == 1
        assert alloc["Combi-weapon, chainfist"]["group_max"] == 1
        assert alloc["Combi-bolter, power fist"]["max"] == 3
        assert alloc["Combi-bolter, power fist"]["group_max"] == 3
        assert alloc["Combi-weapon, power fist"]["max"] == 3
        assert alloc["Combi-weapon, power fist"]["group_max"] == 3
        # Heavy weapon variant: melee slot + heavy flamer / reaper autocannon
        heavy = alloc["Heavy weapon"]
        assert heavy["max"] == 1
        hw_slot = {s["name"]: {c["name"] for c in s["choices"]}
                   for s in heavy["slots"]}
        assert hw_slot["Heavy weapon"] == {"Heavy flamer", "Reaper autocannon"}

    def test_terminator_champion_slots(self, squads):
        m = _model(squads, "Chaos Terminators", "Terminator Champion")
        assert m["count"] == 1
        slot = {s["name"]: {c["name"] for c in s["choices"]}
                for s in m["slots"]}
        assert slot["Weapons"] == {
            "Paired accursed weapons",
            "Combi-weapon, accursed weapon",
            "Combi-bolter, accursed weapon",
        }

    def test_eightbound(self, squads):
        assert _model(squads, "Eightbound", "Eightbound")["count"] == 2
        assert _model(squads, "Eightbound", "Eightbound Champion")["count"] == 1

    def test_exalted_eightbound(self, squads):
        m = _model(squads, "Exalted Eightbound", "Exalted Eightbound")
        assert m["count"] == 2 and m["melee"] == "Chainblades"

    def test_flesh_hounds(self, squads):
        hound = _model(squads, "Flesh Hounds", "Flesh Hound")
        assert hound["count"] == 4
        assert hound["melee"] == "Gore-drenched fangs"
        assert "ranged" not in hound, "base hound must not have Burning roar"
        gore = _model(squads, "Flesh Hounds", "Gore Hound")
        assert gore["count"] == 1
        assert gore["ranged"] == "Burning roar"

    def test_goremongers_alloc(self, squads):
        m = _model(squads, "Goremongers", "Goremonger")
        assert m["count"] == 7
        alloc = {a["name"]: a for a in m["alloc"]}
        assert alloc["Goremonger w/ blood harpoon"]["max"] == 1
        assert alloc["Goremonger w/ 2 pistols"]["max"] == 1
        assert alloc["Goremonger w/ chainblade"]["min"] == 7
        assert alloc["Goremonger w/ chainblade"]["max"] == 7
        assert _model(squads, "Goremongers", "Blood Herald")["count"] == 1

    def test_khorne_berzerkers_alloc(self, squads):
        m = _model(squads, "Khorne Berzerkers", "Khorne Berzerker")
        assert m["count"] == 9
        alloc = {a["name"]: a for a in m["alloc"]}
        assert alloc["Khorne Berzerker"]["min"] == 5  # at least 5 plain chainblades
        assert alloc["Khorne Berzerker"]["max"] == 9
        assert alloc["Khorne Berzerker w/ eviscerator and bolt pistol"]["max"] == 2
        assert alloc["Khorne Berzerker w/ eviscerator and plasma pistol"]["max"] == 2
        assert alloc["Khorne Berzerker w/ chainblade and plasma pistol"]["max"] == 2

    def test_khorne_berzerker_champion_pistol_slot(self, squads):
        m = _model(squads, "Khorne Berzerkers", "Khorne Berzerker Champion")
        assert m["count"] == 1
        slot = {s["name"]: {c["name"] for c in s["choices"]}
                for s in m["slots"]}
        assert slot["Pistol"] == {"Bolt pistol", "Plasma pistol"}


class TestAllSquadsResolve:
    def test_every_squad_resolves(self, we_engine, squads):
        for name in squads:
            if name.startswith("_"):
                continue
            for t in TARGET_SAMPLES:
                res = we_engine._best_squad_variant(name, we_engine.resolve_target(t))
                assert res is not None, f"{name} {t}: did not resolve"
                assert res.get("ranged") or res.get("melee"), f"{name} {t}: empty"
