"""End-to-end tests for the complex deathwatch squad-composition units.

Runs the full pipeline (BSData parser -> config generator -> engine alloc
resolution) through the real regenerated config
(data/config/deathwatch/squads.json) and pins the deterministic resolved
loadouts for the DW-specific complex units covered in this iteration.

This iteration migrated deathwatch squads to the complex layer:
- parallel-variant alloc pools (Deathwatch Veterans, the five Kill Teams)
  — greedy allocation by variant, respecting per-variant min/max and group_max
- per-model weapon slots (Deathwatch Terminator Squad)
- shared SM squads (Intercessor etc.) ride the same payloads already pinned
  in test_space_marines_complex_units.py — here we pin the DW-specific units.

DW catalogue note: the DW merged BSData lists 'Plasma pistol' dual profiles
standard-first, so the engine resolves the bare name to 'Plasma pistol -
standard' (S7 AP-2 D1) — same as the SM/DA/SW pattern already pinned.

Data-coverage note: 'Invader Atv' and 'Decimus Kill Team' have NO BSData
squad-composition entry (the ATV is a mount payload inside Outrider Squad;
Decimus is a datasheet with no composition structure), so they are KEPT with
curated builds. Decimus was hand-fixed this iteration: the pre-migration
config had the plasma swap backwards (ranged 'Plasma pistol - Standard' /
melee 'Plasma pistol - Supercharge'); the datasheet default is Plasma pistol
+ Power weapon. The Outrider Squad embedded ATV slot trips the validator's
known ATV false-positive class (same flags as shipped SM/BA/SW) — documented,
not fixed.

Generator bug fixed this iteration: make_build treated ANY model with
min==1 as a leader, so the Deathwatch Terminator base model (min=1, max=9 —
"at least 1") consumed the squad budget as a fixed leader and the squad
resolved 2/5 models. Leaders are now min==1 AND max==1; the base model stays
in the pool. Verified behavior-neutral for all shipped factions.

Per turtle-dojo, STRUCTURE is asserted (alloc distribution, weapon names and
counts), NOT damage numbers — no expected_wounds.

Run: python3 -m pytest tests/test_deathwatch_complex_units.py -v
"""

from collections import Counter
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.ranking import RankingEngine


@pytest.fixture(scope="module")
def dw_engine():
    return RankingEngine("deathwatch")


def _build(engine, name, target):
    res = engine._best_squad_variant(name, target)
    assert res is not None, f"{name} did not resolve"
    return res


def _rcount(res, name):
    return Counter(w.name for w in res["ranged"])[name]


def _mcount(res, name):
    return Counter(w.name for w in res["melee"])[name]


