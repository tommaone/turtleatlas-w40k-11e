"""Regression lock for the Imperial Knights character slot migration (2026-08-13).

Locks the curated character builds to the BSData truth (verified against the
"Imperium - Imperial Knights - Library" catalogue) and to the Chaos Knights
slot-schema precedent:

- Atrapos: GROUP entries only ('Atrapos lascutter' ranged+melee,
  'Graviton singularity cannon' ranged). The old config fixed both
  '- high intensity' / '- low intensity' (ranged) AND '- singularity' /
  '- contained' — DOUBLE-COUNTING the choice profiles in ranged.
- Canis Rex: 'Las-impulsor' group (was '- high/low intensity' ranged pair,
  summed). Freedom's Hand group (strike/sweep are maxed by the engine, but
  the group name is the clean reference). Sir Hekhtur (pistol + CCW) is a
  SEPARATE model in the unit — only fights after the Knight dies — so his
  weapons are NOT in the Knight's loadout.
- Castellan: 'Plasma decimator' group (was '- standard'/'supercharge' pair).
- Defender: 'Plasma executor' group (same bug class).
- Preceptor: 'Las-impulsor' group + now has Preceptor Multi-laser,
  Carapace-mounted Weapon AND Reaper Chainsword slots (old config had the
  multi-laser slot only, no melee at all).
- Questoris knights (Crusader/Errant/Gallant/Paladin/Warden): full BSData
  slots — Carapace-mounted Weapon + Meltagun (+ Reaper Chainsword where
  BSData offers it). 'Icarus autocannons' is used in the carapace slot
  because BSData's 'Twin Icarus autocannon' does NOT resolve in the merged
  catalog (loader gap); 'Icarus autocannons' is the same profile (A3 S7).
- Magaera / Styrix: 2 builds each (chainsword / hekaton) mirroring CK — the
  'Hekaton siege claw and twin rad cleanser' bundle is SPLIT into
  components (Twin rad cleanser + Hekaton siege claw), Despoiler precedent;
  bundle names resolve to primary profile only.
- Castellan / Valiant: carapace bundles (2 shieldbreakers + 1 siegebreaker
  OR 1 + 2) modeled as 2 builds each with the components split into fixed —
  same precedent. Twin meltagun is min2/max2 on BSData, so both builds
  carry exactly 2 (each A1); the old config carried 1.

STRUCTURE AND RESOLVABILITY ONLY — no damage values. The engine is the
single source of computation; this test locks config shape, not math.

Run: python3 -m pytest tests/test_imperial_knights_slots_migration.py -v
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.ranking import RankingEngine

CONFIG_DIR = Path(__file__).resolve().parent.parent / "data" / "config"
CHARS = CONFIG_DIR / "imperial-knights" / "characters.json"
WEAPON_OPTIONS = CONFIG_DIR / "imperial-knights" / "weapon_options.json"

# ── Fixed double-count weapons (must be GROUP names only) ───────────────
GROUP_NAMES = {
    "Canis Rex": {"Las-impulsor", "Freedom's Hand"},
    "Cerastus Knight Atrapos": {"Atrapos lascutter", "Graviton singularity cannon"},
    "Knight Castellan": {"Plasma decimator"},
    "Knight Defender": {"Plasma executor"},
    "Knight Preceptor": {"Las-impulsor"},
}

# Profile names that must NEVER appear in fixed (they'd double-count ranged).
FORBIDDEN_PROFILES = [
    " - high intensity",
    " - low intensity",
    " - standard",
    " - supercharge",
    " - singularity",
    " - contained",
    " - strike",
    " - sweep",
]

# ── Atrapos ──────────────────────────────────────────────────────────────
ATRAPOS_LAS = "Atrapos lascutter"
ATRAPOS_GRAV = "Graviton singularity cannon"

# ── Questoris slots ──────────────────────────────────────────────────────
CARAPACE_SLOT = "Carapace-mounted Weapon"
CARAPACE_CHOICES = {"Icarus autocannons", "Ironstorm missile pod", "Stormspear rocket pod"}
MELTAGUN_SLOT = "Meltagun"
MELTAGUN_CHOICES = {"Meltagun", "Questoris heavy stubber"}
CHAIN_SLOT = "Reaper Chainsword"
CHAIN_CHOICES = {"Reaper chainsword", "Thunderstrike gauntlet"}

# Units that must carry the carapace + meltagun slots (+ chain where BSData has it)
QUESTORIS_SLOTTED = {
    "Knight Crusader": {"Thermal Cannon", CARAPACE_SLOT, MELTAGUN_SLOT},
    "Knight Errant": {CARAPACE_SLOT, MELTAGUN_SLOT, CHAIN_SLOT},
    "Knight Gallant": {CARAPACE_SLOT, MELTAGUN_SLOT},
    "Knight Paladin": {CARAPACE_SLOT, MELTAGUN_SLOT, CHAIN_SLOT},
    "Knight Preceptor": {"Preceptor Multi-laser", CARAPACE_SLOT, CHAIN_SLOT},
    "Knight Warden": {CARAPACE_SLOT, MELTAGUN_SLOT, CHAIN_SLOT},
}

# ── Magaera / Styrix ─────────────────────────────────────────────────────
MAGAERA_MAIN = {"Lightning cannon", "Phased plasma-fusil"}
STYRIX_MAIN = {"Graviton crusher", "Volkite chierovile"}
RAD_CLEANSER = "Twin rad cleanser"
CHAIN = "Reaper chainsword"
CLAW = "Hekaton siege claw"

# ── Castellan / Valiant carapace: 2-build bundles ────────────────────────
# BSData 'Carapace-mounted Weapons' (min1/max1) offers two bundles:
#   - 2 shieldbreaker missile launchers + 1 twin siegebreaker cannon
#   - 1 shieldbreaker missile launcher + 2 twin siegebreaker cannons
# Bundle names don't resolve in the merged catalog; the components DO
# (Shieldbreaker missile launcher A1, Twin siegebreaker cannon D6) — the
# Despoiler split precedent. Each bundle is modeled as a build with the
# components split into fixed.
CARAPACE_BUILDS = ("shieldbreaker_heavy", "siegebreaker_heavy")
CARAPACE_COMPONENTS = {"Shieldbreaker missile launcher", "Twin siegebreaker cannon"}


def _build_weapons(build) -> set[str]:
    """All weapon names named by a build (fixed + slot choices)."""
    names = {f["name"] for f in build.get("fixed", [])}
    for slot in build.get("slots", []):
        names.update(c["name"] for c in slot.get("choices", []))
    return names


@pytest.fixture(scope="module")
def engine():
    return RankingEngine("imperial-knights")


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


class TestGroupNameMigration:
    """No choice-profile names in fixed — group names only (ranged no double-count)."""

    @pytest.mark.parametrize("unit,groups", GROUP_NAMES.items())
    def test_group_names_in_fixed(self, chars, unit, groups):
        build = chars[unit]["weapon_options"]["builds"][0]
        fixed = {f["name"] for f in build["fixed"]}
        for g in groups:
            assert g in fixed, f"{unit}: group '{g}' missing from fixed"

    @pytest.mark.parametrize("unit", GROUP_NAMES.keys())
    def test_no_profile_suffixed_fixed(self, chars, unit):
        build = chars[unit]["weapon_options"]["builds"][0]
        for f in build["fixed"]:
            for forbidden in FORBIDDEN_PROFILES:
                assert forbidden not in f["name"], (
                    f"{unit}: profile entry '{f['name']}' in fixed (double-count risk)"
                )


class TestAtrapos:
    """Mirror of the Chaos Atrapos lock: lascutter in BOTH lists (dual-profile)."""

    def test_fixed_inventory(self, chars):
        build = chars["Cerastus Knight Atrapos"]["weapon_options"]["builds"][0]
        fixed = frozenset(f["name"] for f in build["fixed"])
        assert fixed == {ATRAPOS_LAS, ATRAPOS_GRAV}, fixed
        assert build["slots"] == []

    def test_lascutter_dual_profile(self, engine, chars):
        """Lascutter contributes to ranged AND melee; category passes through."""
        build = chars["Cerastus Knight Atrapos"]["weapon_options"]["builds"][0]
        ranged, melee = _resolve(engine, build, "Cerastus Knight Atrapos")
        assert any("lascutter" in n for n in ranged), f"no ranged lascutter: {ranged}"
        assert any("lascutter" in n for n in melee), f"no melee lascutter: {melee}"


class TestQuestorisSlots:
    """Crusader/Errant/Gallant/Paladin/Preceptor/Warden carry BSData slot structure."""

    @pytest.mark.parametrize("unit,expected_slots", QUESTORIS_SLOTTED.items())
    def test_slot_names_present(self, chars, unit, expected_slots):
        build = chars[unit]["weapon_options"]["builds"][0]
        slot_names = {s["name"] for s in build["slots"]}
        assert expected_slots.issubset(slot_names), (
            f"{unit}: missing {expected_slots - slot_names} (have {slot_names})"
        )

    @pytest.mark.parametrize("unit", [
        "Knight Crusader", "Knight Errant", "Knight Gallant",
        "Knight Paladin", "Knight Warden",
    ])
    def test_carapace_and_meltagun_choices(self, chars, unit):
        build = chars[unit]["weapon_options"]["builds"][0]
        by_name = {s["name"]: {c["name"] for c in s["choices"]} for s in build["slots"]}
        if CARAPACE_SLOT in by_name:
            assert by_name[CARAPACE_SLOT] == CARAPACE_CHOICES, unit
        assert by_name[MELTAGUN_SLOT] == MELTAGUN_CHOICES, unit

    @pytest.mark.parametrize("unit", ["Knight Errant", "Knight Paladin", "Knight Warden"])
    def test_chain_slot_choices(self, chars, unit):
        build = chars[unit]["weapon_options"]["builds"][0]
        by_name = {s["name"]: {c["name"] for c in s["choices"]} for s in build["slots"]}
        assert by_name[CHAIN_SLOT] == CHAIN_CHOICES, unit

    def test_preceptor_has_melee_slot(self, chars):
        """Old config had NO melee at all — a Preceptor always carries a chainsword/gauntlet."""
        build = chars["Knight Preceptor"]["weapon_options"]["builds"][0]
        by_name = {s["name"]: {c["name"] for c in s["choices"]} for s in build["slots"]}
        assert by_name[CHAIN_SLOT] == CHAIN_CHOICES


class TestMagaeraStyrixBuilds:
    """2 builds each: chainsword (no rad cleanser) / hekaton (claw + rad cleanser)."""

    @pytest.mark.parametrize("unit,main", [
        ("Questoris Knight Magaera", MAGAERA_MAIN),
        ("Questoris Knight Styrix", STYRIX_MAIN),
    ])
    def test_exact_build_names(self, chars, unit, main):
        builds = chars[unit]["weapon_options"]["builds"]
        assert [b["name"] for b in builds] == ["chainsword", "hekaton"]

    @pytest.mark.parametrize("unit,main", [
        ("Questoris Knight Magaera", MAGAERA_MAIN),
        ("Questoris Knight Styrix", STYRIX_MAIN),
    ])
    def test_build_inventories(self, chars, unit, main):
        by_name = {b["name"]: b for b in chars[unit]["weapon_options"]["builds"]}
        chain = frozenset({*main, CHAIN})
        hekaton = frozenset({*main, RAD_CLEANSER, CLAW})
        assert frozenset(f["name"] for f in by_name["chainsword"]["fixed"]) == chain
        assert frozenset(f["name"] for f in by_name["hekaton"]["fixed"]) == hekaton
        assert by_name["chainsword"]["slots"] == []
        assert by_name["hekaton"]["slots"] == []


class TestDominusCarapaceBuilds:
    """Castellan/Valiant: 2 carapace bundles, split into component builds."""

    @pytest.mark.parametrize("unit", ["Knight Castellan", "Knight Valiant"])
    def test_exact_build_names(self, chars, unit):
        builds = chars[unit]["weapon_options"]["builds"]
        assert [b["name"] for b in builds] == list(CARAPACE_BUILDS), unit

    @pytest.mark.parametrize("unit", ["Knight Castellan", "Knight Valiant"])
    def test_carapace_components_present(self, chars, unit):
        """Each build's fixed must carry BOTH carapace components (split bundles)."""
        for b in chars[unit]["weapon_options"]["builds"]:
            names = {f["name"] for f in b["fixed"]}
            assert CARAPACE_COMPONENTS.issubset(names), f"{unit}/{b['name']}: {names}"
            assert b["slots"] == [], f"{unit}/{b['name']}: unexpected slots"

    @pytest.mark.parametrize("unit", ["Knight Castellan", "Knight Valiant"])
    def test_bundle_counts(self, chars, unit):
        """2 shieldbreakers + 1 siegebreaker vs 1 + 2 — exact component counts."""
        from collections import Counter
        by_name = {b["name"]: b for b in chars[unit]["weapon_options"]["builds"]}
        sb = Counter(f["name"] for f in by_name["shieldbreaker_heavy"]["fixed"])
        sg = Counter(f["name"] for f in by_name["siegebreaker_heavy"]["fixed"])
        assert sb["Shieldbreaker missile launcher"] == 2, sb
        assert sb["Twin siegebreaker cannon"] == 1, sb
        assert sg["Shieldbreaker missile launcher"] == 1, sg
        assert sg["Twin siegebreaker cannon"] == 2, sg


