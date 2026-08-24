"""Golden loadout locks — tyranids.

Source of truth: workspace/golden_loadouts/tyranids.json
(Wahapedia 11ed, fetched 2026-08-24, confidence high).

Verdicts applied (regression report lines 104-107):
- Hive Tyrant: datasheet caps at ONE gun total (never both HVC and
  stranglethorn); the 5d21b52 twin-ranged-slot structure could pick 2x HVC
  (illegal). The regenerated melee+one-ranged structure is correct — KEPT,
  dead unresolvable choices (Yrmgarl factors, The Miasma Cannon) and the
  off-datasheet 'Venom cannon' removed.
- Tervigon: bogus duplicate fixed entries ('Stinger salvo' ranged + lowercase
  'stinger salvoes' typed MELEE = fake melee weapon) — FIXED to one canonical
  ranged entry.
- Harpy: 'Spike columns' resolves to nothing and the lowercase melee salvoes
  entry was noise — FIXED to stinger salvoes + scything wings + gun slot.
- Tyrannofex: double stinger + 'powerful limbs' typed RANGED — FIXED to
  limbs in melee; pts_3rd 190 restored per MFM 3rd+ tier.

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
    """Strip choice-profile suffixes ('... - strike') for identity."""
    return name.split(" - ")[0]

GOLDEN = Path(__file__).resolve().parent.parent / "workspace" / "golden_loadouts" / "tyranids.json"


@pytest.fixture(scope="module")
def engine():
    return RankingEngine("tyranids")


class TestHiveTyrant:
    """Golden: at most ONE gun (HVC xor stranglethorn); at least one melee weapon."""

    def test_at_most_one_gun(self, engine, MEQ):
        res = engine.resolve_loadout("Hive Tyrant", MEQ)
        assert res is not None
        _pts, ranged, _m, _i, _info = res
        guns = [w.name for w in ranged if w.name in (
            "Heavy venom cannon", "Stranglethorn cannon")]
        assert len(guns) <= 1, f"datasheet: never both guns, got {guns}"

    def test_melee_always_present(self, engine, MEQ):
        res = engine.resolve_loadout("Hive Tyrant", MEQ)
        _pts, _r, melee, _i, _info = res
        assert len(melee) >= 1
        assert melee[0].name in ("Monstrous bonesword and lash whip",
                                 "Monstrous scything talons")

    def test_no_off_datasheet_choices(self, engine, MEQ):
        """'Venom cannon' / 'The Miasma Cannon' / 'Yrmgarl factors' are not on
        the 11e datasheet — they must never appear in a scored loadout."""
        res = engine.resolve_loadout("Hive Tyrant", MEQ)
        _pts, ranged, melee, _i, _info = res
        names = {w.name for w in ranged} | {w.name for w in melee}
        assert not names & {"Venom cannon", "The Miasma Cannon",
                            "Yrmgarl factors"}


class TestTervigon:
    """Golden: exactly one stinger salvoes RANGED; no fake melee salvoes."""

    def test_single_ranged_salvo(self, engine, MEQ):
        res = engine.resolve_loadout("Tervigon", MEQ)
        assert res is not None
        _pts, ranged, _m, _i, _info = res
        counts = Counter(w.name.lower() for w in ranged)
        salvo = sum(v for k, v in counts.items() if "stinger salvo" in k)
        assert salvo == 1, f"exactly one stinger salvoes entry, got {salvo}"

    def test_no_melee_salvo(self, engine, MEQ):
        res = engine.resolve_loadout("Tervigon", MEQ)
        _pts, _r, melee, _i, _info = res
        assert all("stinger" not in w.name.lower() for w in melee)

    def test_claws_or_talons(self, engine, MEQ):
        res = engine.resolve_loadout("Tervigon", MEQ)
        _pts, _r, melee, _i, _info = res
        assert len(melee) >= 1
        assert _base(melee[0].name) in ("Massive crushing claws",
                                        "Massive scything talons")


class TestHarpy:
    """Golden: stinger salvoes + scything wings fixed; one twin gun of two."""

    def test_fixed_salvo_and_wings(self, engine, MEQ):
        res = engine.resolve_loadout("Harpy", MEQ)
        assert res is not None
        _pts, ranged, melee, _i, _info = res
        assert any(w.name == "Stinger salvoes" for w in ranged)
        assert any(w.name == "Scything wings" for w in melee)

    def test_one_twin_gun(self, engine, MEQ):
        res = engine.resolve_loadout("Harpy", MEQ)
        _pts, ranged, _m, _i, _info = res
        guns = [w.name for w in ranged if w.name in (
            "Twin heavy venom cannon", "Twin stranglethorn cannon")]
        assert len(guns) == 1

    def test_no_spike_columns_phantom(self, engine, MEQ):
        res = engine.resolve_loadout("Harpy", MEQ)
        _pts, ranged, melee, _i, _info = res
        names = {w.name for w in ranged} | {w.name for w in melee}
        assert "Spike columns" not in names


class TestTyrannofex:
    """Golden: limbs are MELEE; one main gun of three; pts_3rd per MFM."""

    def test_limbs_in_melee_not_ranged(self, engine, MEQ):
        res = engine.resolve_loadout("Tyrannofex", MEQ)
        assert res is not None
        _pts, ranged, melee, _i, _info = res
        assert any(w.name == "Powerful limbs" for w in melee)
        assert all(w.name != "Powerful limbs" for w in ranged)

    def test_single_salvo(self, engine, MEQ):
        res = engine.resolve_loadout("Tyrannofex", MEQ)
        _pts, ranged, _m, _i, _info = res
        salvo = sum(1 for w in ranged if "stinger salvo" in w.name.lower())
        assert salvo == 1, f"exactly one stinger salvoes entry, got {salvo}"

    def test_one_main_gun(self, engine, MEQ):
        res = engine.resolve_loadout("Tyrannofex", MEQ)
        _pts, ranged, _m, _i, _info = res
        mains = [w.name for w in ranged if w.name in (
            "Fleshborer hive", "Acid spray", "Rupture cannon")]
        assert len(mains) == 1

    def test_pts_3rd_restored(self):
        cfg = json.loads((Path(__file__).resolve().parent.parent
                          / "data/config/tyranids/weapon_options.json").read_text())
        assert cfg["Tyrannofex"]["pts"] == 180
        assert cfg["Tyrannofex"]["pts_3rd"] == 190


def test_golden_source_file_exists():
    data = json.loads(GOLDEN.read_text())
    for u in data["units"]:
        assert u.get("_source"), f"{u['unit']}: golden entry without source"