class TestDeathwatchComplexUnits:
    """Real-config regression pins: exact resolved loadout per complex unit."""

    def test_deathwatch_veterans_alloc(self, dw_engine, MEQ):
        """Deathwatch Veterans n=5: 3 Deathwatch thunder hammer + 2 frag
        cannon (frag cannon maxes at 2; the hammer out-scores the remaining
        specials vs MEQ)."""
        res = _build(dw_engine, "Deathwatch Veterans", MEQ)
        assert res["_alloc_info"] == [
            ("Veteran", [
                ("Veteran w/ Deathwatch thunder hammer", 3),
                ("Veteran w/ frag cannon and CCW", 2),
            ]),
        ]
        assert _rcount(res, "Frag cannon") == 2
        assert _mcount(res, "Deathwatch thunder hammer") == 3
        assert _mcount(res, "Close combat weapon") == 2
        assert len(res["melee"]) == 5

    def test_deathwatch_terminator_squad_all_default(self, dw_engine, MEQ):
        """Deathwatch Terminator Squad n=5: 4 Terminators + 1 Sergeant, all
        resolve the default Power Fist & Storm Bolter slot choice vs MEQ.
        Regression pin: the base model (min=1, max=9) must NOT be treated as
        a leader — the squad must resolve 5 models, not 2."""
        res = _build(dw_engine, "Deathwatch Terminator Squad", MEQ)
        assert _rcount(res, "Storm Bolter") == 5
        assert _mcount(res, "Power Fist") == 5
        assert len(res["ranged"]) == 5
        assert len(res["melee"]) == 5

    def test_fortis_kill_team_alloc(self, dw_engine, MEQ):
        """Fortis Kill Team n=10: the Intercessor pool spreads across the
        incinerator/special variants (group_max respected); the plasma
        incinerator variant resolves to Plasma Incinerator - Standard in the
        DW catalogue (standard-first profile order)."""
        res = _build(dw_engine, "Fortis Kill Team", MEQ)
        assert res["_alloc_info"] == [
            ("Kill Team Intercessor", [
                ("Kill Team Intercessor", 2),
                ("Kill Team Intercessor w/ grenade launcher", 2),
                ("Kill Team Intercessor w/ plasma pistol and incinerator", 1),
                ("Kill Team Intercessor w/ bolt pistol and incinerator", 3),
                ("Kill Team Intercessor w/ vengor launcher", 1),
            ]),
        ]
        assert _rcount(res, "Deathwatch bolt rifle") == 4
        assert _rcount(res, "Astartes grenade launcher - frag") == 2
        assert _rcount(res, "Plasma Incinerator - Standard") == 4
        assert _mcount(res, "Power fist") == 1
        assert len(res["melee"]) == 10

    def test_indomitor_kill_team_alloc(self, dw_engine, MEQ):
        """Indomitor Kill Team n=10: 3 flamestorm gauntlet bodies (max), 1
        heavy bolter (max), 6 base Heavy Intercessors."""
        res = _build(dw_engine, "Indomitor Kill Team", MEQ)
        assert res["_alloc_info"] == [
            ("Kill Team Heavy Intercessor", [
                ("Kill Team Heavy Intercessor w/ power fists & flamestorm gauntlets", 3),
                ("Kill Team Heavy Intercessor", 6),
                ("Kill Team Heavy Intercessor w/ heavy bolter", 1),
            ]),
        ]
        assert _rcount(res, "Flamestorm gauntlets") == 3
        assert _rcount(res, "Deathwatch heavy bolt rifle") == 6
        assert _rcount(res, "Deathwatch heavy bolter") == 1
        assert _mcount(res, "Twin power fists") == 3

    def test_spectrus_kill_team_alloc(self, dw_engine, MEQ):
        """Spectrus Kill Team n=10: 4 occulus bolt carbines, 3 las fusils,
        3 base Infiltrators (marksman carbines)."""
        res = _build(dw_engine, "Spectrus Kill Team", MEQ)
        assert res["_alloc_info"] == [
            ("Kill Team Infiltrator", [
                ("Kill Team Infiltrator", 3),
                ("Kill Team Infiltrator w/ occulus bolt carbine", 4),
                ("Kill Team Infiltrator w/ las fusil", 3),
            ]),
        ]
        assert _rcount(res, "Deathwatch marksman bolt carbine") == 3
        assert _rcount(res, "Deathwatch occulus bolt carbine") == 4
        assert _rcount(res, "Las fusil") == 3

    def test_talonstrike_kill_team_alloc(self, dw_engine, MEQ):
        """Talonstrike Kill Team n=10: 5 Heavy Intercessor jump bodies
        (assault bolters), 4 Intercessor jump bodies (chainswords), 1
        Plasma pistol - standard (sergeant slot)."""
        res = _build(dw_engine, "Talonstrike Kill Team", MEQ)
        assert res["_alloc_info"] == [
            ("Intercessor", [
                ("Intercessor w/ heavy bolt pistol and Jump Pack", 4),
                ("Heavy Intercessor w/ Jump Pack", 5),
            ]),
        ]
        assert _rcount(res, "Assault bolters") == 5
        assert _rcount(res, "Heavy Bolt Pistol") == 4
        assert _rcount(res, "Plasma pistol - standard") == 1
        assert _mcount(res, "Astartes Chainsword") == 4

    def test_decimus_kill_team_curated(self, dw_engine, MEQ):
        """Decimus Kill Team n=5: kept (no BSData composition), curated build
        now matches the datasheet — Plasma pistol + Power weapon on all 5.
        Regression pin: the pre-migration config had the plasma profiles
        swapped into the wrong slots (supercharge as melee)."""
        res = _build(dw_engine, "Decimus Kill Team", MEQ)
        assert _rcount(res, "Plasma pistol - standard") == 5
        assert _mcount(res, "Power weapon") == 5
        assert len(res["ranged"]) == 5
        assert len(res["melee"]) == 5
