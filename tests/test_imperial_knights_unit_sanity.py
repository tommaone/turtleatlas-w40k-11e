"""Per-unit sanity locks for the Imperial Knights slot migration.

Mirrors the Chaos Knights per-unit verification depth (Despoiler build
inventory + Atrapos profile-selection): each unit with a complex slot
system gets its exact canonical fixed inventory and slot structure locked
against the BSData truth (verified 2026-08-13 against "Imperium - Imperial
Knights - Library" + MFM):

- Canis Rex: 5 fixed weapons (2-model unit: Canis Rex + Sir Hekhtur);
  Las-impulsor group, never '- high/low intensity'.
- Atrapos: lascutter DUAL-profile — contributes to ranged AND melee; the
  ranged list must carry the ranged profile (A < 10), melee the melee
  profile (A >= 10). Category pass-through regression.
- Questoris knights: exact fixed inventory per unit; Crusader/Errant/
  Gallant/Paladin/Warden/Preceptor carry Carapace-mounted Weapon +
  Meltagun (+ Reaper Chainsword) slots per BSData.
- Acastus: Asterius 2x Twin conversion beam + 2x volkite + karacnos;
  Porphyrion 2x Twin magna lascannon + Carapace + TWO independent Shoulder
  weapon slots (min2/max2 group — duplicates legal).
- Armigers: Helverin 2x Armiger autocannon; Warglaive Thermal spear +
  Reaper chain-cleaver; both carry the Heavy Stubber slot. Moirax: exactly
  15 builds (5 doubles + 10 pairs), claw builds split into
  Rad cleanser + Siege claw.
- Castellan/Valiant: fixed only — carapace slot NOT modeled (BSData
  shieldbreaker/siegebreaker bundle names don't resolve in the merged
  catalog; documented gap).

STRUCTURE AND PROFILE SELECTION ONLY — no damage values. The engine is
the single source of computation; these tests lock config shape, profile
category and resolvability, not math.

Run: python3 -m pytest tests/test_imperial_knights_unit_sanity.py -v
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

TITANIC = "Titanic feet"

# Canonical weapon names (as they appear in the merged catalogue)
LAS = "Las-impulsor"
FREEDOM = "Freedom's Hand"
GRAV = "Graviton singularity cannon"
ATRAPOS_LAS = "Atrapos lascutter"
PLASMA_DEC = "Plasma decimator"
PLASMA_EXEC = "Plasma executor"

CARAPACE_SLOT = "Carapace-mounted Weapon"
MELTAGUN_SLOT = "Meltagun"
CHAIN_SLOT = "Reaper Chainsword"
CARAPACE_CHOICES = {"Icarus autocannons", "Ironstorm missile pod", "Stormspear rocket pod"}
MELTAGUN_CHOICES = {"Meltagun", "Questoris heavy stubber"}
CHAIN_CHOICES = {"Reaper chainsword", "Thunderstrike gauntlet"}

# ── Canis Rex ────────────────────────────────────────────────────────────
CANIS_FIXED = {
    LAS, "Questoris multi-laser", "Hekhtur's pistol", FREEDOM,
    "Close combat weapon",
}

# ── Questoris fixed inventories (ranged+melee, in any order) ─────────────
QUESTORIS_FIXED = {
    "Knight Crusader": {"Avenger gatling cannon", "Heavy flamer", TITANIC},
    "Knight Errant": {"Thermal cannon"},
    "Knight Gallant": {"Reaper chainsword", "Thunderstrike gauntlet"},
    "Knight Paladin": {"Questoris heavy stubber", "Rapid-fire battle cannon"},
    "Knight Preceptor": {LAS},
    "Knight Warden": {"Avenger gatling cannon", "Heavy flamer"},
    "Knight Castellan": {PLASMA_DEC, "Volcano lance", "Twin meltagun", TITANIC},
    "Knight Defender": {"Twin incendine combustor", "Conversion beam obliterator",
                        PLASMA_EXEC, "Phosphor blaster", TITANIC},
    "Knight Valiant": {"Conflagration cannon", "Thundercoil harpoon",
                       "Twin meltagun", TITANIC},
    "Knight Destrier": {"Questoris heavy stubber", TITANIC},
}

# ── Questoris slot structure (which slots each unit must carry) ──────────
QUESTORIS_SLOTS = {
    "Knight Crusader": {"Thermal Cannon", CARAPACE_SLOT, MELTAGUN_SLOT},
    "Knight Errant": {CARAPACE_SLOT, MELTAGUN_SLOT, CHAIN_SLOT},
    "Knight Gallant": {CARAPACE_SLOT, MELTAGUN_SLOT},
    "Knight Paladin": {CARAPACE_SLOT, MELTAGUN_SLOT, CHAIN_SLOT},
    "Knight Preceptor": {"Preceptor Multi-laser", CARAPACE_SLOT, CHAIN_SLOT},
    "Knight Warden": {CARAPACE_SLOT, MELTAGUN_SLOT, CHAIN_SLOT},
    # Castellan/Valiant: fixed-only by design (carapace catalog gap)
    "Knight Castellan": set(),
    "Knight Valiant": set(),
}

# ── Destrier slots (mixed melee/ranged arm choices) ──────────────────────
DESTRIER_SLOTS = {
    "Chastiser Gatling Cannon": {"Bellatus reaper chainsword",
                                 "Thundershock spear", "Chastiser gatling cannon"},
    "Frag Bombard": {"Thundershock spear", "Bellatus reaper chainsword",
                     "Frag bombard"},
}

# ── Acastus ──────────────────────────────────────────────────────────────
ASTERIUS_FIXED = {
    "Twin conversion beam cannon", "Twin conversion beam cannon",
    "Asterius volkite culverin", "Asterius volkite culverin",
    "Karacnos mortar battery", TITANIC,
}
PORPHYRION_FIXED = {"Twin magna lascannon", "Twin magna lascannon", TITANIC}
PORPHYRION_SLOTS = {
    "Carapace weapon": {"Acastus ironstorm missile pod", "Helios defence missiles"},
    "Shoulder weapon 1": {"Acastus autocannon", "Lascannon"},
    "Shoulder weapon 2": {"Acastus autocannon", "Lascannon"},
}

# ── Armigers ─────────────────────────────────────────────────────────────
HELVERIN_FIXED = {"Armiger autocannon", "Armiger autocannon", "Armoured feet"}
WARGLIAVE_FIXED = {"Thermal spear", "Reaper chain-cleaver"}
STUBBER_SLOT = "Heavy Stubber"
STUBBER_CHOICES = {"Meltagun", "Questoris heavy stubber"}

# ── Moirax ───────────────────────────────────────────────────────────────
MOIRAX_FEET = "Armoured feet"
MOIRAX_SINGLE_ARMS = ["volkite", "conversion", "graviton", "lightning", "claw"]
MOIRAX_ARM_WEAPONS = {
    "volkite": "Volkite veuglaire",
    "conversion": "Conversion beam cannon",
    "graviton": "Graviton pulsar",
    "lightning": "Lightning lock",
    "claw": None,  # claw = Rad cleanser (ranged) + Siege claw (melee)
}
MOIRAX_CLAW = {"Rad cleanser", "Siege claw"}

# Sample targets for resolvability checks (GEQ horde, MEQ elite, Knight vehicle)
TARGET_SAMPLES = ["GEQ", "MEQ", "Knight"]

ALL_UNITS = [
    "Canis Rex", "Cerastus Knight Acheron", "Cerastus Knight Atrapos",
    "Cerastus Knight Castigator", "Cerastus Knight Lancer",
    "Knight Castellan", "Knight Crusader", "Knight Defender",
    "Knight Destrier", "Knight Errant", "Knight Gallant", "Knight Paladin",
    "Knight Preceptor", "Knight Valiant", "Knight Warden",
    "Questoris Knight Magaera", "Questoris Knight Styrix",
]


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


def _resolve(engine, build, unit_name, target_name="MEQ"):
    """Resolve one build via the engine's slots path -> (ranged, melee) names."""
    r, m, _n = engine._resolve_slots_build(
        build, unit_name, engine.resolve_target(target_name))
    return [w.name for w in r], [w.name for w in m]


