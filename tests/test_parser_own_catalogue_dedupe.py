"""Regression locks for the own-catalogue dedupe fix.

query_faction's dedupe pass 2 previously picked the "most complete" entry
per unit name, letting stale linked-library duplicates (e.g. the 10e-era
Chaos Daemons Library) override the faction's own 11e catalogue entry.

The library entries carry the wrong faction keyword (Faction: Legiones
Daemonica) plus legacy junk links (e.g. "Shadow Legion", "Khorne Battleline"),
so the ranking faction-keyword filter dropped the units entirely — Bloodletters
was missing from the World Eaters ranking until this fix.

Lock: when both the faction's own catalogue and a linked library define the
same unit, the own-catalogue entry wins (it carries the current 11e profile +
the correct god-legion faction keyword). The completeness heuristic only fills
gaps for factions whose own catalogue is a linked-library shell (Drukhari).

STRUCTURE ONLY — no damage values. The engine is the single source of
computation; this locks parser output shape, not math.

Run: python3 -m pytest tests/test_parser_own_catalogue_dedupe.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from adapter.bsdata_parser_11e import BSDataParser11e

# (faction, unit, expected OC, expected faction keyword, stale keywords that must be gone)
CASES = [
    (
        "Chaos - World Eaters",
        "Bloodletters",
        "1",
        "Faction: Blood Legions",
        ["Faction: Legiones Daemonica", "Khorne Battleline", "Shadow Legion"],
    ),
    (
        "Chaos - Emperor's Children",
        "Daemonettes",
        "1",
        "Faction: Legions of Excess",
        ["Faction: Legiones Daemonica", "Slaanesh Battleline", "Shadow Legion"],
    ),
    (
        "Chaos - Thousand Sons",
        "Pink Horrors",
        "1",
        "Faction: Scintillating Legions",
        ["Faction: Legiones Daemonica", "Tzeentch Battleline", "Shadow Legion"],
    ),
    (
        "Chaos - Thousand Sons",
        "Blue Horrors",
        "0",
        "Faction: Scintillating Legions",
        ["Faction: Legiones Daemonica", "Tzeentch Battleline", "Shadow Legion"],
    ),
]


@pytest.fixture(scope="module")
def parser() -> BSDataParser11e:
    return BSDataParser11e()


@pytest.mark.parametrize(
    "faction,unit,expect_oc,faction_kw,stale_kws", CASES,
    ids=[f"{c[0]}/{c[1]}" for c in CASES],
)
def test_own_catalogue_entry_wins(parser, faction, unit, expect_oc, faction_kw, stale_kws):
    result = parser.query_faction(faction)
    assert result is not None, f"{faction}: not parsed"
    matches = [u for u in result["units"] if u["name"] == unit]
    assert len(matches) == 1, f"{faction}/{unit}: expected exactly 1 unit, got {len(matches)}"
    u = matches[0]

    stats = u.get("stats") or {}
    assert stats.get("OC") == expect_oc, (
        f"{faction}/{unit}: OC={stats.get('OC')}, expected {expect_oc} "
        "(own-catalogue 11e profile must win over the stale library entry)"
    )

    kws = u.get("keywords") or []
    assert faction_kw in kws, f"{faction}/{unit}: missing {faction_kw} in {kws}"
    for stale in stale_kws:
        assert stale not in kws, f"{faction}/{unit}: stale keyword {stale!r} still present in {kws}"
