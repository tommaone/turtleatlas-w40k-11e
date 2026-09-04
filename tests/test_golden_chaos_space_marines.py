"""Golden loadout locks — chaos-space-marines (regression sweep units).

Source of truth: tests/golden_loadouts/chaos-space-marines.json
(Wahapedia 11ed, fetched 2026-08-24, confidence high).

Verdicts applied (regression report lines 25-28):
- Chaos Lord: 'Astartes chainblade' was the WRONG catalog entry (distinct
  profile from the datasheet's astartes chainsword) — FIXED to chainsword.
- Chaos Lord With Jump Pack: twin lightning claws replace BOTH bolt pistol
  AND accursed weapon; the single-build slot structure allowed the illegal
  claws+pistol combo — FIXED as a separate fixed build.
- Forgefiend: arm guns are paired (2x hades OR 2x ectoplasma via count:2);
  head is jaws OR ectoplasma+limbs bundle. KEPT.
- Khorne Lord Of Skulls: moved characters.json -> weapon_options.json;
  structure matches datasheet (one gun of each pair). KEPT.

STRUCTURE + COUNT assertions only — damage values stay engine-derived.
"""

import json
import sys
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from engine.ranking import RankingEngine

def _base(name):
    """Strip choice-profile suffixes ('... - strike'/' - standard') for identity."""
    return name.split(" - ")[0]

GOLDEN = Path(__file__).resolve().parent / "golden_loadouts" / "chaos-space-marines.json"


@pytest.fixture(scope="module")
def engine():
    return RankingEngine("chaos-space-marines")


class TestChaosLord:
    """Golden: daemon hammer / accursed / CHAINSWORD melee + plasma pistol or power fist."""

    def test_no_chainblade_phantom(self, engine, MEQ):
        """chainblade is a different weapon (A7 S4) than the datasheet chainsword."""
        res = engine.resolve_loadout("Chaos Lord", MEQ)
        assert res is not None
        _pts, _r, melee, _i, _info = res
        assert all(w.name != "Astartes chainblade" for w in melee)

    def test_melee_from_datasheet_list(self, engine, MEQ):
        res = engine.resolve_loadout("Chaos Lord", MEQ)
        _pts, _r, melee, _i, _info = res
        assert len(melee) >= 1
        assert melee[0].name in ("Daemon hammer", "Accursed weapon",
                                 "Astartes chainsword")

    def test_pistol_or_fist(self, engine, MEQ):
        res = engine.resolve_loadout("Chaos Lord", MEQ)
        _pts, ranged, _m, _i, _info = res
        guns = [_base(w.name) for w in ranged]
        assert guns in ([], ["Plasma pistol"])


class TestChaosLordJumpPack:
    """Golden: claws build has NO ranged; default build has <= one pistol."""

    def test_claws_build_excludes_pistol(self, engine, MEQ):
        """Twin lightning claws replace bolt pistol AND accursed weapon —
        any claws+ranged resolution would be an illegal combo."""
        res = engine.resolve_loadout("Chaos Lord With Jump Pack", MEQ)
        assert res is not None
        _pts, ranged, melee, _i, info = res
        names = [w.name for w in melee]
        if "Twin lightning claws" in names:
            assert not ranged, "illegal combo: lightning claws + pistol scored"

    def test_default_melee_options(self, engine, MEQ):
        res = engine.resolve_loadout("Chaos Lord With Jump Pack", MEQ)
        _pts, _r, melee, _i, _info = res
        assert melee[0].name in ("Accursed weapon", "Power fist",
                                 "Twin lightning claws")

    def test_ranged_only_pistols(self, engine, MEQ):
        res = engine.resolve_loadout("Chaos Lord With Jump Pack", MEQ)
        _pts, ranged, _m, _i, _info = res
        assert all(_base(w.name) in ("Plasma pistol", "Bolt pistol")
                   for w in ranged)
        assert len(ranged) <= 1


class TestForgefiend:
    """Golden: arm cannons are PAIRED (0 or 2, never 1); head is jaws OR
    ectoplasma+limbs (separate build so limbs score)."""

    def test_arm_guns_always_paired(self, engine, MEQ):
        """Arm guns are swapped as a PAIR: hades count is always even.
        Ectoplasma may add an odd head gun (head swap)."""
        res = engine.resolve_loadout("Forgefiend", MEQ)
        assert res is not None
        _pts, ranged, _m, _i, _info = res
        counts = Counter(_base(w.name) for w in ranged)
        assert counts["Hades autocannon"] % 2 == 0, (
            f"hades x{counts['Hades autocannon']}: arm guns swap in pairs")

    def test_melee_always_present(self, engine, MEQ):
        """jaws default OR armoured limbs when the head gun replaces them."""
        res = engine.resolve_loadout("Forgefiend", MEQ)
        _pts, ranged, melee, _i, _info = res
        assert len(melee) >= 1
        assert {w.name for w in melee} <= {"Forgefiend jaws", "Armoured limbs"}

    def test_limbs_only_with_ecto_head(self, engine, MEQ):
        res = engine.resolve_loadout("Forgefiend", MEQ)
        _pts, ranged, melee, _i, _info = res
        has_ecto = any(_base(w.name) == "Ectoplasma cannon" for w in ranged)
        if any(w.name == "Armoured limbs" for w in melee):
            assert has_ecto, "limbs exist only when the head gun replaced the jaws"


class TestKhorneLordOfSkulls:
    """Golden: cleaver fixed + exactly one gun of each pair."""

    def test_cleaver_fixed(self, engine, MEQ):
        res = engine.resolve_loadout("Khorne Lord Of Skulls", MEQ)
        assert res is not None
        _pts, _r, melee, _i, _info = res
        assert any(_base(w.name) == "Great cleaver of Khorne" for w in melee)

    def test_one_gun_per_pair(self, engine, MEQ):
        res = engine.resolve_loadout("Khorne Lord Of Skulls", MEQ)
        _pts, ranged, _m, _i, _info = res
        names = [w.name for w in ranged]
        assert len(names) == 2, f"exactly two cannon slots, got {names}"
        pair_a = {"Hades gatling cannon", "Skullhurler"}
        pair_b = {"Gorestorm cannon", "Daemongore cannon", "Ichor cannon"}
        assert len(set(names) & pair_a) == 1
        assert len(set(names) & pair_b) == 1


class TestWeaponPairCounts:
    """Golden follow-up (2026-08-24): Defiler/Maulerfiend pair choices
    under-counted (same defect class as TestCsmVehicleCounts in
    test_golden_loadouts.py; Land Raider/Venomcrawler/Destructor were
    fixed separately by commit 9e7292a)."""

    def test_defiler_two_excruciators(self, engine, MEQ):
        res = engine.resolve_loadout("Defiler", MEQ)
        _pts, ranged, _m, _i, _info = res
        assert [w.name for w in ranged].count("Excruciator cannon") == 2

    def test_maulerfiend_two_magma_cutters(self, engine, MEQ):
        res = engine.resolve_loadout("Maulerfiend", MEQ)
        _pts, ranged, _m, _i, _info = res
        assert [w.name for w in ranged].count("Magma cutter") == 2

def test_golden_source_file_exists():
    data = json.loads(GOLDEN.read_text())
    for u in data["units"]:
        assert u.get("_source"), f"{u['unit']}: golden entry without source"