class TestCanisRex:
    """2-model unit (Canis Rex + Sir Hekhtur) — 5 fixed weapons, group names."""

    def test_exact_fixed_inventory(self, chars):
        build = chars["Canis Rex"]["weapon_options"]["builds"][0]
        fixed = frozenset(f["name"] for f in build["fixed"])
        assert fixed == CANIS_FIXED, fixed
        assert build["slots"] == []

    def test_no_las_impulsor_profiles(self, chars):
        build = chars["Canis Rex"]["weapon_options"]["builds"][0]
        fixed = {f["name"] for f in build["fixed"]}
        assert "Las-impulsor - high intensity" not in fixed
        assert "Las-impulsor - low intensity" not in fixed
        assert "Freedom's Hand - strike" not in fixed
        assert "Freedom's Hand - sweep" not in fixed

    def test_resolves(self, engine, chars):
        build = chars["Canis Rex"]["weapon_options"]["builds"][0]
        for t in TARGET_SAMPLES:
            ranged, melee = _resolve(engine, build, "Canis Rex", t)
            assert len(ranged) == 3, f"{t}: {ranged}"
            assert len(melee) == 2, f"{t}: {melee}"
            assert any(LAS in n for n in ranged), f"{t}: no las-impulsor in {ranged}"
            assert any(FREEDOM in n for n in melee), f"{t}: no Freedom's Hand in {melee}"


