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