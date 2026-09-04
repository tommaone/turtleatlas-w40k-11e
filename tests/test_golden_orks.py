"""Golden loadout locks — Orks datasheet-verified equipment structures.

Source of truth: tests/golden_loadouts/orks-golden.json
(wahapedia 11ed, fetched 2026-08-24, confidence high).

Companion to the GK/CSM pilot (tests/test_golden_loadouts.py, commit
ec7b60c). STRUCTURE + COUNT + CAP assertions only — no damage numbers;
the engine stays the single source of computation.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from engine.ranking import RankingEngine

GOLDEN = Path(__file__).resolve().parent / "golden_loadouts" / "orks-golden.json"
CHARACTERS = Path(__file__).resolve().parent.parent / "data" / "config" / "orks" / "characters.json"
WEAPON_OPTIONS = Path(__file__).resolve().parent.parent / "data" / "config" / "orks" / "weapon_options.json"


@pytest.fixture(scope="module")
def orks_engine():
    return RankingEngine("orks")


def _resolve(engine, name, MEQ):
    res = engine.resolve_loadout(name, MEQ)
    assert res is not None, f"{name}: no resolve"
    return res


# ---------------------------------------------------------------------------
# Characters
# ---------------------------------------------------------------------------


class TestWarboss:
    """Golden: three paired builds — no illegal cross combos."""

    def test_three_builds_exist(self):
        d = json.loads(WEAPON_OPTIONS.read_text())
        names = [b["name"] for b in d["Warboss"]["builds"]]
        assert names == ["default", "kombi-powerklaw", "shoota-choppa"]

    def test_shoota_only_pairs_with_kustom_choppa(self):
        d = json.loads(WEAPON_OPTIONS.read_text())
        for b in d["Warboss"]["builds"]:
            all_names = [f["name"] for f in b.get("fixed", [])]
            if "Kustom shoota" in all_names:
                assert "Kustom choppa" in all_names
                assert "Big choppa" not in all_names and "Power klaw" not in all_names


class TestBigMekInMegaArmour:
    """Golden: power klaw fixed; killsaw is melee; non-weapon wargear excluded."""

    def test_resolves_with_real_combos(self, orks_engine, MEQ):
        _pts, ranged, _melee, _i, info = _resolve(orks_engine, "Big Mek In Mega Armour", MEQ)
        # Regression: pre-fix the Grot Oiler slot poisoned every combo -> bare fixed.
        assert info.get("_n_combos", 0) > 0
        # Tellyport blasta combo must be reachable (best loadout takes it vs MEQ).
        assert "Tellyport blasta" in [w.name for w in ranged]

    def test_weapon_slot_types(self):
        d = json.loads(CHARACTERS.read_text())
        b = d["Big Mek In Mega Armour"]["weapon_options"]["builds"][0]
        slot = next(s for s in b["slots"] if s["name"] == "Weapon")
        types = {c["name"]: c["type"] for c in slot["choices"]}
        assert types["Killsaw"] == "melee"
        assert types["Kustom mega-blasta"] == "ranged"

    def test_no_grot_oiler_slot(self):
        d = json.loads(CHARACTERS.read_text())
        b = d["Big Mek In Mega Armour"]["weapon_options"]["builds"][0]
        assert all("Grot oiler" not in [c["name"] for c in s["choices"]] for s in b["slots"])


class TestMek:
    """Golden: kustom mega-slugga ONLY ranged; phantom mega-blasta gone."""

    def test_single_ranged_mega_slugga(self, orks_engine, MEQ):
        _pts, ranged, _melee, _i, _info = _resolve(orks_engine, "Mek", MEQ)
        names = [w.name for w in ranged]
        assert names == ["Kustom mega-slugga"], f"expected exactly one mega-slugga, got {names}"

    def test_melee_swap_options(self, orks_engine, MEQ):
        res = orks_engine.resolve_loadout("Mek", MEQ)
        assert res is not None and len(res[2]) >= 1


class TestPainboss:
    def test_base_claw_only(self, orks_engine, MEQ):
        _pts, ranged, melee, _i, _info = _resolve(orks_engine, "Painboss", MEQ)
        assert ranged == []
        assert [w.name for w in melee] == ["Beast Snagga klaw"]

    def test_no_grot_orderly(self, orks_engine, MEQ):
        res = orks_engine.resolve_loadout("Painboss", MEQ)
        all_w = [w.name for w in res[1] + res[2]]
        assert "Grot orderly" not in all_w


class TestPainboy:
    def test_syringe_and_klaw(self, orks_engine, MEQ):
        _pts, ranged, melee, _i, _info = _resolve(orks_engine, "Painboy", MEQ)
        assert ranged == []
        names = sorted(w.name for w in melee)
        # Regression: audit sweep wrote a literal '"' into the name and used an
        # ASCII apostrophe — catalogue name carries U+2019. Lookup silently
        # KeyError'd and the syringe vanished from scoring.
        assert names == ["Power klaw", "\u2019Urty syringe"]


# ---------------------------------------------------------------------------
# Vehicles / monsters
# ---------------------------------------------------------------------------


class TestBattlewagon:
    """Golden: at most ONE big gun; optionals baked as legal maximal build."""

    BIG_GUNS = {"Killkannon", "Zzap gun", "Kannon"}

    def test_one_big_gun_max(self, orks_engine, MEQ):
        _pts, ranged, melee, _i, _info = _resolve(orks_engine, "Battlewagon", MEQ)
        big = [w.name for w in ranged + melee if w.name in self.BIG_GUNS]
        assert len(big) <= 1, f"max ONE big gun, got {big}"

    def test_deff_rolla_or_nothing(self, orks_engine, MEQ):
        _pts, ranged, melee, _i, _info = _resolve(orks_engine, "Battlewagon", MEQ)
        assert [w.name for w in melee].count("Deff rolla") <= 1


class TestBurnaBommer:
    def test_base_guns_and_optional_skorcha(self, orks_engine, MEQ):
        _pts, ranged, _melee, _i, _info = _resolve(orks_engine, "Burna-Bommer", MEQ)
        names = [w.name for w in ranged]
        assert names.count("Twin big shoota") >= 1
        assert names.count("Twin supa-shoota") >= 1
        assert names.count("Skorcha missile rack") <= 1


class TestDakkajet:
    """Golden: TWO base twin supa-shootas + up to ONE additional (max 3)."""

    def test_two_to_three_supa_shootas(self, orks_engine, MEQ):
        _pts, ranged, _melee, _i, _info = _resolve(orks_engine, "Dakkajet", MEQ)
        n = [w.name for w in ranged].count("Twin supa-shoota")
        assert 2 <= n <= 3, f"expected 2-3 twin supa-shootas, got {n}"


class TestDeffDread:
    """Golden: FOUR arm slots over the union pool; stompy feet always present."""

    POOL = {"Dread klaw", "Big shoota", "Kustom mega-blasta", "Rokkit launcha", "Skorcha"}

    def test_four_arm_weapons(self, orks_engine, MEQ):
        _pts, ranged, melee, _i, _info = _resolve(orks_engine, "Deff Dread", MEQ)
        arms = [w.name for w in ranged + melee if w.name in self.POOL]
        assert len(arms) == 4, f"expected exactly 4 arm weapons, got {arms}"

    def test_stompy_feet_fixed(self, orks_engine, MEQ):
        _pts, _r, melee, _i, _info = _resolve(orks_engine, "Deff Dread", MEQ)
        assert "Stompy feet" in [w.name for w in melee]

    def test_all_choices_resolve(self, orks_engine, MEQ):
        """No unresolvable choice may silently skip combos."""
        res = orks_engine.resolve_loadout("Deff Dread", MEQ)
        assert res[4].get("_n_combos", 0) == 625  # 5^4 fully explored


class TestGargantuanSquiggoth:
    def test_tusks_and_at_most_one_gun(self, orks_engine, MEQ):
        _pts, ranged, melee, _i, _info = _resolve(orks_engine, "Gargantuan Squiggoth", MEQ)
        assert any(w.name.startswith("Huge tusks") for w in melee)
        guns = [w.name for w in ranged if w.name in ("Supa-kannon", "Kannon")]
        assert len(guns) <= 1


class TestWazbomBlastajet:
    def test_main_weapon_exactly_one(self, orks_engine, MEQ):
        _pts, ranged, _melee, _i, _info = _resolve(orks_engine, "Wazbom Blastajet", MEQ)
        names = [w.name for w in ranged]
        main = [n for n in names if n in ("Twin wazbom mega-kannon", "Twin tellyport mega-blasta")]
        assert len(main) == 1
        assert names.count("Smasha gun") == 1
        assert names.count("Twin supa-shoota") <= 1


def test_golden_source_file_exists():
    """The golden corpus must be present and carry sources."""
    data = json.loads(GOLDEN.read_text())
    for u in data["units"]:
        assert u.get("_source"), f"{u['unit']}: golden entry without source"
        assert u.get("verdict"), f"{u['unit']}: golden entry without verdict"
