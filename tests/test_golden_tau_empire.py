"""Golden loadout locks — tau-empire datasheet-verified structures.

Golden follow-up (2026-08-24): literal '2 x' weapon names ('2 Smart missile
systems', '2 accelerator burst cannons', '2 twin pulse carbines', '2 nexus
missile launchers') failed catalogue lookup, so every combo containing them
was silently skipped. Rewritten to catalogue-exact singular + count (engine
honours count on slot choices since 9e7292a).

Sources: wahapedia.ru 11ed t-au-empire datasheets — Devilfish ("2 twin pulse
carbines can be replaced with 2 smart missile systems"), Sky Ray Gunship
("2 twin pulse carbines can be replaced with: 2 accelerator burst cannons /
2 smart missile systems"), Ta'unar Supremacy Armour ("3 pulse ordnance drivers
can be replaced with one of the following: 2 nexus missile launchers / ...").

STRUCTURE + COUNT assertions only — damage values stay engine-derived.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from engine.ranking import RankingEngine


@pytest.fixture(scope="module")
def engine():
    return RankingEngine("tau-empire")


def _ranged_counts(engine, unit, MEQ):
    res = engine.resolve_loadout(unit, MEQ)
    assert res is not None, f"{unit}: loadout did not resolve"
    _pts, ranged, _melee, _innate, _info = res
    from collections import Counter
    return Counter(w.name for w in ranged)


class TestDevilfish:
    """Drone rack pair: base is 2 twin pulse carbines, swappable for
    2 smart missile systems."""

    def test_pair_resolves(self, engine, MEQ):
        counts = _ranged_counts(engine, "Devilfish", MEQ)
        assert counts["Twin pulse carbine"] == 2 or \
            counts["Smart missile system"] == 2, dict(counts)

    def test_no_single_drone_rack_gun(self, engine, MEQ):
        counts = _ranged_counts(engine, "Devilfish", MEQ)
        assert counts["Twin pulse carbine"] != 1
        assert counts["Smart missile system"] != 1

    def test_choice_entries_carry_count(self, engine):
        cfg = json.loads((Path(__file__).resolve().parent.parent
                          / "data/config/tau-empire/weapon_options.json").read_text())
        b = cfg["Devilfish"]["builds"][0]
        slot = [s for s in b["slots"] if s["name"] == "Twin Pulse Carbines"][0]
        for c in slot["choices"]:
            assert c.get("count") == 2, f"choice {c['name']} lacks count=2"
            engine.W(c["name"], unit_name="Devilfish", category=c.get("type"))


class TestSkyRayGunship:
    """Base is 2 twin pulse carbines; either pair can be swapped for
    2 accelerator burst cannons or 2 smart missile systems."""

    def test_pair_resolves(self, engine, MEQ):
        counts = _ranged_counts(engine, "Sky Ray Gunship", MEQ)
        pairs = [counts[n] for n in ("Twin pulse carbine",
                                     "Accelerator burst cannon",
                                     "Smart missile system")]
        assert any(p >= 2 for p in pairs), dict(counts)

    def test_no_lone_sponson_gun(self, engine, MEQ):
        """The swap weapon must arrive as a PAIR, never a single gun."""
        counts = _ranged_counts(engine, "Sky Ray Gunship", MEQ)
        assert counts["Accelerator burst cannon"] != 1
        assert counts["Smart missile system"] != 1

    def test_choice_entries_carry_count(self, engine):
        cfg = json.loads((Path(__file__).resolve().parent.parent
                          / "data/config/tau-empire/weapon_options.json").read_text())
        b = cfg["Sky Ray Gunship"]["builds"][0]
        slot = [s for s in b["slots"] if s["name"] == "Weapon"][0]
        for c in slot["choices"]:
            assert c.get("count") == 2, f"choice {c['name']} lacks count=2"
            engine.W(c["name"], unit_name="Sky Ray Gunship", category=c.get("type"))


class TestTaunarSupremacyArmour:
    """Secondary battery: 3 pulse ordnance drivers replaceable with
    2 nexus missile launchers (wahapedia 11ed)."""

    def test_secondary_pair_or_triple(self, engine, MEQ):
        counts = _ranged_counts(engine, "Taunar Supremacy Armour", MEQ)
        ok = counts["Nexus missile launcher"] == 2 or \
            counts["Pulse ordnance driver"] == 3
        assert ok, dict(counts)

    def test_choice_entries_carry_count(self, engine):
        cfg = json.loads((Path(__file__).resolve().parent.parent
                          / "data/config/tau-empire/weapon_options.json").read_text())
        b = cfg["Taunar Supremacy Armour"]["builds"][0]
        slot = [s for s in b["slots"] if s["name"] == "Secondary weapons"][0]
        expected = {"Nexus missile launcher": 2, "Pulse ordnance driver": 3}
        for c in slot["choices"]:
            if c["name"] in expected:
                assert c.get("count") == expected[c["name"]], (
                    f"choice {c['name']} wrong count"
                )
                engine.W(c["name"], unit_name="Taunar Supremacy Armour",
                         category=c.get("type"))
