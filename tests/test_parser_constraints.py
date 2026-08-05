"""Tests for BSData wargear constraint extraction (bsdata_parser_11e).

Verifies that extract_wargear_constraints() does not LOSE fixed weapons when
augmenting from the merged data (data/merged/<faction>.json). The merged data
is the ground truth for FIXED weapons; BSData wargear groups only carry a
subset (the rest live on model profiles / shared-entry entryLinks).

Targets the regression where:
  - Thunderhawk Gunship  -> 2 of 6 weapons were captured
  - Land Raider          -> 1 of 6 weapons were captured
  - Stormraven Gunship   -> 3 of 9 weapons were captured
  - Chaos Daemons        -> 0 constraint units (faction-name resolution failed)

Run: python3 -m pytest tests/test_parser_constraints.py -v
"""

import json
import sys
from pathlib import Path

import pytest

# Ensure the repo root is importable so `adapter.*` resolves.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from adapter.bsdata_parser_11e import BSDataParser11e


MERGED_DIR = Path(__file__).resolve().parent.parent / "data" / "merged"


def _merged_weapons(faction_file: str) -> dict[str, list[str]]:
    """Return unit_name -> list of weapon names from a merged faction JSON."""
    with open(MERGED_DIR / faction_file) as f:
        data = json.load(f)
    out: dict[str, list[str]] = {}
    for u in data.get("units", []):
        weapons = (u.get("profile") or {}).get("weapons", [])
        if weapons:
            out[u["name"]] = [w.get("name", "") for w in weapons]
    return out


def _unit_fixed_names(builds: list[dict]) -> set[str]:
    """All fixed weapon names across a unit's builds (case-insensitive set)."""
    names: set[str] = set()
    for b in builds:
        for n in b.get("fixed_ranged", []) or []:
            names.add(n.lower())
        for n in b.get("fixed_melee", []) or []:
            names.add(n.lower())
    return names


def _unit_all_weapons(builds: list[dict]) -> set[str]:
    """All weapon names captured by a unit's builds — fixed OR choice options.

    Choice-aware extraction (vehicle fix) models optional weapon slots as
    ranged_choices / slots instead of flattening every option into fixed. A
    merged weapon is only "captured" if it appears somewhere in the builds.
    """
    names = _unit_fixed_names(builds)
    for b in builds:
        for group in b.get("ranged_choices", []) or []:
            names |= {n.lower() for n in group}
        for group in b.get("melee_choices", []) or []:
            names |= {n.lower() for n in group}
        for slot in b.get("slots", []) or []:
            for c in slot.get("choices", []) or []:
                names.add(c.get("name", "").lower())
    return names


@pytest.fixture(scope="module")
def parser():
    return BSDataParser11e()


@pytest.fixture(scope="module")
def gk_constraints(parser):
    """extract_wargear_constraints('Grey Knights') (short display name)."""
    return parser.extract_wargear_constraints("Grey Knights")


@pytest.fixture(scope="module")
def gk_merged_weapons():
    return _merged_weapons("grey-knights.json")


# ---------------------------------------------------------------------------
# Grey Knights — fixed weapon completeness (the core regression)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("unit, expected_count", [
    ("Grey Knights Thunderhawk Gunship", 6),
    ("Land Raider", 6),
    ("Stormraven Gunship", 9),
])
def test_vehicle_fixed_weapons_complete(gk_constraints, gk_merged_weapons,
                                        unit, expected_count):
    """Every weapon the merged data lists must survive into the build(s).

    Choice-aware extraction surfaces genuine optional slots (e.g. Thunderhawk
    heavy cannon → Turbo-laser destructor) as choice groups rather than fixed.
    A merged weapon is captured whether it is fixed or a choice option.
    """
    assert unit in gk_constraints, f"unit missing from constraints: {unit}"
    builds = gk_constraints[unit]["builds"]
    assert builds, f"{unit} has no builds"

    merged_names = {n.lower() for n in gk_merged_weapons[unit]}
    captured = _unit_all_weapons(builds)

    # The merged list IS the ground truth for weapons — none may be lost.
    assert merged_names <= captured, (
        f"{unit}: merged lists {sorted(merged_names)} but parser captured "
        f"{sorted(captured)} (missing {sorted(merged_names - captured)})"
    )
    assert len(merged_names) == expected_count, (
        f"{unit}: expected {expected_count} merged weapons, got {len(merged_names)}"
    )


