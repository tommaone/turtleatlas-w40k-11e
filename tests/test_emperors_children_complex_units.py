"""Regression locks for the Emperor's Children squad slot migration.

Locks the regenerated EC squads to the BSData truth (verified 2026-08-13
against the "Chaos - Emperor's Children Library" catalogue):

- Chaos Terminators: alloc pool (4 profiles, chainfist capped at 1) +
  Terminator Champion Wargear slot (paired accursed weapons option, no
  chainfist — the 1-chainfist-per-5 datasheet cap lives in the pool).
- Noise Marines: alloc pool (sonic blaster min 3, blastmaster max 2) +
  Disharmonist Sonic Blaster slot (screamer pistol + power sword option).
- Infractors: Obsessionist carries TWO slots (Pistol + Melee weapon).
- Tormentors: alloc pool (plasma/meltagun max 2 each) + Obsessionist
  Bolt Pistol + Power Sword slots.

STRUCTURE ONLY — no damage values. The engine is the single source of
computation; this test locks the config shape and resolvability, not math.

Run: python3 -m pytest tests/test_emperors_children_complex_units.py -v
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.ranking import RankingEngine

CONFIG_DIR = Path(__file__).resolve().parent.parent / "data" / "config"
SQUADS_PATH = CONFIG_DIR / "emperors-children" / "squads.json"

TARGET_SAMPLES = ["GEQ", "MEQ", "TEQ"]


@pytest.fixture(scope="module")
def ec_engine():
    return RankingEngine("emperors-children")


@pytest.fixture(scope="module")
def squads():
    return json.load(open(SQUADS_PATH))


def _model(squads, unit, model_name) -> dict:
    build = squads[unit]["builds"][0]
    return next(m for m in build["models"] if m["name"] == model_name)


class TestChaosTerminators:
    def test_alloc_pool(self, squads):
        m = _model(squads, "Chaos Terminators", "Heavy weapon")
        assert m["count"] == 4
        alloc = {a["name"]: a for a in m["alloc"]}
        assert alloc["Chainfist and combi-bolter"]["max"] == 1
        assert alloc["Chainfist and combi-bolter"]["group_max"] == 1
        assert alloc["Chainfist and combi-weapon"]["group_max"] == 1
        assert alloc["Accursed weapon and combi-bolter"]["min"] == 0
        assert alloc["Accursed weapon and combi-bolter"]["ranged"] == "Combi-bolter"
        assert alloc["Power fist and combi-weapon"]["max"] == 3

    def test_champion_wargear_slot(self, squads):
        m = _model(squads, "Chaos Terminators", "Terminator Champion")
        assert m["count"] == 1
        slot = m["slots"][0]
        names = {c["name"] for c in slot["choices"]}
        assert "Paired accursed weapons" in names
        # 1-chainfist-per-5 datasheet cap: the champion cannot add a second
        # chainfist on top of the pool's shared group_max=1.
        assert "Chainfist and combi-bolter" not in names
        assert "Chainfist and combi-weapon" not in names


class TestNoiseMarines:
    def test_alloc_pool(self, squads):
        m = _model(squads, "Noise Marines", "Noise Marine")
        assert m["count"] == 5
        alloc = {a["name"]: a for a in m["alloc"]}
        assert alloc["Noise Marine w/ sonic blaster"]["min"] == 3
        assert alloc["Noise Marine w/ blastmaster"]["max"] == 2
        assert alloc["Noise Marine w/ blastmaster"]["ranged"] == "Blastmaster"

    def test_disharmonist_sonic_blaster_slot(self, squads):
        m = _model(squads, "Noise Marines", "Disharmonist")
        slot = m["slots"][0]
        names = {c["name"] for c in slot["choices"]}
        assert "Sonic blaster" in names
        assert "Screamer pistol and power sword" in names


class TestInfractors:
    def test_obsessionist_two_slots(self, squads):
        m = _model(squads, "Infractors", "Obsessionist")
        slots = {s["name"]: {c["name"] for c in s["choices"]} for s in m["slots"]}
        assert "Pistol" in slots and "Melee weapon" in slots
        assert "Bolt pistol" in slots["Pistol"] and "Plasma pistol" in slots["Pistol"]
        assert "Rapture lash" in slots["Melee weapon"] and "Power sword" in slots["Melee weapon"]


class TestTormentors:
    def test_alloc_pool(self, squads):
        m = _model(squads, "Tormentors", "Tormentor")
        assert m["count"] == 4
        alloc = {a["name"]: a for a in m["alloc"]}
        assert alloc["Tormentor"]["min"] == 4
        assert alloc["Tormentor w/ plasma gun"]["max"] == 2
        assert alloc["Tormentor w/ meltagun"]["max"] == 2

    def test_obsessionist_slots(self, squads):
        m = _model(squads, "Tormentors", "Obsessionist")
        slots = {s["name"]: {c["name"] for c in s["choices"]} for s in m["slots"]}
        assert "Bolt Pistol" in slots and "Power Sword" in slots
        assert "Rapture lash" in slots["Power Sword"]


class TestAllSquadsResolve:
    def test_every_squad_resolves(self, ec_engine, squads):
        for name in squads:
            if name.startswith("_"):
                continue
            for t in TARGET_SAMPLES:
                res = ec_engine._best_squad_variant(name, ec_engine.resolve_target(t))
                assert res is not None, f"{name} {t}: did not resolve"
                assert res.get("ranged") or res.get("melee"), f"{name} {t}: empty"
