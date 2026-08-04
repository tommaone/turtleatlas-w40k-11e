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

# Canonical target profiles come from the shared engine config (single source
# of truth — tests must not duplicate their own W/model_count values).

_BASE_CFG_PATH = Path(__file__).resolve().parent.parent / "data" / "config" / "_base.json"


def _target_from_cfg(key: str):
    from dpp import TargetProfile
    with open(_BASE_CFG_PATH) as f:
        cfg = json.load(f)
    t = cfg["target_profiles"][key]
    return TargetProfile(
        toughness=t["toughness"],
        save=t.get("save", 7),
        invuln=t.get("invuln"),
        model_count=t.get("model_count", 1),
        wounds_per_model=t.get("wounds_per_model", 1),
    )


@pytest.fixture
def MEQ():
    return _target_from_cfg("MEQ")


@pytest.fixture
def TEQ():
    return _target_from_cfg("TEQ")


@pytest.fixture
def GEQ():
    return _target_from_cfg("GEQ")


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
