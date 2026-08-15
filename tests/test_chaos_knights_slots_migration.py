"""Regression lock for the Chaos Knights slot-schema migration (Tyrant,
Magaera, Styrix + all weapon_options units).

Locks the curated build inventories to the BSData truth (verified 2026-08-11
against the "Chaos - Chaos Knights Library" catalogue):

- Knight Tyrant: 4 builds = 2 main-weapon bundles x 2 carapace count-bundles.
  BSData: fixed [2x Twin daemonbreath meltagun (min2/max2), Titanic feet];
  Main weapons (pick 1): Brimstone volcano lance + Ectoplasma decimator OR
  Darkflame cannon + Warpshock harpoon; Carapace weapons (pick 1): 2x
  Gheiststrike + 1x desecrator OR 1x Gheiststrike + 2x desecrator. The
  Ectoplasma decimator is the GROUP entry (standard/supercharge variants are
  maxed by the engine) — the old config fixed both '- standard' and
  '- supercharge' as separate ranged weapons, DOUBLE-COUNTING them.
- Magaera / Styrix: 2 builds each. BSData: fixed main ranged x2; Melee weapon
  (pick 1) = 'Hekaton siege claw and twin rad cleanser' bundle OR Reaper
  chainsword. No Titanic feet. The old config had a MANDATORY Twin rad
  cleanser slot (wrong — it only comes with the hekaton claw).
- Asterius: fixed 2x volkite culverin, 1x karacnos, 2x twin conversion beam,
  Titanic feet (old config had 1x each — undercounted the pair weapons).
- Porphyrion: fixed 2x Twin magna lascannon + Titanic feet; Carapace weapon
  slot (ironstorm/helios); TWO independent Shoulder weapon slots
  (autocannon/lascannon each, duplicates legal — BSData min2/max2 group).
- War Dogs Brigand/Executioner/Huntsman/Karnivore: fixed weapons + one
  Carapace weapon slot. Huntsman/Karnivore carry no Armoured feet (BSData).
- Stalker: NO fixed weapons — exactly 3 slots (Carapace weapon,
  Chaincannon/spear, Slaughterclaw/chaintalon).
- Moirax: 15 builds (5 double-arm + 10 pair-arm), duplicates legal (BSData
  'Weapons' min2/max2). The 'Siege claw and rad cleanser' bundle is SPLIT
  into components (Rad cleanser + Siege claw) — Despoiler precedent; bundle
  names resolve to primary profile only.

STRUCTURE ONLY — no damage values. The engine is the single source of
computation; this test locks the config shape and resolvability, not math.

Run: python3 -m pytest tests/test_chaos_knights_slots_migration.py -v
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.ranking import RankingEngine

CONFIG_DIR = Path(__file__).resolve().parent.parent / "data" / "config"
CHARS = CONFIG_DIR / "chaos-knights" / "characters.json"
WEAPON_OPTIONS = CONFIG_DIR / "chaos-knights" / "weapon_options.json"

TARGET_SAMPLES = ["GEQ", "MEQ", "Knight"]

# ── Tyrant ───────────────────────────────────────────────────────────────
TYRANT_MELTAGUN = "Twin daemonbreath meltagun"
TYRANT_FEET = "Titanic feet"
TYRANT_VOLCANO = "Brimstone volcano lance"
TYRANT_ECTO = "Ectoplasma decimator"
TYRANT_DARKFLAME = "Darkflame cannon"
TYRANT_WARPSHOCK = "Warpshock harpoon"
TYRANT_GHEIST = "Gheiststrike missile launcher"
TYRANT_DESECRATOR = "Twin desecrator cannon"

TYRANT_EXPECTED = {
    "volcano_carapace_gheist2": {
        TYRANT_MELTAGUN, TYRANT_MELTAGUN, TYRANT_FEET, TYRANT_VOLCANO,
        TYRANT_ECTO, TYRANT_GHEIST, TYRANT_GHEIST, TYRANT_DESECRATOR,
    },
    "volcano_carapace_desecrator2": {
        TYRANT_MELTAGUN, TYRANT_MELTAGUN, TYRANT_FEET, TYRANT_VOLCANO,
        TYRANT_ECTO, TYRANT_GHEIST, TYRANT_DESECRATOR, TYRANT_DESECRATOR,
    },
    "darkflame_carapace_gheist2": {
        TYRANT_MELTAGUN, TYRANT_MELTAGUN, TYRANT_FEET, TYRANT_DARKFLAME,
        TYRANT_WARPSHOCK, TYRANT_GHEIST, TYRANT_GHEIST, TYRANT_DESECRATOR,
    },
    "darkflame_carapace_desecrator2": {
        TYRANT_MELTAGUN, TYRANT_MELTAGUN, TYRANT_FEET, TYRANT_DARKFLAME,
        TYRANT_WARPSHOCK, TYRANT_GHEIST, TYRANT_DESECRATOR, TYRANT_DESECRATOR,
    },
}

# ── Magaera / Styrix ─────────────────────────────────────────────────────
MAGAERA_MAIN = {"Lightning cannon", "Phased plasma-fusil"}
STYRIX_MAIN = {"Graviton crusher", "Volkite chierovile"}
RAD_CLEANSER = "Twin rad cleanser"
CHAIN = "Reaper chainsword"
CLAW = "Hekaton siege claw"

# ── Moirax ───────────────────────────────────────────────────────────────
MOIRAX_FEET = "Armoured feet"
MOIRAX_SINGLES = {"Volkite veuglaire", "Conversion beam cannon", "Graviton pulsar",
                  "Lightning lock"}
MOIRAX_CLAW = {"Rad cleanser", "Siege claw"}
# 5 doubles + 10 pairs = 15
MOIRAX_ARM_NAMES = ["volkite", "conversion", "graviton", "lightning", "claw"]
MOIRAX_COUNT = 15

# ── Stalker slots ────────────────────────────────────────────────────────
STALKER_SLOTS = {
    "Carapace weapon": {"Diabolus heavy stubber", "Havoc multi-launcher"},
    "Chaincannon/spear": {"Avenger chaincannon", "Daemonbreath spear"},
    "Slaughterclaw/chaintalon": {"Slaughterclaw", "Reaper chaintalon"},
}


def _build_weapons(build) -> set[str]:
    """All weapon names named by a build (fixed + slot choices)."""
    names = {f["name"] for f in build.get("fixed", [])}
    for slot in build.get("slots", []):
        names.update(c["name"] for c in slot.get("choices", []))
    return names


@pytest.fixture(scope="module")
def engine():
    return RankingEngine("chaos-knights")


@pytest.fixture(scope="module")
def chars():
    return json.load(open(CHARS))


@pytest.fixture(scope="module")
def wopt():
    return json.load(open(WEAPON_OPTIONS))


def _assert_slots_schema(build, name):
    assert {"fixed", "slots"}.issubset(build.keys()), f"{name}: no slots schema"
    legacy = {"ranged", "melee", "ranged_choices", "melee_choices",
              "max_ranged", "max_melee"} & set(build.keys())
    assert not legacy, f"{name}: legacy keys {legacy}"


def _resolve(engine, build, unit_name, target_name="MEQ"):
    """Resolve one build via the engine's slots path -> (ranged, melee) names."""
    r, m, _n = engine._resolve_slots_build(
        build, unit_name, engine.resolve_target(target_name))
    return [w.name for w in r], [w.name for w in m]


