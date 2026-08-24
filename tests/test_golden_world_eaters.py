"""Golden loadout locks — World Eaters datasheet-verified equipment structures.

Source of truth: workspace/golden_loadouts/world-eaters-golden.json
(wahapedia 11ed, fetched 2026-08-24, confidence high). The Defiler pins
mirror the CSM golden verdict from tests/test_golden_loadouts.py
(commit ec7b60c).

STRUCTURE + COUNT + CAP assertions only — no damage numbers; the engine
stays the single source of computation.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from engine.ranking import RankingEngine

GOLDEN = Path(__file__).resolve().parent.parent / "workspace" / "golden_loadouts" / "world-eaters-golden.json"
CHARACTERS = Path(__file__).resolve().parent.parent / "data" / "config" / "world-eaters" / "characters.json"
WEAPON_OPTIONS = Path(__file__).resolve().parent.parent / "data" / "config" / "world-eaters" / "weapon_options.json"


@pytest.fixture(scope="module")
def we_engine():
    return RankingEngine("world-eaters")


def _resolve(engine, name, MEQ):
    res = engine.resolve_loadout(name, MEQ)
    assert res is not None, f"{name}: no resolve"
    return res


class TestBloodthirster:
    """Golden: axe/flail/lash bundles are MELEE — never in the ranged pool."""

    def test_ranged_pool_hellfire_only(self, we_engine, MEQ):
        _pts, ranged, _melee, _i, _info = _resolve(we_engine, "Bloodthirster", MEQ)
        names = [w.name for w in ranged]
        assert names == ["Hellfire breath"], f"ranged pool polluted: {names}"

    def test_bundle_types_melee(self):
        d = json.loads(CHARACTERS.read_text())
        slot = d["Bloodthirster"]["weapon_options"]["builds"][0]["slots"][0]
        types = {c["name"]: c["type"] for c in slot["choices"]}
        assert types["Axe and flail"] == "melee"
        assert types["Axe and lash"] == "melee"

    def test_bundles_resolve_as_melee(self, we_engine, MEQ):
        """Both alternative kits must be reachable melee options."""
        for bundle in ("Axe and flail", "Axe and lash"):
            w = we_engine.W(bundle, unit_name="Bloodthirster", category="melee")
            assert w is not None


class TestChaosPredators:
    """Golden: sponsons are a matched PAIR; pintle one-of-two; all resolve."""

    @pytest.mark.parametrize("unit,main_gun", [
        ("Chaos Predator Annihilator", "Predator twin lascannon"),
        ("Chaos Predator Destructor", "Predator autocannon"),
    ])
    def test_sponson_pair_and_pintle(self, we_engine, MEQ, unit, main_gun):
        _pts, ranged, _melee, _i, info = _resolve(we_engine, unit, MEQ)
        names = [w.name for w in ranged]
        assert info.get("_n_combos", 0) > 0
        assert names.count(main_gun) == 1
        # Sponsons: exactly two of the same gun (or none picked if out-damaged,
        # but the pair must never be split or single).
        hb, lc = names.count("Heavy bolter"), names.count("Lascannon")
        assert hb in (0, 2) and lc in (0, 2), f"unpaired sponsons: HB={hb} LC={lc}"
        assert not (hb and lc), "cannot mix heavy bolters and lascannons"
        # Pintle: at most one combi
        assert names.count("Combi-bolter") + names.count("Combi-weapon") <= 1

    def test_no_stale_names(self):
        """Pre-fix config used unresolvable names — guard against regression."""
        d = json.loads(WEAPON_OPTIONS.read_text())
        for u in ("Chaos Predator Annihilator", "Chaos Predator Destructor"):
            b = d[u]["builds"][0]
            for s in b["slots"]:
                for c in s["choices"]:
                    assert c["name"] in ("Heavy bolter", "Lascannon",
                                         "Combi-bolter", "Combi-weapon",
                                         "Havoc launcher"), c["name"]


class TestDefiler:
    """Golden (mirrors CSM ec7b60c): electroscourge capped at ONE model-wide."""

    def test_electroscourge_max_one(self, we_engine, MEQ):
        res = we_engine.compute_ranking(mission="Purge the Foe", meta_name="all-comers")
        df = [x for x in res if x["name"] == "Defiler"][0]
        detail = df["loadout_detail"]
        # loadout_detail is a summary string; resolve directly instead.
        _pts, ranged, melee, _i, _info = _resolve(we_engine, "Defiler", MEQ)
        total = ([w.name for w in ranged] + [w.name for w in melee]).count("Electroscourge")
        assert total <= 1

    def test_double_hades_lascannon_legal(self, we_engine, MEQ):
        build = {
            "fixed": [],
            "slots": [
                {"name": "A", "choices": [{"name": "Hades lascannon", "type": "ranged"}]},
                {"name": "B", "choices": [{"name": "Hades lascannon", "type": "ranged"}]},
            ],
        }
        resolved = we_engine._resolve_slots_build(build, "Defiler", MEQ)
        assert resolved is not None
        assert [w.name for w in resolved[0]].count("Hades lascannon") == 2

    def test_double_electroscourge_combo_skipped(self, we_engine, MEQ):
        build = {
            "fixed": [],
            "slots": [
                {"name": "A", "choices": [{"name": "Heavy baleflamer", "type": "ranged"},
                                          {"name": "Electroscourge", "type": "melee", "max_count": 1}]},
                {"name": "B", "choices": [{"name": "Heavy missile launcher", "type": "ranged"},
                                          {"name": "Electroscourge", "type": "melee", "max_count": 1}]},
            ],
        }
        resolved = we_engine._resolve_slots_build(build, "Defiler", MEQ)
        assert resolved is not None
        total = ([w.name for w in resolved[0]] + [w.name for w in resolved[1]]) \
            .count("Electroscourge")
        assert total <= 1

    def test_config_carries_max_count(self):
        d = json.loads(WEAPON_OPTIONS.read_text())
        for b in d["Defiler"]["builds"]:
            for s in b["slots"]:
                for c in s["choices"]:
                    if c["name"] == "Electroscourge":
                        assert c.get("max_count") == 1


class TestForgefiend:
    """Golden: arm guns come as a matched PAIR of one type."""

    def test_matched_arm_pair(self, we_engine, MEQ):
        _pts, ranged, _melee, _i, _info = _resolve(we_engine, "Forgefiend", MEQ)
        names = [w.name for w in ranged]
        ecto, hades = names.count("Ectoplasma cannon"), names.count("Hades autocannon")
        # Arms are a matched pair (2+0 or 0+2); the head bundle may add ONE
        # extra ectoplasma cannon when the ecto+claws kit is picked.
        assert hades in (0, 2), f"unmatched hades arms: {hades}"
        assert ecto >= 2 if hades == 0 else ecto <= 1

    def test_head_slot_structure(self):
        d = json.loads(WEAPON_OPTIONS.read_text())
        b = d["Forgefiend"]["builds"][0]
        head = next(s for s in b["slots"] if s["name"] == "Head weapons")
        names = {c["name"] for c in head["choices"]}
        assert names == {"Forgefiend jaws", "Ectoplasma cannon and claws"}


class TestHelbrute:
    """Golden: hammer/scourge are MELEE; fist bundles carry their own gun."""

    def test_melee_replacements_resolve_as_melee(self, we_engine, MEQ):
        for nm in ("Helbrute hammer", "Power scourge"):
            w = we_engine.W(nm, unit_name="Helbrute", category="melee")
            assert w is not None

    def test_fist_bundles_resolve(self, we_engine, MEQ):
        for nm in ("Helbrute fist with combi-bolter", "Helbrute fist with heavy flamer"):
            w = we_engine.W(nm, unit_name="Helbrute", category="ranged")
            assert w is not None

    def test_two_fists_legal(self, we_engine, MEQ):
        build = {
            "fixed": [],
            "slots": [
                {"name": "Missile", "choices": [
                    {"name": "Helbrute fist with combi-bolter", "type": "ranged"}]},
                {"name": "Melta", "choices": [
                    {"name": "Helbrute fist with heavy flamer", "type": "ranged"}]},
            ],
        }
        resolved = we_engine._resolve_slots_build(build, "Helbrute", MEQ)
        assert resolved is not None
        # The loader resolves each fist bundle to its gun profile (bundle name
        # -> inner weapon), so assert the distinct per-fist guns.
        names = [w.name for w in resolved[0]]
        assert names.count("Combi-bolter") == 1
        assert names.count("Heavy flamer") == 1


class TestKhorneLordOfSkulls:
    """Golden: cleaver fixed; one gatling pick; one gorestorm pick."""

    def test_structure(self, we_engine, MEQ):
        _pts, ranged, melee, _i, _info = _resolve(we_engine, "Khorne Lord Of Skulls", MEQ)
        names = [w.name for w in ranged] + [w.name for w in melee]
        assert any(n.startswith("Great cleaver of Khorne") for n in names)
        gatling = [n for n in names if n in ("Hades gatling cannon", "Skullhurler")]
        assert len(gatling) == 1
        storm = [n for n in names if n in ("Gorestorm cannon", "Daemongore cannon", "Ichor cannon")]
        assert len(storm) == 1


class TestWeaponPairCounts:
    """Golden follow-up (2026-08-24): 'Two X'/'2 X' choices under-counted."""

    def test_defiler_two_excruciators(self, we_engine, MEQ):
        res = we_engine.resolve_loadout("Defiler", MEQ)
        _pts, ranged, _m, _i, _info = res
        assert [w.name for w in ranged].count("Excruciator cannon") == 2

    def test_maulerfiend_two_magma_cutters(self, we_engine, MEQ):
        res = we_engine.resolve_loadout("Maulerfiend", MEQ)
        _pts, ranged, _m, _i, _info = res
        assert [w.name for w in ranged].count("Magma cutter") == 2

def test_golden_source_file_exists():
    """The golden corpus must be present and carry sources."""
    data = json.loads(GOLDEN.read_text())
    for u in data["units"]:
        assert u.get("_source"), f"{u['unit']}: golden entry without source"
        assert u.get("verdict"), f"{u['unit']}: golden entry without verdict"