class TestAtraposDualProfile:
    """Lascutter in BOTH lists; profile category must not leak (CK lock mirror)."""

    def test_fixed_inventory(self, chars):
        build = chars["Cerastus Knight Atrapos"]["weapon_options"]["builds"][0]
        fixed = frozenset(f["name"] for f in build["fixed"])
        assert fixed == {ATRAPOS_LAS, GRAV}, fixed
        assert build["slots"] == []

    def test_ranged_lascutter_has_ranged_profile(self, engine, chars):
        build = chars["Cerastus Knight Atrapos"]["weapon_options"]["builds"][0]
        ranged, melee = _resolve(engine, build, "Cerastus Knight Atrapos")
        las_r = [n for n in ranged if "lascutter" in n.lower()]
        assert las_r, "no ranged lascutter"
        # Category pass-through regression: the fixed entry is declared
        # type=ranged and MUST resolve to the ranged profile. A leak puts
        # the melee profile in the ranged list.
        assert all("(ranged)" in n for n in las_r), f"ranged leaked melee: {las_r}"

    def test_melee_lascutter_has_melee_profile(self, engine, chars):
        build = chars["Cerastus Knight Atrapos"]["weapon_options"]["builds"][0]
        ranged, melee = _resolve(engine, build, "Cerastus Knight Atrapos")
        las_m = [n for n in melee if "lascutter" in n.lower()]
        assert las_m, "no melee lascutter"
        assert all("(melee)" in n for n in las_m), f"melee leaked ranged: {las_m}"

    def test_graviton_is_ranged(self, engine, chars):
        build = chars["Cerastus Knight Atrapos"]["weapon_options"]["builds"][0]
        ranged, _melee = _resolve(engine, build, "Cerastus Knight Atrapos")
        grav = [n for n in ranged if "graviton" in n.lower()]
        assert grav, f"no graviton in ranged: {ranged}"


class TestQuestorisFixedInventories:
    """Exact fixed inventory per Questoris knight — no drift, no profiles."""

    @pytest.mark.parametrize("unit,expected", QUESTORIS_FIXED.items())
    def test_fixed_inventory(self, chars, unit, expected):
        build = chars[unit]["weapon_options"]["builds"][0]
        fixed = frozenset(f["name"] for f in build["fixed"])
        assert fixed == expected, f"{unit}: {fixed} != {expected}"

    @pytest.mark.parametrize("unit", QUESTORIS_FIXED.keys())
    def test_no_choice_profiles_in_fixed(self, chars, unit):
        """standard/supercharge, high/low intensity never in fixed (double-count)."""
        build = chars[unit]["weapon_options"]["builds"][0]
        for f in build["fixed"]:
            for bad in ("- standard", "- supercharge",
                        "- high intensity", "- low intensity"):
                assert bad not in f["name"], f"{unit}: {f['name']}"