class TestTyrantBuilds:
    """Knight Tyrant — 4 legal combos (2 main x 2 carapace), ecto not double-counted."""

    def test_exact_build_names(self, chars):
        builds = chars["Knight Tyrant"]["weapon_options"]["builds"]
        assert [b["name"] for b in builds] == list(TYRANT_EXPECTED.keys())

    def test_slots_schema(self, chars):
        for b in chars["Knight Tyrant"]["weapon_options"]["builds"]:
            _assert_slots_schema(b, b["name"])

    def test_no_ecto_profiles_fixed(self, chars):
        """The old config fixed '- standard' AND '- supercharge' (ranged sum =
        double count). Only the group entry may appear — never the raw profiles."""
        for b in chars["Knight Tyrant"]["weapon_options"]["builds"]:
            fixed = {f["name"] for f in b["fixed"]}
            assert "Ectoplasma decimator - standard" not in fixed, b["name"]
            assert "Ectoplasma decimator - supercharge" not in fixed, b["name"]
            if b["name"].startswith("volcano"):
                assert TYRANT_ECTO in fixed, f"{b['name']}: ecto group missing"
            else:
                assert TYRANT_ECTO not in fixed, f"{b['name']}: ecto in darkflame build"

    def test_fixed_inventories(self, chars):
        by_name = {b["name"]: b for b in chars["Knight Tyrant"]["weapon_options"]["builds"]}
        for name, expected in TYRANT_EXPECTED.items():
            b = by_name[name]
            fixed = frozenset(f["name"] for f in b["fixed"])
            assert fixed == expected, f"{name}: {fixed} != {expected}"
            assert b["slots"] == [], f"{name}: unexpected slots"

    def test_all_names_resolve(self, engine, chars):
        for b in chars["Knight Tyrant"]["weapon_options"]["builds"]:
            for name in _build_weapons(b):
                try:
                    engine.W(name, unit_name="Knight Tyrant")
                except KeyError:
                    pytest.fail(f"{b['name']}: weapon '{name}' does not resolve")

    def test_every_build_resolves(self, engine, chars):
        for b in chars["Knight Tyrant"]["weapon_options"]["builds"]:
            ranged, melee = _resolve(engine, b, "Knight Tyrant")
            assert len(ranged) == 7, f"{b['name']}: ranged {len(ranged)}"
            assert len(melee) == 1 and melee[0] == TYRANT_FEET, f"{b['name']}: melee {melee}"


