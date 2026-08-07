"""
Test every datasheet pricing matches MFM 1:1 — all tiers.

Loads MFM YAML directly (source of truth) and validates every
config unit has correct pts (1st unit) and pts_3rd (3rd+ unit).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
MFM_DIR = REPO_ROOT / "mfm" / "data"
CONFIG_DIR = REPO_ROOT / "data" / "config"

# Factions we support
TEST_FACTIONS = ["grey-knights", "chaos-knights", "chaos-daemons", "emperors-children"]

# Unit name patterns that are exempt from MFM pricing checks
# (Legends, Crucible, Forge World, Titanicus — no current MFM entry)
MFM_EXEMPT_PATTERNS = ["[Crucible]", "Titan", "Acatus", "Soul Grinder"]


def _load_mfm(slug: str) -> dict:
    """Load MFM YAML for a faction."""
    path = MFM_DIR / f"{slug}.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


def _load_config_units(slug: str) -> dict[str, dict]:
    """Load all config units for a faction into a flat dict."""
    units = {}
    config_dir = CONFIG_DIR / slug
    for fn in ["characters.json", "squads.json", "vehicles.json", "weapon_options.json"]:
        fp = config_dir / fn
        if not fp.exists():
            continue
        with open(fp) as f:
            data = json.load(f)
        for name, entry in data.items():
            if isinstance(entry, dict) and "pts" in entry and entry["pts"] is not None:
                units[_norm(name)] = (name, entry, fn)
    return units


def _is_exempt(name: str) -> bool:
    """Check if a unit name is exempt from MFM pricing checks."""
    return any(p in name for p in MFM_EXEMPT_PATTERNS)


def _norm(name: str) -> str:
    """Normalize name: lowercase, strip, normalize apostrophes."""
    return name.lower().strip().replace("\u2019", "'")


# ── Per-faction test collection ──────────────────────────────────────


@pytest.mark.parametrize("slug", TEST_FACTIONS)
def test_all_config_units_have_mfm_pricing(slug: str):
    """Every unit in config must exist in MFM with pricing data."""
    mfm = _load_mfm(slug)
    config_units = _load_config_units(slug)

    mfm_names = {_norm(u["name"]): u for u in mfm["units"] if u.get("pricing")}

    missing = []
    for norm_name, (display, entry, fn) in sorted(config_units.items()):
        if _is_exempt(display):
            continue
        if norm_name not in mfm_names:
            missing.append(f"  {display:40s} (in {fn})")

    assert not missing, (
        f"{slug}: {len(missing)} config units not found in MFM:\n"
        + "\n".join(missing)
    )


@pytest.mark.parametrize("slug", TEST_FACTIONS)
def test_first_unit_pts_match_mfm(slug: str):
    """Config pts (1st unit) must match MFM first-tier pricing."""
    mfm = _load_mfm(slug)
    config_units = _load_config_units(slug)

    mfm_pts = {}
    for u in mfm["units"]:
        if u.get("pricing"):
            first = [(c["models"], c["points"]) for c in u["pricing"][0]["costs"]]
            mfm_pts[_norm(u["name"])] = first

    errors = []
    for norm_name, (display, entry, fn) in sorted(config_units.items()):
        if _is_exempt(display):
            continue
        # Skip weapon_slot vehicles — pts is chassis base, not full price
        if "weapon_slots" in entry:
            continue
        config_pts = entry["pts"]
        n = entry.get("n")
        mfm_costs = mfm_pts.get(norm_name)
        if mfm_costs is None:
            errors.append(f"  {display:40s} no MFM price (in {fn})")
            continue
        # The engine resolves by model count (config n), not the first cost
        # in the tier — a unit evaluated at n=5 uses the 5-model price.
        mfm_val = None
        if n is not None:
            for models, points in mfm_costs:
                if models == n:
                    mfm_val = points
                    break
        if mfm_val is None:
            mfm_val = mfm_costs[0][1]
        if config_pts != mfm_val:
            errors.append(
                f"  {display:40s} config={config_pts:4d}  mfm={mfm_val:4d} (n={n})  ({fn})"
            )

    assert not errors, (
        f"{slug}: {len(errors)} units have wrong 1st-unit pts:\n"
        + "\n".join(errors)
    )


@pytest.mark.parametrize("slug", TEST_FACTIONS)
def test_third_unit_pts_match_mfm(slug: str):
    """Config pts_3rd must match MFM 3rd+ tier pricing when it exists."""
    mfm = _load_mfm(slug)
    config_units = _load_config_units(slug)

    # Build MFM third tier lookup, keyed by unit name. The engine resolves by
    # model count (config n), not the first cost in the tier — a unit evaluated
    # at n=5 uses the 5-model 3rd+ price, not the min-size one. The lookup is
    # a dict of (name -> list of (models, points)) so each config unit picks
    # the tier price matching its own n.
    mfm_third: dict[str, list[tuple[int, int]]] = {}
    for u in mfm["units"]:
        if not u.get("pricing"):
            continue
        third_costs = None
        for p in u["pricing"]:
            if p["range"] == "[3,)":
                third_costs = [(c["models"], c["points"]) for c in p["costs"]]
                break
        if third_costs is not None:
            mfm_third[_norm(u["name"])] = third_costs

    errors = []
    for norm_name, (display, entry, fn) in sorted(config_units.items()):
        if _is_exempt(display):
            continue
        config_pts_3rd = entry.get("pts_3rd")
        n = entry.get("n")
        mfm_costs = mfm_third.get(norm_name)

        # If MFM has 3rd+ tier, config must match the price at its own n
        if mfm_costs is not None:
            mfm_val = None
            if n is not None:
                for models, points in mfm_costs:
                    if models == n:
                        mfm_val = points
                        break
            # Fall back to the min-size tier price when n is unknown
            if mfm_val is None:
                mfm_val = mfm_costs[0][1]
            if config_pts_3rd is None:
                errors.append(
                    f"  {display:40s} config missing pts_3rd, should be {mfm_val} (n={n})"
                )
            elif config_pts_3rd != mfm_val:
                errors.append(
                    f"  {display:40s} config={config_pts_3rd:4d}  mfm={mfm_val:4d} (n={n})  ({fn})"
                )
        # If MFM has no 3rd+ tier, config must NOT have pts_3rd
        elif config_pts_3rd is not None:
            errors.append(
                f"  {display:40s} config has pts_3rd={config_pts_3rd} but MFM has no 3rd+ tier"
            )

    assert not errors, (
        f"{slug}: {len(errors)} units have wrong 3rd-tier pricing:\n"
        + "\n".join(errors)
    )


@pytest.mark.parametrize("slug", TEST_FACTIONS)
def test_pts_3rd_is_higher_than_pts(slug: str):
    """Progressive pricing must be more expensive, never cheaper."""
    config_units = _load_config_units(slug)
    errors = []
    for norm_name, (display, entry, fn) in sorted(config_units.items()):
        pts = entry["pts"]
        pts_3rd = entry.get("pts_3rd")
        if pts_3rd is not None and pts_3rd < pts:
            errors.append(f"  {display:40s} pts={pts} > pts_3rd={pts_3rd}  (cheaper 3rd+!)")
    assert not errors, (
        f"{slug}: {len(errors)} units have pts_3rd CHEAPER than pts:\n"
        + "\n".join(errors)
    )


@pytest.mark.parametrize("slug", TEST_FACTIONS)
def test_pts_and_pts_3rd_non_negative(slug: str):
    """No unit has negative or zero pricing."""
    config_units = _load_config_units(slug)
    errors = []
    for norm_name, (display, entry, fn) in sorted(config_units.items()):
        if _is_exempt(display):
            continue
        if entry["pts"] <= 0:
            errors.append(f"  {display:40s} pts={entry['pts']}")
        pts_3rd = entry.get("pts_3rd")
        if pts_3rd is not None and pts_3rd <= 0:
            errors.append(f"  {display:40s} pts_3rd={pts_3rd}")
    assert not errors, (
        f"{slug}: {len(errors)} units have zero/negative pricing:\n"
        + "\n".join(errors)
    )