def test_thunderhawk_all_six_weapons(gk_constraints):
    """Thunderhawk: all six merged weapons present (fixed or choice option).

    The datasheet has real option slots the old all-fixed flattening destroyed:
      - Thunderhawk heavy cannon  OR  Turbo-laser destructor
      - Thunderhawk cluster bombs OR  Hellstrike missile battery
    """
    expected = {
        "lascannon", "armoured hull", "twin heavy bolter",
        "thunderhawk heavy cannon", "turbo-laser destructor",
        "hellstrike missile battery",
    }
    captured = _unit_all_weapons(
        gk_constraints["Grey Knights Thunderhawk Gunship"]["builds"])
    assert expected <= captured

    builds = gk_constraints["Grey Knights Thunderhawk Gunship"]["builds"]
    fixed = _unit_fixed_names(builds)
    assert fixed == {"lascannon", "armoured hull", "twin heavy bolter"}, (
        "Thunderhawk fixed weapons: expected the 3 built-ins, "
        f"got {sorted(fixed)} (options must be choices, not fixed)"
    )


def test_landraider_all_six_weapons(gk_constraints):
    expected = {
        "godhammer lascannon", "storm bolter", "hunter-killer missile",
        "multi-melta", "twin heavy bolter", "armoured tracks",
    }
    captured = _unit_fixed_names(gk_constraints["Land Raider"]["builds"])
    assert captured == expected


def test_stormraven_all_nine_weapons(gk_constraints):
    expected = {
        "hurricane bolter", "armoured hull", "stormstrike missile launcher",
        "twin heavy plasma cannon", "twin assault cannon", "twin lascannon",
        "twin multi-melta", "twin heavy bolter", "typhoon missile launcher",
    }
    captured = _unit_fixed_names(gk_constraints["Stormraven Gunship"]["builds"])
    assert captured == expected


# ---------------------------------------------------------------------------
# Faction-name resolution (short / slug / full BSData name all accepted)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", [
    "Grey Knights",
    "grey-knights",
    "Imperium - Grey Knights",
])
def test_faction_name_resolution(parser, name):
    """Short display name, MFM slug, and full BSData name all resolve the same."""
    r = parser.extract_wargear_constraints(name)
    assert r, f"faction name {name!r} resolved to no constraints"
    assert "Grey Knights Thunderhawk Gunship" in r


# ---------------------------------------------------------------------------
# Chaos Daemons — was 0 units entirely (faction-name + augmentation)
# ---------------------------------------------------------------------------


def test_chaos_daemons_has_units(parser):
    """Chaos Daemons must return at least one constraint unit."""
    r = parser.extract_wargear_constraints("Chaos Daemons")
    assert len(r) >= 1, (
        "Chaos Daemons returned 0 constraint units. The BSData catalogue "
        "'Chaos - Chaos Daemons' has wargear groups in its linked libraries "
        "(Chaos - Daemons Library, Chaos - Chaos Knights Library); if this still "
        "fails, the catalogue resolution / merged augmentation is broken."
    )


def test_chaos_daemons_slug_alias(parser):
    """The MFM slug 'chaos-daemons' must also resolve."""
    r = parser.extract_wargear_constraints("chaos-daemons")
    assert len(r) >= 1


# ---------------------------------------------------------------------------
# Aeldari vehicles — nested-model Wargear + choice-group preservation (Vyper bug)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def aeldari_constraints(parser):
    return parser.extract_wargear_constraints("Aeldari")


def test_vypers_nested_model_wargear_descent(aeldari_constraints):
    """Vypers carry Wargear on the NESTED model entry, not the top-level unit.

    The old top-level-only search fell through to the merged fallback, which
    flattened every gun into fixed_ranged (the 14-entry 'loads all weapons'
    artifact). The corrected extraction must surface the two choice slots.
    """
    assert "Vypers" in aeldari_constraints
    builds = aeldari_constraints["Vypers"]["builds"]
    assert builds, "Vypers has no builds"
    b = builds[0]
    # Only the hull is fixed; all guns are choices.
    assert b.get("fixed_melee") == ["Wraithbone hull"], b.get("fixed_melee")
    assert not b.get("fixed_ranged"), b.get("fixed_ranged")
    slots = b.get("slots", [])
    assert [s["name"] for s in slots] == [
        "Bright Lance Replacement", "Shuriken Cannon Replacement",
    ]
    bl_choices = [c["name"] for c in slots[0]["choices"]]
    assert bl_choices == ["Bright Lance", "Scatter Laser", "Starcannon"]
    sc_choices = [c["name"] for c in slots[1]["choices"]]
    assert sc_choices == ["Shuriken Cannon", "Missile Launcher"]