class TestMagaeraStyrixBuilds:
    """2 builds each: chainsword (no rad cleanser) / hekaton (claw + rad cleanser)."""

    @pytest.mark.parametrize("unit,main", [
        ("Chaos Questoris Knight Magaera", MAGAERA_MAIN),
        ("Chaos Questoris Knight Styrix", STYRIX_MAIN),
    ])
    def test_exact_build_names(self, chars, unit, main):
        builds = chars[unit]["weapon_options"]["builds"]
        assert [b["name"] for b in builds] == ["chainsword", "hekaton"]

    @pytest.mark.parametrize("unit", ["Chaos Questoris Knight Magaera",
                                      "Chaos Questoris Knight Styrix"])
    def test_no_feet_no_mandatory_rad(self, chars, unit):
        """No Titanic feet (BSData has none); rad cleanser is NOT in chainsword."""
        for b in chars[unit]["weapon_options"]["builds"]:
            fixed = {f["name"] for f in b["fixed"]}
            assert "Titanic feet" not in fixed, f"{unit}/{b['name']}: has feet"
            if b["name"] == "chainsword":
                assert RAD_CLEANSER not in fixed, f"{unit}/chainsword: rad cleanser leaked"
                assert CHAIN in fixed
            else:
                assert RAD_CLEANSER in fixed and CLAW in fixed

    @pytest.mark.parametrize("unit,main", [
        ("Chaos Questoris Knight Magaera", MAGAERA_MAIN),
        ("Chaos Questoris Knight Styrix", STYRIX_MAIN),
    ])
    def test_main_weapons_always_fixed(self, chars, unit, main):
        for b in chars[unit]["weapon_options"]["builds"]:
            fixed = {f["name"] for f in b["fixed"]}
            assert main <= fixed, f"{unit}/{b['name']}: main weapons {main - fixed} missing"

    @pytest.mark.parametrize("unit", ["Chaos Questoris Knight Magaera",
                                      "Chaos Questoris Knight Styrix"])
    def test_all_names_resolve(self, engine, chars, unit):
        for b in chars[unit]["weapon_options"]["builds"]:
            for name in _build_weapons(b):
                try:
                    engine.W(name, unit_name=unit)
                except KeyError:
                    pytest.fail(f"{unit}/{b['name']}: '{name}' does not resolve")

    @pytest.mark.parametrize("unit", ["Chaos Questoris Knight Magaera",
                                      "Chaos Questoris Knight Styrix"])
    def test_loadout_resolves_per_target(self, engine, unit):
        for t in TARGET_SAMPLES:
            res = engine.resolve_loadout(unit, engine.resolve_target(t))
            assert res is not None, f"{unit}: no loadout for {t}"