class TestResolvability:
    """Every config weapon resolves in the merged catalog; every unit resolves."""

    @pytest.mark.parametrize("unit", [
        "Canis Rex", "Cerastus Knight Acheron", "Cerastus Knight Atrapos",
        "Cerastus Knight Castigator", "Cerastus Knight Lancer",
        "Knight Castellan", "Knight Crusader", "Knight Defender",
        "Knight Destrier", "Knight Errant", "Knight Gallant", "Knight Paladin",
        "Knight Preceptor", "Knight Valiant", "Knight Warden",
        "Questoris Knight Magaera", "Questoris Knight Styrix",
    ])
    def test_char_all_names_resolve(self, engine, chars, unit):
        for b in chars[unit]["weapon_options"]["builds"]:
            for name in _build_weapons(b):
                try:
                    engine.W(name, unit_name=unit)
                except KeyError:
                    pytest.fail(f"{unit}/{b['name']}: '{name}' does not resolve")

    def test_wo_all_names_resolve(self, engine, wopt):
        for unit, cfg in wopt.items():
            if unit.startswith("_"):
                continue
            for b in cfg.get("builds", []):
                for name in _build_weapons(b):
                    try:
                        engine.W(name, unit_name=unit)
                    except KeyError:
                        pytest.fail(f"{unit}/{b['name']}: '{name}' does not resolve")

    @pytest.mark.parametrize("unit", [
        "Canis Rex", "Cerastus Knight Acheron", "Cerastus Knight Atrapos",
        "Cerastus Knight Castigator", "Cerastus Knight Lancer",
        "Knight Castellan", "Knight Crusader", "Knight Defender",
        "Knight Destrier", "Knight Errant", "Knight Gallant", "Knight Paladin",
        "Knight Preceptor", "Knight Valiant", "Knight Warden",
        "Questoris Knight Magaera", "Questoris Knight Styrix",
    ])
    def test_char_builds_resolve(self, engine, chars, unit):
        for b in chars[unit]["weapon_options"]["builds"]:
            ranged, melee = _resolve(engine, b, unit)
            assert ranged or melee, f"{unit}/{b['name']}: resolved to empty"

    def test_wo_builds_resolve(self, engine, wopt):
        for unit, cfg in wopt.items():
            if unit.startswith("_"):
                continue
            for b in cfg.get("builds", []):
                ranged, melee = _resolve(engine, b, unit)
                assert ranged or melee, f"{unit}/{b['name']}: resolved to empty"