def test_vypers_no_all_fixed_collapse(aeldari_constraints):
    """The merge-augment must NOT collapse Vypers to an all-fixed default.

    Every merged weapon is captured as a choice option, so the augment's subset
    check passes and the choice structure is preserved.
    """
    b = aeldari_constraints["Vypers"]["builds"][0]
    merged = {"bright lance", "scatter laser", "starcannon",
              "shuriken cannon", "missile launcher", "wraithbone hull"}
    captured = _unit_all_weapons(aeldari_constraints["Vypers"]["builds"])
    assert merged <= captured
    assert len(b.get("fixed_ranged") or []) < 3, (
        "Vypers guns must be choices, not fixed"
    )


def test_no_singular_vyper_duplicate(aeldari_constraints):
    """Merged lists both 'Vypers' (unit) and 'Vyper' (model-level duplicate).

    The singular duplicate must NOT be added as a merged-only all-fixed build.
    """
    vyper_keys = [k for k in aeldari_constraints if k.lower() == "vyper"]
    assert vyper_keys == [], f"singular 'Vyper' duplicate leaked: {vyper_keys}"
    assert "Vypers" in aeldari_constraints


def test_falcon_inline_choice_group(aeldari_constraints):
    """Falcon's hull-weapon choice group uses inline selectionEntries."""
    b = aeldari_constraints["Falcon"]["builds"][0]
    assert b.get("fixed_ranged") == ["Pulse Laser"]
    slots = b.get("slots", [])
    assert [c["name"] for c in slots[0]["choices"]] == [
        "Twin Shuriken Catapult", "Shuriken Cannon",
    ]


def test_crimson_hunter_count_choices(aeldari_constraints):
    """Crimson Hunter's '2 Starcannons'/'2 Bright Lances' resolve with counts.

    The wrapper upgrades nest the real weapon ('Starcannon') one level down;
    the count prefix must survive so the engine applies the ×2 multiplicity.
    """
    b = aeldari_constraints["Crimson Hunter"]["builds"][0]
    slots = b.get("slots", [])
    assert [s["name"] for s in slots] == ["Weapon Option"]
    choices = slots[0]["choices"]
    assert [(c["name"], c.get("count", 1)) for c in choices] == [
        ("Starcannon", 2), ("Bright Lance", 2),
    ]


def test_wave_serpent_two_slots(aeldari_constraints):
    """Wave Serpent has both hull and turret weapon slots (no fixed guns)."""
    b = aeldari_constraints["Wave Serpent"]["builds"][0]
    assert not b.get("fixed_ranged"), b.get("fixed_ranged")
    assert [s["name"] for s in b.get("slots", [])] == [
        "Hull weapon", "Turret Weapon",
    ]

# ---------------------------------------------------------------------------
# Aeldari squad model-composition — per-model builds with per-model slots
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def aeldari_composition(parser):
    return parser.extract_squad_composition("Aeldari")


def test_composition_dark_reapers_structure(aeldari_composition):
    """Dark Reapers: main model + exarch with a Weapon slot (4 options)."""
    b = aeldari_composition["Dark Reapers"]["builds"][0]
    models = b["models"]
    assert [(m["name"], m.get("min"), m.get("max")) for m in models] == [
        ("Dark Reaper", 4, 9),
        ("Dark Reaper Exarch", 1, 1),
    ]
    dr = models[0]
    assert dr["ranged"] == "Reaper Launcher"
    assert dr["melee"] == "Close combat weapon"
    ex = models[1]
    assert ex["melee"] == "Close combat weapon"
    slot = ex["slots"][0]
    assert slot["name"] == "Weapon"
    assert [c["ranged"] for c in slot["choices"]] == [
        "Shuriken Cannon", "Tempest Launcher", "Missile Launcher", "Reaper Launcher",
    ]
    assert slot["choices"][-1].get("default") is True