class TestWave3CerastusAndMiscBuilds:
    """Wave-3 (2026-08-15) audit locks: Cerastus x3 + Rampager/Ruinator/Abominant.

    All are fixed loadouts with NO BSData choice slots (0-slot end-state is
    correct). Melee weapons reference GROUP names — never '- strike'/'- sweep'
    profile pairs. The group entry resolves with variants the engine maxes
    (melee path); profile pairs were the pre-slots pattern and are the same
    double-entry class the IK lock forbids in ranged.
    """

    FIXED_INVENTORIES = {
        "Chaos Cerastus Knight Acheron": {
            "Acheron flame cannon", "Twin heavy bolter", "Reaper chainfist"},
        "Chaos Cerastus Knight Castigator": {
            "Castigator bolt cannon", "Tempest warblade"},
        "Knight Rampager": {
            "Diabolus heavy stubber", "Reaper chainsword", "Warpstrike claw"},
        "Knight Ruinator": {
            "Darkflame lance", "Terrorpulse missiles", "Fellbore"},
        "Knight Abominant": {
            "Diabolus heavy stubber", "Volkite combustor", "Balemace", "Electroscourge"},
    }

    @pytest.mark.parametrize("unit,expected", FIXED_INVENTORIES.items())
    def test_fixed_inventory(self, chars, unit, expected):
        build = chars[unit]["weapon_options"]["builds"][0]
        names = {f["name"] for f in build["fixed"]}
        assert names == expected, f"{unit}: {names}"
        assert build["slots"] == [], f"{unit}: unexpected slots"

    @pytest.mark.parametrize("unit", FIXED_INVENTORIES.keys())
    def test_no_profile_suffixes(self, chars, unit):
        for b in chars[unit]["weapon_options"]["builds"]:
            for f in b["fixed"]:
                assert " - " not in f["name"], f"{unit}: profile entry '{f['name']}'"

    @pytest.mark.parametrize("unit", FIXED_INVENTORIES.keys())
    def test_all_names_resolve(self, engine, chars, unit):
        for b in chars[unit]["weapon_options"]["builds"]:
            for name in _build_weapons(b):
                try:
                    engine.W(name, unit_name=unit)
                except KeyError:
                    pytest.fail(f"{unit}/{b['name']}: '{name}' does not resolve")

    def test_lancer_dual_profile(self, engine, chars):
        """Shock lance is ranged (12" A6 S6) AND melee (strike/sweep)."""
        build = chars["Chaos Cerastus Knight Lancer"]["weapon_options"]["builds"][0]
        ranged, melee = _resolve(engine, build, "Chaos Cerastus Knight Lancer")
        assert any("shock lance" in n for n in ranged), f"no ranged lance: {ranged}"
        assert any("shock lance" in n for n in melee), f"no melee lance: {melee}"

    def test_lancer_inventory(self, chars):
        """One ranged group entry + one melee group entry, no profile pairs."""
        build = chars["Chaos Cerastus Knight Lancer"]["weapon_options"]["builds"][0]
        names = [f["name"] for f in build["fixed"]]
        assert names == ["Cerastus shock lance", "Cerastus shock lance"], names
        assert sorted(f["type"] for f in build["fixed"]) == ["melee", "ranged"]
        assert build["slots"] == []


