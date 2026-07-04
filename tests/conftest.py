"""Shared fixtures for all tests."""

import json
import sys
from pathlib import Path

import pytest

# Add engine dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

# ---------------------------------------------------------------------------
# Fixtures: DPP engine
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def weapon_catalog():
    """WeaponCatalog loaded from GK merged JSON."""
    from weapon_loader import WeaponCatalog

    merged_path = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "merged"
        / "grey-knights.json"
    )
    return WeaponCatalog(str(merged_path))


@pytest.fixture(scope="session")
def gk_merged():
    """Raw GK merged JSON data."""
    p = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "merged"
        / "grey-knights.json"
    )
    with open(p) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Fixtures: Target profiles
# ---------------------------------------------------------------------------


@pytest.fixture
def MEQ():
    from dpp import TargetProfile
    return TargetProfile(toughness=4, save=3, invuln=None)


@pytest.fixture
def TEQ():
    from dpp import TargetProfile
    return TargetProfile(toughness=5, save=2, invuln=4)


@pytest.fixture
def GEQ():
    from dpp import TargetProfile
    return TargetProfile(toughness=3, save=5, invuln=None)


# ---------------------------------------------------------------------------
# Fixtures: Sample weapons
# ---------------------------------------------------------------------------


@pytest.fixture
def storm_bolter(weapon_catalog):
    """Storm Bolter profile as loaded from BSData."""
    try:
        return weapon_catalog.load("Storm bolter", unit_name="Strike Squad")
    except KeyError:
        return weapon_catalog.load("storm bolter", unit_name="Strike Squad")


@pytest.fixture
def psycannon(weapon_catalog):
    """Psycannon profile as loaded from BSData."""
    return weapon_catalog.load("Psycannon")