class TestQuestorisSlots:
    """Slot structure per unit matches BSData (carapace/meltagun/chain)."""

    @pytest.mark.parametrize("unit,expected_slots", QUESTORIS_SLOTS.items())
    def test_slot_names(self, chars, unit, expected_slots):
        build = chars[unit]["weapon_options"]["builds"][0]
        slot_names = {s["name"] for s in build["slots"]}
        assert slot_names == expected_slots, f"{unit}: {slot_names} != {expected_slots}"

    @pytest.mark.parametrize("unit", [
        "Knight Crusader", "Knight Errant", "Knight Gallant",
        "Knight Paladin", "Knight Warden",
    ])
    def test_carapace_meltagun_choices(self, chars, unit):
        build = chars[unit]["weapon_options"]["builds"][0]
        by_name = {s["name"]: {c["name"] for c in s["choices"]} for s in build["slots"]}
        assert by_name[CARAPACE_SLOT] == CARAPACE_CHOICES, unit
        assert by_name[MELTAGUN_SLOT] == MELTAGUN_CHOICES, unit

    def test_preceptor_slots(self, chars):
        build = chars["Knight Preceptor"]["weapon_options"]["builds"][0]
        by_name = {s["name"]: {c["name"] for c in s["choices"]} for s in build["slots"]}
        assert by_name["Preceptor Multi-laser"] == {
            "Questoris heavy stubber", "Meltagun", "Preceptor multi-laser"}
        assert by_name[CARAPACE_SLOT] == CARAPACE_CHOICES
        assert by_name[CHAIN_SLOT] == CHAIN_CHOICES

    def test_crusader_thermal_slot(self, chars):
        build = chars["Knight Crusader"]["weapon_options"]["builds"][0]
        by_name = {s["name"]: {c["name"] for c in s["choices"]} for s in build["slots"]}
        # BSData models 'Rapid-fire battlecannon and Questoris heavy stubber'
        # as a bundle; the component 'Rapid-fire battle cannon' is used here
        # because bundle names resolve to primary profile only (Despoiler
        # precedent — the bundle entry would silently lose the battlecannon).
        assert by_name["Thermal Cannon"] == {"Thermal cannon", "Rapid-fire battle cannon"}

    def test_destrier_slots(self, chars):
        build = chars["Knight Destrier"]["weapon_options"]["builds"][0]
        by_name = {s["name"]: {c["name"] for c in s["choices"]} for s in build["slots"]}
        assert by_name == DESTRIER_SLOTS, by_name

    def test_castellan_valiant_no_carapace_slot(self, chars):
        """Shieldbreaker/siegebreaker bundle names don't resolve — gap documented."""
        for unit in ("Knight Castellan", "Knight Valiant"):
            build = chars[unit]["weapon_options"]["builds"][0]
            assert build["slots"] == [], f"{unit}: unexpected slots"


class TestAcastus:
    """Asterius 2x each pair weapon; Porphyrion 2x magna + 3 slots, shoulder dup legal."""

    def test_asterius_fixed_counts(self, chars):
        build = wopt_asterius()
        from collections import Counter
        counts = Counter(f["name"] for f in build["fixed"])
        assert counts["Twin conversion beam cannon"] == 2
        assert counts["Asterius volkite culverin"] == 2
        assert counts["Karacnos mortar battery"] == 1
        assert counts[TITANIC] == 1
        assert build["slots"] == []

    def test_porphyrion_fixed_and_slots(self, chars):
        build = wopt_porphyrion()
        from collections import Counter
        counts = Counter(f["name"] for f in build["fixed"])
        assert counts["Twin magna lascannon"] == 2
        assert counts[TITANIC] == 1
        by_name = {s["name"]: {c["name"] for c in s["choices"]} for s in build["slots"]}
        assert by_name == PORPHYRION_SLOTS, by_name

    def test_porphyrion_resolves_per_target(self, engine, chars):
        build = wopt_porphyrion()
        for t in TARGET_SAMPLES:
            ranged, melee = _resolve(engine, build, "Acastus Knight Porphyrion", t)
            assert len(ranged) == 5, f"{t}: {ranged}"  # 2 magna + 3 slots
            assert len(melee) == 1 and melee[0] == TITANIC, f"{t}: {melee}"


