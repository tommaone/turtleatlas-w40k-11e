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
    """Every fixed weapon the merged data lists must survive into the build(s)."""
    assert unit in gk_constraints, f"unit missing from constraints: {unit}"
    builds = gk_constraints[unit]["builds"]
    assert builds, f"{unit} has no builds"

    merged_names = {n.lower() for n in gk_merged_weapons[unit]}
    captured = _unit_fixed_names(builds)

    # The merged list IS the ground truth for FIXED weapons.
    assert captured == merged_names, (
        f"{unit}: merged lists {sorted(merged_names)} but parser captured "
        f"{sorted(captured)} (missing {sorted(merged_names - captured)})"
    )
    assert len(captured) == expected_count, (
        f"{unit}: expected {expected_count} fixed weapons, got {len(captured)}"
    )


def test_thunderhawk_all_six_weapons(gk_constraints):
    """Thunderhawk: all six merged weapons present by name."""
    expected = {
        "lascannon", "armoured hull", "twin heavy bolter",
        "thunderhawk heavy cannon", "turbo-laser destructor",
        "hellstrike missile battery",
    }
    captured = _unit_fixed_names(gk_constraints["Grey Knights Thunderhawk Gunship"]["builds"])
    assert captured == expected


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