def test_composition_banshee_bundle_payload(aeldari_composition):
    """Howling Banshees exarch: bundle choices resolve to {ranged, melee}."""
    ex = aeldari_composition["Howling Banshees"]["builds"][0]["models"][1]
    slot = ex["slots"][0]
    assert slot["choices"][0]["name"] == "Banshee Blade and Shuriken Pistol"
    assert slot["choices"][0]["ranged"] == "Shuriken Pistol"
    assert slot["choices"][0]["melee"] == "Banshee Blade"
    mirrors = [c for c in slot["choices"] if c["name"] == "Mirrorswords"][0]
    assert "ranged" not in mirrors
    assert mirrors["melee"] == "Mirrorswords"


def test_composition_dire_avenger_two_catapults(aeldari_composition):
    """Two Avenger Shuriken Catapults: min=2 on the linked catapult -> count 2."""
    ex = aeldari_composition["Dire Avengers"]["builds"][0]["models"][1]
    two = [c for c in ex["slots"][0]["choices"]
           if c["name"] == "Two Avenger Shuriken Catapults"][0]
    assert two["ranged"] == "Avenger shuriken catapult"
    assert two.get("ranged_count") == 2
    # Default points at the shared catapult SE (e007...) — lands on the
    # single-catapult choice.
    single = [c for c in ex["slots"][0]["choices"]
              if c["name"] == "Avenger shuriken catapult"][0]
    assert single.get("default") is True


def test_composition_rangers_direct_models(aeldari_composition):
    """Rangers put the model SE directly on the unit entry (no sibling SEGs)."""
    b = aeldari_composition["Rangers"]["builds"][0]
    assert [(m["name"], m.get("min"), m.get("max")) for m in b["models"]] == [
        ("Ranger", 5, 10),
    ]
    assert b["models"][0]["ranged"] == ["Long rifle", "Shuriken Pistol"]
    assert b["models"][0]["melee"] == "Close Combat Weapon"


def test_composition_chainsabres_dual_profile(aeldari_composition):
    """Chainsabres carries Melee+Ranged profiles in BSData — a dual-profile
    weapon lands in BOTH lists (melee A5 + pistol A1). The loader resolves
    the correct profile per list context."""
    ex = aeldari_composition["Striking Scorpions"]["builds"][0]["models"][1]
    chainsabres = [c for c in ex["slots"][0]["choices"]
                   if c["name"] == "Chainsabres"][0]
    assert chainsabres["ranged"] == "Chainsabres"
    assert chainsabres["melee"] == "Chainsabres"


def test_composition_harlequin_blade_infolink(aeldari_composition):
    """Troupe: Harlequin's Blade lives as an infoLink profile ref on the model
    SE (11e sharedProfiles pattern) — it must resolve to a melee fixed weapon,
    not get dropped as an ability wrapper."""
    blade_player = [m for m in aeldari_composition["Troupe"]["builds"][0]["models"]
                    if m["name"] == "Player with Harlequin's Blade"][0]
    assert blade_player["ranged"] == "Shuriken Pistol"
    assert blade_player["melee"] == "Harlequin's Blade"


def test_composition_troupe_parallel_variants(aeldari_composition):
    """Troupe pool: 4 player variants share the squad budget (all capped/uncapped,
    none mandatory) + a Lead Player leader (min=1 max=1)."""
    models = aeldari_composition["Troupe"]["builds"][0]["models"]
    players = [m for m in models if m.get("min") != 1]
    assert {m["name"] for m in players} == {
        "Player with Harlequin's Blade",
        "Player with Harlequin's Special Weapon",
        "Player with Fusion Pistol",
        "Player with Neuro Disruptor",
    }
    blade = [m for m in players if m["name"] == "Player with Harlequin's Blade"][0]
    assert blade.get("max") == 11
    lead = [m for m in models if m.get("min") == 1][0]
    assert lead["name"] == "Lead Player"
    assert lead.get("max") == 1


def test_composition_windriders_three_variants(aeldari_composition):
    """Windriders: 3 parallel weapon variants, each capped at 6, no leader."""
    models = aeldari_composition["Windriders"]["builds"][0]["models"]
    assert [(m["name"], m.get("min"), m.get("max")) for m in models] == [
        ("Windrider with Twin Shuriken Catapult", None, 6),
        ("Windrider with Scatter Laser", None, 6),
        ("Windrider with Shuriken Cannon", None, 6),
    ]