class TestPorphyrion:
    """Fixed 2x magna + feet; carapace slot + TWO shoulder slots (duplicates legal)."""

    def test_slots_schema(self, wopt):
        b = wopt["Chaos Acastus Knight Porphyrion"]["builds"][0]
        _assert_slots_schema(b, "Porphyrion")

    def test_fixed_and_slots(self, wopt):
        b = wopt["Chaos Acastus Knight Porphyrion"]["builds"][0]
        fixed = {f["name"] for f in b["fixed"]}
        assert fixed == {"Twin magna lascannon", "Titanic feet"}
        assert len([f for f in b["fixed"] if f["name"] == "Twin magna lascannon"]) == 2
        slots = {s["name"]: {c["name"] for c in s["choices"]} for s in b["slots"]}
        assert slots.get("Carapace weapon") == {"Acastus ironstorm missile pod",
                                                "Helios defence missiles"}
        for sname in ("Shoulder weapon 1", "Shoulder weapon 2"):
            assert slots.get(sname) == {"Acastus autocannon", "Lascannon"}, sname

    def test_loadout_resolves(self, engine):
        for t in TARGET_SAMPLES:
            res = engine.resolve_loadout("Chaos Acastus Knight Porphyrion",
                                         engine.resolve_target(t))
            assert res is not None and len(res[1]) == 5, f"Porphyrion {t}"


class TestAsterius:
    """Fixed: 2x volkite, karacnos, 2x conversion beam, feet — no slots."""

    def test_pair_weapons_doubled(self, wopt):
        b = wopt["Chaos Acastus Knight Asterius"]["builds"][0]
        fixed = [f["name"] for f in b["fixed"]]
        assert fixed.count("Asterius volkite culverin") == 2
        assert fixed.count("Twin conversion beam cannon") == 2
        assert fixed.count("Karacnos mortar battery") == 1
        assert "Titanic feet" in fixed
        assert b["slots"] == []

    def test_loadout_resolves(self, engine):
        for t in TARGET_SAMPLES:
            res = engine.resolve_loadout("Chaos Acastus Knight Asterius",
                                         engine.resolve_target(t))
            assert res is not None and len(res[1]) == 5, f"Asterius {t}"


class TestWarDogs:
    """Brigand/Executioner/Huntsman/Karnivore: fixed weapons + carapace slot."""

    @pytest.mark.parametrize("unit,fixed_expected,carapace_expected,has_feet", [
        ("War Dog Brigand", {"Avenger chaincannon", "Daemonbreath spear"},
         {"Diabolus heavy stubber", "Havoc multi-launcher"}, True),
        ("War Dog Executioner", {"War Dog autocannon"},
         {"Diabolus heavy stubber", "Daemonbreath meltagun"}, True),
        ("War Dog Huntsman", {"Daemonbreath spear", "Reaper chaintalon"},
         {"Diabolus heavy stubber", "Daemonbreath meltagun"}, False),
        ("War Dog Karnivore", {"Reaper chaintalon", "Slaughterclaw"},
         {"Diabolus heavy stubber", "Havoc multi-launcher"}, False),
    ])
    def test_war_dog_config(self, wopt, unit, fixed_expected, carapace_expected, has_feet):
        b = wopt[unit]["builds"][0]
        _assert_slots_schema(b, unit)
        fixed = {f["name"] for f in b["fixed"]}
        assert fixed_expected <= fixed, f"{unit}: missing {fixed_expected - fixed}"
        assert ("Armoured feet" in fixed) == has_feet, f"{unit}: feet mismatch"
        slots = {s["name"]: {c["name"] for c in s["choices"]} for s in b["slots"]}
        assert slots == {"Carapace weapon": carapace_expected}, f"{unit}: slots {slots}"

    @pytest.mark.parametrize("unit", ["War Dog Brigand", "War Dog Executioner",
                                      "War Dog Huntsman", "War Dog Karnivore"])
    def test_loadout_resolves(self, engine, unit):
        for t in TARGET_SAMPLES:
            res = engine.resolve_loadout(unit, engine.resolve_target(t))
            assert res is not None, f"{unit}: no loadout for {t}"