class TestArmigers:
    """Helverin/Warglaive fixed + Heavy Stubber slot; Moirax 15-build inventory."""

    def test_helverin_fixed(self, chars):
        build = wopt_armiger("Armiger Helverin")
        fixed = frozenset(f["name"] for f in build["fixed"])
        assert fixed == HELVERIN_FIXED, fixed
        slot = {s["name"]: {c["name"] for c in s["choices"]} for s in build["slots"]}
        assert slot == {STUBBER_SLOT: STUBBER_CHOICES}, slot

    def test_warglaive_fixed(self, chars):
        build = wopt_armiger("Armiger Warglaive")
        fixed = frozenset(f["name"] for f in build["fixed"])
        assert fixed == WARGLIAVE_FIXED, fixed
        slot = {s["name"]: {c["name"] for c in s["choices"]} for s in build["slots"]}
        assert slot == {STUBBER_SLOT: STUBBER_CHOICES}, slot

    def test_moirax_15_builds(self, chars):
        builds = wopt_moirax()
        assert len(builds) == 15, f"{len(builds)} != 15"

    def test_moirax_5_double_arms(self, chars):
        builds = wopt_moirax()
        # Name pattern: moirax_<arm1>_<arm2>. Doubles repeat the arm
        # (moirax_volkite_volkite); pairs differ (moirax_volkite_conversion).
        def _arms(name):
            _, a1, a2 = name.split("_")
            return a1, a2

        doubles = [b["name"] for b in builds
                   if b["name"].startswith("moirax_")
                   and _arms(b["name"])[0] == _arms(b["name"])[1]]
        assert len(doubles) == 5, f"doubles: {doubles}"

    def test_moirax_10_pair_arms(self, chars):
        builds = wopt_moirax()
        def _arms(name):
            _, a1, a2 = name.split("_")
            return a1, a2

        pairs = [b["name"] for b in builds
                 if b["name"].startswith("moirax_")
                 and _arms(b["name"])[0] != _arms(b["name"])[1]]
        assert len(pairs) == 10, f"pairs: {pairs}"

    def test_moirax_claw_builds_split(self, chars):
        """Claw = Rad cleanser (ranged) + Siege claw (melee), never the bundle."""
        builds = wopt_moirax()
        for b in builds:
            if "claw" in b["name"]:
                names = {f["name"] for f in b["fixed"]}
                assert MOIRAX_CLAW.issubset(names), f"{b['name']}: {names}"
                assert "Siege claw and rad cleanser" not in names, b["name"]

    def test_moirax_every_build_has_feet(self, chars):
        builds = wopt_moirax()
        for b in builds:
            feet = [f for f in b["fixed"] if f["name"] == MOIRAX_FEET]
            assert feet, f"{b['name']}: no Armoured feet"

    def test_moirax_resolves_per_target(self, engine, chars):
        for b in wopt_moirax():
            for t in TARGET_SAMPLES:
                ranged, melee = _resolve(engine, b, "Armiger Moirax", t)
                assert ranged or melee, f"{b['name']}/{t}: empty"


class TestPerTargetResolvability:
    """Every character unit resolves a loadout on GEQ/MEQ/Knight targets."""

    @pytest.mark.parametrize("unit", ALL_UNITS)
    def test_all_characters_resolve(self, engine, chars, unit):
        for b in chars[unit]["weapon_options"]["builds"]:
            for t in TARGET_SAMPLES:
                ranged, melee = _resolve(engine, b, unit, t)
                assert ranged or melee, f"{unit}/{b['name']}/{t}: empty"


# ── small helpers to reach into weapon_options.json ──────────────────────

def _wo_unit(name):
    cfg = json.load(open(WEAPON_OPTIONS))
    return cfg[name]["builds"][0]


def wopt_asterius():
    return _wo_unit("Acastus Knight Asterius")


def wopt_porphyrion():
    return _wo_unit("Acastus Knight Porphyrion")


def wopt_armiger(name):
    return _wo_unit(name)


def wopt_moirax():
    cfg = json.load(open(WEAPON_OPTIONS))
    return cfg["Armiger Moirax"]["builds"]