def test_composition_voidscarred_nested_pool(aeldari_composition):
    """Corsair Voidscarred: base variants live in a NESTED 'Voidscarred' SEG
    (min=4) inside '4 -9 Voidscarred'. The recursion must collect them and tag
    them with pool_min=4; the capped specials stay untagged."""
    models = aeldari_composition["Corsair Voidscarred"]["builds"][0]["models"]
    base = [m for m in models if m.get("pool_min") == 4]
    assert {m["name"] for m in base} == {
        "Voidscarred w/ pistol and sword",
        "Voidscarred w/ rifle",
        "Voidscarred with Faolchú",
        "Voidscarred with fusion pistol",
        "Voidscarred with heavy weapon",
        "Voidscarred with ranger long rifle",
        "Voidscarred with special weapon",
    }
    specials = [m for m in models if not m.get("pool_min") and m.get("min") != 1]
    assert {m["name"] for m in specials} == {
        "Shade Runner", "Soul Weaver", "Way Seeker",
    }
    assert all(m["max"] == 1 for m in specials)
    # heavy/special weapon variants carry a nested Weapon slot
    heavy = [m for m in base if m["name"] == "Voidscarred with heavy weapon"][0]
    assert [c["name"] for c in heavy["slots"][0]["choices"]] == [
        "Shuriken cannon", "Wraithcannon",
    ]
    felarch = [m for m in models if m.get("min") == 1][0]
    assert felarch["name"] == "Voidscarred Felarch"


def test_composition_warlock_multiple_fixed_ranged(aeldari_composition):
    """Warlock with Witchblade: fixed ranged is BOTH Shuriken Pistol AND
    Destructor (own entryLinks) — a list, not a collapsed single."""
    warlock = [m for m in aeldari_composition["Warlock Conclave"]["builds"][0]["models"]
               if m["name"] == "Warlock with Witchblade"][0]
    assert warlock["ranged"] == ["Shuriken Pistol", "Destructor"]
    assert warlock["melee"] == "Witchblade"


def test_composition_warlock_singing_spear_always_melee(aeldari_composition):
    """Warlock with Singing Spear: the spear is dual-profile (throwable ranged
    + melee half) — the model ALWAYS has a melee profile. The melee half must
    not be dropped by first-profile resolution."""
    warlock = [m for m in aeldari_composition["Warlock Conclave"]["builds"][0]["models"]
               if m["name"] == "Warlock with Singing Spear"][0]
    assert warlock["ranged"] == ["Singing Spear", "Shuriken Pistol", "Destructor"]
    assert warlock["melee"] == "Singing Spear"


def test_composition_warlock_skyrunner_three_ranged(aeldari_composition):
    """Warlock Skyrunner with Singing Spear: 3 fixed ranged weapons
    (Shuriken Pistol + Twin Shuriken Catapult + Destructor) + Singing Spear
    (dual-profile: ranged AND melee)."""
    skyrunner = [m for m in aeldari_composition["Warlock Skyrunners"]["builds"][0]["models"]
                 if m["name"] == "Warlock Skyrunner with Singing Spear"][0]
    assert set(skyrunner["ranged"]) == {
        "Shuriken Pistol", "Twin Shuriken Catapult", "Destructor", "Singing Spear",
    }
    assert skyrunner["melee"] == "Singing Spear"


def test_composition_reaver_splinter_pistol_preserved(aeldari_composition):
    """Ynnari Reaver: Splinter Rifle + Splinter Pistol fixed ranged (the pistol
    was dropped by the old single-weapon collapse)."""
    reaver = [m for m in aeldari_composition["Ynnari Reavers"]["builds"][0]["models"]
              if m["name"] == "Reaver"][0]
    assert reaver["ranged"] == ["Splinter Rifle", "Splinter Pistol"]
    assert reaver["melee"] == "Bladevanes"


def test_squad_no_model_type_as_weapon(aeldari_constraints):
    """Regression: the 61 squad false flags.

    Model-type containers (Dark Reaper, Howling Banshee, Ranger) must NEVER
    appear as fixed weapons in squad constraints. Squads now carry composition
    builds (models[] with per-model slots); the unit-level fixed lists are
    empty and the merge-augment must not clobber the composition back into an
    all-fixed default build.
    """
    for unit in ("Dark Reapers", "Howling Banshees", "Rangers"):
        builds = aeldari_constraints[unit]["builds"]
        assert builds, f"{unit} has no builds"
        b = builds[0]
        assert "models" in b, f"{unit} composition was clobbered by augment"
        assert not b.get("fixed_ranged"), b.get("fixed_ranged")
        assert not b.get("fixed_melee"), b.get("fixed_melee")