class TestStalker:
    """No fixed weapons — exactly 3 independent slots."""

    def test_three_slots_no_fixed(self, wopt):
        b = wopt["War Dog Stalker"]["builds"][0]
        _assert_slots_schema(b, "Stalker")
        assert b["fixed"] == [], "Stalker: unexpected fixed weapons"
        slots = {s["name"]: {c["name"] for c in s["choices"]} for s in b["slots"]}
        assert slots == STALKER_SLOTS, f"Stalker: slots {slots}"

    def test_loadout_resolves(self, engine):
        for t in TARGET_SAMPLES:
            res = engine.resolve_loadout("War Dog Stalker", engine.resolve_target(t))
            assert res is not None and len(res[1]) >= 1, f"Stalker {t}"


class TestMoirax:
    """15 builds (5 doubles + 10 pairs). Claw bundle split into Rad cleanser + Siege claw."""

    def test_exact_build_count(self, wopt):
        builds = wopt["War Dog Moirax"]["builds"]
        assert len(builds) == MOIRAX_COUNT, f"Moirax: {len(builds)} builds"

    def test_double_and_pair_coverage(self, wopt):
        builds = wopt["War Dog Moirax"]["builds"]
        names = {b["name"] for b in builds}
        # 5 doubles
        for a in MOIRAX_ARM_NAMES:
            assert f"moirax_{a}_{a}" in names, a
        # 10 pairs
        for i in range(5):
            for j in range(i + 1, 5):
                assert f"moirax_{MOIRAX_ARM_NAMES[i]}_{MOIRAX_ARM_NAMES[j]}" in names

    def test_claw_arms_carry_both_components(self, wopt):
        for b in wopt["War Dog Moirax"]["builds"]:
            if "claw" not in b["name"]:
                continue
            fixed = [f["name"] for f in b["fixed"]]
            n_claw = b["name"].count("claw")
            assert fixed.count("Rad cleanser") == n_claw, b["name"]
            assert fixed.count("Siege claw") == n_claw, b["name"]

    def test_every_build_has_feet_and_two_arms(self, wopt):
        for b in wopt["War Dog Moirax"]["builds"]:
            fixed = [f["name"] for f in b["fixed"]]
            assert MOIRAX_FEET in fixed, b["name"]
            arms = [n for n in fixed if n != MOIRAX_FEET]
            # A claw arm contributes TWO entries (Rad cleanser + Siege claw);
            # any other arm contributes ONE. Two arms total per build.
            n_claw = b["name"].count("claw")
            assert len(arms) == n_claw * 2 + (2 - n_claw), (
                f"{b['name']}: arms {arms} (expected {n_claw * 2 + (2 - n_claw)})")

    def test_all_names_resolve(self, engine, wopt):
        for b in wopt["War Dog Moirax"]["builds"]:
            for name in _build_weapons(b):
                try:
                    engine.W(name, unit_name="War Dog Moirax")
                except KeyError:
                    pytest.fail(f"{b['name']}: '{name}' does not resolve")

    def test_loadout_resolves(self, engine):
        for t in TARGET_SAMPLES:
            res = engine.resolve_loadout("War Dog Moirax", engine.resolve_target(t))
            assert res is not None, f"Moirax: no loadout for {t}"
