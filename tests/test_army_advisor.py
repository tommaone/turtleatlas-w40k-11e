"""Regression tests for the army-choice guide's first-army recommendations.

Catch the class of bug the user caught on 2026-09-06: World Eaters
recommended as a first army because a roster-wide wounds median (vehicles
included) came out "Durable", while their 2W melee core punishes every
positioning error.

These tests run pure computation (compute()/guide_lines()) — no generated
artifacts are written, so suite runs never touch tracked files.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import army_advisor as aa


def _first_army_names():
    data = aa.compute()
    lines = aa.guide_lines(data)
    names, in_section = [], False
    for ln in lines:
        if ln.startswith("## If this is"):
            in_section = True
            continue
        if in_section and ln.startswith("## "):
            break
        if in_section and ln.startswith("- **"):
            names.append(ln.split("**", 2)[1])
    return names


def test_world_eaters_not_a_first_army():
    # Regression for the exact bug the user caught: statline bulk says
    # "Durable" (median W 8 via vehicles) but the 2W melee core is fragile.
    statline = aa.durability_map()["world-eaters"]
    assert statline["statline_band"] == "Durable"
    assert "World Eaters" not in _first_army_names()


def test_dark_angels_in_first_army():
    names = _first_army_names()
    assert names and "Dark Angels" == names[0]


def test_death_guard_and_custodes_in_first_army():
    names = _first_army_names()
    assert "Death Guard" in names
    assert "Adeptus Custodes" in names


def test_imperial_knights_not_a_first_army():
    assert "Imperial Knights" not in _first_army_names()


def test_only_expert_rated_factions_in_first_army():
    data = aa.compute()
    fit = [x["fid"] for x in data["factions"]
           if x["first_army_fit"] in ("Great", "Good")]
    names = _first_army_names()
    for n in names:
        fid = [x["fid"] for x in data["factions"] if x["name"] == n]
        assert fid and fid[0] in fit, f"{n} listed without expert Great/Good fit"


def test_guide_header_is_fresh():
    data = aa.compute()
    lines = aa.guide_lines(data)
    assert any("Generated 2026-09-06" in ln for ln in lines[:4])
    assert not any("2026-08-23" in ln for ln in lines)
    assert data["generated"] == "2026-09-06"