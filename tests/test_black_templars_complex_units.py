"""End-to-end tests for the complex black-templars squad-composition units.

Runs the full pipeline (BSData parser -> config generator -> engine alloc
resolution) through the real regenerated config
(data/config/black-templars/squads.json) and pins the deterministic resolved
loadouts for the BT-specific complex units covered in this iteration.

This iteration migrated black-templars squads to the complex layer:
- parallel-variant alloc pools (Crusader Squad — Initiate/Neophyte mix with
  pool_min + group_max constraints)
- per-model weapon slots (Sword Brethren Squad)
- shared SM squads (Intercessor etc.) ride the same payloads already pinned
  in test_space_marines_complex_units.py — here we pin the BT-specific units.
- 'Chaplain Grimaldus' moved OUT of squads.json into characters.json this
  iteration: he is a character (n=1), not a squad, and had been misplaced in
  the squads file. Converted to the characters weapon_options.builds schema;
  the two old plasma builds (Standard/Supercharge) collapse to one build with
  the bare 'Plasma Pistol', which the choice-profile max-over fix resolves to
  the better profile deterministically. Pinned via resolve_loadout below.

BT catalogue note: 'Primaris Crusader Squad' is NOT a separate datasheet in
11e — the Primaris Crusader options live inside the single 'Crusader Squad'
datasheet, so no separate config entry exists.

Data-coverage note: 'Invader Atv' has no BSData squad-composition entry
(mount payload inside Outrider Squad) — kept with curated builds. The
Outrider Squad embedded ATV slot trips the validator's known ATV
false-positive class (same flags as shipped SM/BA/SW) — documented, not fixed.

Per turtle-dojo, STRUCTURE is asserted (alloc distribution, weapon names and
counts), NOT damage numbers — no expected_wounds.

Run: python3 -m pytest tests/test_black_templars_complex_units.py -v
"""

from collections import Counter
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.ranking import RankingEngine


@pytest.fixture(scope="module")
def bt_engine():
    return RankingEngine("black-templars")


def _build(engine, name, target):
    res = engine._best_squad_variant(name, target)
    assert res is not None, f"{name} did not resolve"
    return res


def _rcount(res, name):
    return Counter(w.name for w in res["ranged"])[name]


def _mcount(res, name):
    return Counter(w.name for w in res["melee"])[name]


class TestBlackTemplarsComplexUnits:
    """Real-config regression pins: exact resolved loadout per complex unit."""

    def test_crusader_squad_alloc(self, bt_engine, MEQ):
        """Crusader Squad n=10: 9 model pool across the Initiate/Neophyte
        variants (respecting pool_min 5 Initiate-equivalents and group_max
        2 on the special weapons) + 1 Sword Brother leader. vs MEQ the
        power-fist Initiates max (2), the pyreblasters max (2), 4 Neophyte
        chainswords and 1 chainsword Initiate fill the rest."""
        res = _build(bt_engine, "Crusader Squad", MEQ)
        assert res["_alloc_info"] == [
            ("Initiate", [
                ("Initiate w/Chainsword & Heavy Bolt Pistol", 1),
                ("Initiate w/Power Fist & Heavy Bolt Pistol", 2),
                ("Initiate w/Pyreblaster", 2),
                ("Neophyte w/ Astartes Chainsword", 4),
            ]),
        ]
        assert _rcount(res, "Pyreblaster") == 2
        assert _rcount(res, "Pyre Pistol") == 1
        assert _mcount(res, "Power fist") == 2
        assert _mcount(res, "Master-crafted Power Weapon") == 1
        assert len(res["melee"]) == 10

    def test_sword_brethren_squad_alloc(self, bt_engine, MEQ):
        """Sword Brethren Squad n=4: all 4 models allocate to the base Sword
        Brother variant and resolve the Plasma pistol + Thunder Hammer slot
        picks vs MEQ."""
        res = _build(bt_engine, "Sword Brethren Squad", MEQ)
        assert res["_alloc_info"] == [
            ("Sword Brother", [("Sword Brother", 4)]),
        ]
        assert _rcount(res, "Plasma pistol - standard") == 4
        assert _mcount(res, "Thunder Hammer") == 4
        assert len(res["melee"]) == 4


class TestBlackTemplarsCharacters:
    """Character resolution pins — Grimaldus after the squads→characters move."""

    def test_grimaldus_resolves_from_characters(self, bt_engine, MEQ):
        """Chaplain Grimaldus (100 pts) now lives in characters.json with the
        weapon_options.builds schema: one build, bare 'Plasma Pistol' ranged +
        Artificer Crozius melee. The bare plasma resolves to the standard
        profile in the BT catalogue (standard-first profile order)."""
        res = bt_engine.resolve_loadout("Chaplain Grimaldus", MEQ)
        assert res is not None
        pts, ranged, melee, innate, info = res
        assert pts == 100
        assert Counter(w.name for w in ranged) == {"Plasma pistol - standard": 1}
        assert Counter(w.name for w in melee) == {"Artificer Crozius": 1}

    def test_helbrecht_dual_sword_profiles(self, bt_engine, MEQ):
        """High Marshal Helbrecht: Ferocity ranged + both Sword of the High
        Marshals profiles (Sweep + Strike) — dual-profile max-over applies."""
        res = bt_engine.resolve_loadout("High Marshal Helbrecht", MEQ)
        assert res is not None
        pts, ranged, melee, innate, info = res
        assert pts == 110  # MFM v1.2 truth (was 120 pre-refresh)
        assert Counter(w.name for w in ranged) == {"Ferocity": 1}
        assert Counter(w.name for w in melee) == {
            "Sword of the High Marshals - Sweep": 1,
            "Sword of the High Marshals - Strike": 1,
        }

    def test_castellan_choices_resolve(self, bt_engine, MEQ):
        """Castellan: Combi-weapon ranged + Master-crafted Power Weapon melee
        via the choices lists (not the fixed lists)."""
        res = bt_engine.resolve_loadout("Castellan", MEQ)
        assert res is not None
        pts, ranged, melee, innate, info = res
        assert pts == 70
        assert Counter(w.name for w in ranged) == {"Combi-weapon": 1}
        assert Counter(w.name for w in melee) == {"Master-crafted Power Weapon": 1}
