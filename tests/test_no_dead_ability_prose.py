"""Guard the ability-prose strip: no dead rule text stays committed.

`scripts/strip_ability_prose.py` removes `description` from every merged ability
that the engine's prose-parsing detectors do not consume. AGENTS.md forbids
committing verbatim rule text, and 89% of the corpus prose was unread dead
weight.

This file pins the invariant in the direction that is checkable from the
committed artifact: **if a description is present, something reads it.** Without
this test, a `bsdata` bump that regenerates merged data would quietly restore
~530KB of rule text and nothing would notice.

The opposite direction — "nothing the engine needs got stripped" — cannot be
checked from a stripped artifact, because a stripped ability looks identical to
one that never had prose. That guarantee comes from the strip script only
removing prose when all three detectors return None, and from the before/after
probe (2704 abilities, 0 engine outputs changed). The aggregate counts asserted
in `test_load_bearing_counts_match_recorded_baseline` catch a regression in it.
"""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))
sys.path.insert(0, str(REPO_ROOT))

from damage_boost_detect import detect_damage_boost  # noqa: E402
from dpp import parse_transport_capacity  # noqa: E402
from reroll_detect import detect_army_wide_reroll, detect_reroll_ability  # noqa: E402

MERGED = REPO_ROOT / "data" / "merged"


def _all_abilities():
    for path in sorted(MERGED.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for unit in data.get("units", []):
            for ability in (unit.get("profile") or {}).get("abilities") or []:
                if isinstance(ability, dict):
                    yield path.name, unit.get("name"), ability


ABILITIES = list(_all_abilities())


def test_merged_corpus_has_abilities():
    assert len(ABILITIES) > 2000, "merged corpus looks unpopulated — is the submodule present?"


def test_no_dead_ability_prose_is_committed():
    """Every surviving description must be one the engine actually parses."""
    dead = [
        (f, u, a.get("name"))
        for f, u, a in ABILITIES
        if a.get("description")
        and detect_reroll_ability(a) is None
        and detect_army_wide_reroll(a) is None
        and detect_damage_boost(a) is None
        and not (str(a.get("name", "")).upper() == "TRANSPORT"
                 and parse_transport_capacity(a.get("description")) is not None)
    ]
    assert not dead, (
        f"{len(dead)} committed ability description(s) that no engine detector reads. "
        f"Run: python3 scripts/strip_ability_prose.py  first 3: {dead[:3]}"
    )


def test_strip_script_is_idempotent():
    """Re-running the strip must find nothing left to do."""
    import subprocess
    out = subprocess.run(
        [sys.executable, "scripts/strip_ability_prose.py", "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert out.returncode == 0, f"--check failed, dead prose present:\n{out.stdout}"


def test_load_bearing_counts_match_recorded_baseline():
    """Pins that nothing the engine parses was stripped.

    A `bsdata` bump legitimately changes these numbers — update the baseline in
    the same commit that regenerates merged data, and say so in the commit body.
    """
    counts = {
        "reroll": sum(1 for _, _, a in ABILITIES if detect_reroll_ability(a)),
        "army_wide_reroll": sum(1 for _, _, a in ABILITIES if detect_army_wide_reroll(a)),
        "damage_boost": sum(1 for _, _, a in ABILITIES if detect_damage_boost(a)),
        "transport_capacity": sum(
            1 for _, _, a in ABILITIES
            if str(a.get("name", "")).upper() == "TRANSPORT"
            and parse_transport_capacity(a.get("description")) is not None
        ),
    }
    assert counts == {
        "reroll": 32,
        "army_wide_reroll": 128,
        "damage_boost": 1,
        "transport_capacity": 134,
    }, (
        "load-bearing ability counts moved. If a bsdata bump caused this, update the "
        f"baseline in this test in the same commit. Got: {counts}"
    )


def test_every_transport_ability_retains_parseable_capacity():
    """The transport path is prose-driven, so it must survive the strip."""
    transports = [
        a for _, _, a in ABILITIES
        if str(a.get("name", "")).upper() == "TRANSPORT"
    ]
    assert transports, "no Transport abilities in merged — merge looks wrong"
    unparseable = [a.get("description", "") for a in transports
                   if parse_transport_capacity(a.get("description")) is None]
    # Some Transport entries legitimately carry no model count (the Manta's
    # "of all of the following", the Night Scythe's unit count). Those are
    # documented returns-None-by-design in dpp.parse_transport_capacity.
    assert len(unparseable) < len(transports), (
        f"all {len(transports)} Transport abilities lost parseable capacity"
    )
