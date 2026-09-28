"""Tests for the config-vs-BSData weapon name matching ladder.

Context: `validate_configs_vs_bsdata.py --all` reported 68 HIGH findings, of
which 55 were `NOT IN DATA`. Measured against HEAD, those 55 collapsed to 35
unique weapons, and 5 of them were the SAME weapon as the merged corpus entry,
differing only in case or punctuation ('Combi weapon' vs 'Combi-weapon'), because
the fallback compared raw substrings and so was blind to hyphens.

The ladder's last rung is now squashed *equality* (case + punctuation
insensitive). These tests pin both halves: punctuation variants resolve, and
weapons the corpus genuinely lacks are still reported.
"""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.validate_configs_vs_bsdata import (  # noqa: E402
    dedupe_issues,
    squash,
    validate_unit,
)


def _not_in_data(issues):
    return [msg for _, msg in issues if msg.startswith("NOT IN DATA")]


def _check(config_weapon, catalog_names):
    """Run check 1 for one unit holding a single weapon."""
    issues = validate_unit(
        "Test Unit",
        {"ranged": [config_weapon]},
        [],                      # no merged weapons for this unit
        None,                    # no BSData constraints -> check 1 only
        {n.lower() for n in catalog_names},
    )
    return _not_in_data(issues)


# ---------------------------------------------------------------------------
# squash(): punctuation-insensitive comparison
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("a,b", [
    ("Combi-weapon", "combi weapon"),
    ("Hunter-slayer missile", "hunter slayer missile"),
    ("Sanctus bio-dagger", "sanctus bio dagger"),
    ("Drones (0-2)", "drones 0 2"),
    # The apostrophe is dropped either way, so the following 's' must survive.
    ("Makari’s stabba", "Makari's stabba"),
    ("C'tan Powers", "C’TAN POWERS"),
])
def test_squash_ignores_case_and_punctuation(a, b):
    assert squash(a) == squash(b)


def test_squash_still_distinguishes_different_weapons():
    assert squash("Combi-weapon") != squash("Combi-cannon")
    assert squash("Plasma Pistol") != squash("Plasma Rifle")


# ---------------------------------------------------------------------------
# The fix: punctuation-only differences must not be reported as findings
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("config_weapon,catalog_name", [
    ("Combi weapon", "Combi-weapon"),
    ("hunter slayer missile", "Hunter-slayer missile"),
    ("sanctus bio dagger", "Sanctus bio-dagger"),
    ("drones (0 2)", "Drones (0-2)"),
    ("grav pistol", "Grav-pistol"),
])
def test_punctuation_only_difference_is_not_a_finding(config_weapon, catalog_name):
    """Each case fails against HEAD's punctuation-blind matcher."""
    assert _check(config_weapon, [catalog_name]) == []


def test_exact_match_is_not_a_finding():
    assert _check("Combi-weapon", ["Combi-weapon"]) == []


# ---------------------------------------------------------------------------
# ...but the fix must not hide real findings
# ---------------------------------------------------------------------------


def test_genuinely_absent_weapon_is_still_high():
    assert _check("Frobnitzer of Doom", ["Combi-weapon"]) == [
        "NOT IN DATA: 'Frobnitzer of Doom'"]


@pytest.mark.parametrize("fragment,victim", [
    # A generic catalog word must not vouch for a longer config name. Under a
    # substring matcher, catalog 'weapons' silently cleared this one.
    ("weapons", "Fleshmetal weapons"),
    ("shield", "blizzard shield"),
    # A short but real catalog weapon must not vouch for a different one.
    ("Bane", "Baneblade"),
    ("Claws", "Slaughter claws"),
    ("Missile Launcher", "Cyclone missile launcher"),
])
def test_substring_of_a_catalog_name_is_not_a_match(fragment, victim):
    """This is the reason the last rung is equality, not containment.

    Each pair is a real name from the corpus, not an invented one.
    """
    assert _check(victim, [fragment]), (
        f"catalog '{fragment}' must not vouch for '{victim}'")


@pytest.mark.parametrize("empty_squash", ["—", "➤", "- - -", " "])
def test_name_squashing_to_empty_matches_nothing(empty_squash):
    """`'' in anything` is True in Python; equality must not inherit that."""
    assert squash(empty_squash) == ""
    assert _check(empty_squash, ["boltgun", "anythingatall"])


def test_real_short_weapon_still_matches_its_own_config_entry():
    """Dropping substring matching must not break an exact short name."""
    assert _check("Bane", ["Bane"]) == []
    assert _check("Claws", ["claws"]) == []


# ---------------------------------------------------------------------------
# Duplicate collapsing
# ---------------------------------------------------------------------------


def test_dedupe_collapses_identical_messages_keeping_order():
    issues = [
        ("HIGH", "NOT IN DATA: 'a'"),
        ("MEDIUM", "MISSING FIXED MELEE: 'b'"),
        ("HIGH", "NOT IN DATA: 'a'"),
    ]
    assert dedupe_issues(issues) == [
        ("HIGH", "NOT IN DATA: 'a'"),
        ("MEDIUM", "MISSING FIXED MELEE: 'b'"),
    ]


def test_dedupe_keeps_distinct_messages():
    issues = [("HIGH", "GROUP CAP 'a': 1 != 2"), ("HIGH", "GROUP CAP 'b': 1 != 2")]
    assert len(dedupe_issues(issues)) == 2


# ---------------------------------------------------------------------------
# Real merged data: bind the behaviour to the corpus, don't hand-write names
# ---------------------------------------------------------------------------


def _real_weapon_names():
    names = set()
    for merged in (REPO_ROOT / "data" / "merged").glob("*.json"):
        data = json.loads(merged.read_text(encoding="utf-8-sig"))
        for unit in data.get("units", []):
            profile = unit.get("profile") or {}
            for weapon in profile.get("weapons", []):
                if isinstance(weapon, dict) and weapon.get("name"):
                    names.add(weapon["name"])
    return names


def test_hyphenated_corpus_weapon_resolves_its_spaced_variant():
    """Self-locating: find a real hyphenated weapon, test the spaced form.

    Fails loudly if the corpus stops containing hyphens, so the test cannot
    silently stop asserting.
    """
    real = _real_weapon_names()
    hyphenated = sorted(n for n in real if "-" in n)
    assert hyphenated, "no hyphenated weapon in merged corpus — test needs updating"

    real_sq = {squash(n) for n in real}
    for name in hyphenated:
        spaced_sq = squash(name.replace("-", " "))
        assert spaced_sq in real_sq, f"'{name}' should resolve to its spaced form"
