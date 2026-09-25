"""Guard: MFM duplicate names are pricing TIERS, not separate units.

imperial-agents lists 29 of its units twice — the second entry carries
groupTitle ("Every Model Has The Imperium Keyword") at a different rate.
The merge map was last-wins, so that opt-in group rate became the base
price for 14 units, overstating their points and understating DPP/point.

This test calls merge_faction() LIVE on purpose. A test that reads the
committed data/merged/imperial-agents.json only asserts a checked-in
artifact matches a literal — it stays green when adapter/merge.py is
reverted to the buggy last-wins map, which is exactly what a static
golden pin did before. The committed-artifact assertion is kept as a
second test so a stale regen is still caught.

The same rule also lives in tests/test_config_points_match_mfm.py (the
config oracle) and scripts/sync_config_pts.py (the sanctioned writer);
all three must prefer the plain entry.
"""

import json
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

MFM_IA = REPO / "mfm" / "data" / "imperial-agents.yaml"
MERGED_IA = REPO / "data" / "merged" / "imperial-agents.json"

# Deliberate tripwire, not a derived expectation: these are the upstream
# prices as of the 2026-09-25 MFM snapshot. If MFM restructures
# imperial-agents this fails loudly, which is the point — it must not
# silently accept a reshaped duplicate-name scheme.
DUPLICATED = {
    "Eversor Assassin": (100, 110),
    "Exaction Squad": (90, 85),
    "Grey Knights Terminator Squad": (175, 190),
    "Inquisitor": (55, 65),
    "Inquisitor Coteaz": (75, 95),
    "Inquisitor Draxus": (75, 110),
    "Inquisitorial Agents": (50, 60),
    "Navigator": (60, 75),
    "Rogue Trader Entourage": (75, 105),
    "Sisters Of Battle Immolator": (90, 105),
    "Sisters Of Battle Squad": (100, 110),
    "Subductor Squad": (85, 100),
    "Vindicare Assassin": (110, 125),
    "Voidsmen-At-Arms": (50, 70),
}


def _plain_and_group(faction_yaml):
    """name -> (plain price, groupTitle price) for the units that have both."""
    plain, group = {}, {}
    for u in faction_yaml.get("units", []):
        costs = [c for pr in (u.get("pricing") or []) for c in pr.get("costs", [])
                 if c.get("points") is not None]
        if not costs:
            continue
        (group if u.get("groupTitle") else plain)[u["name"]] = costs[0]["points"]
    return {n: (plain[n], group[n]) for n in plain if n in group}


def _base_points(merged_units):
    """name -> first-tier points, as adapter/merge.py writes them."""
    out = {}
    for u in merged_units:
        costs = (u.get("pricing") or [{}])[0].get("costs") or []
        if costs:
            out[u["name"]] = costs[0].get("points")
    return out


@pytest.fixture(scope="module")
def ia_merged_live():
    """Run the real merge so a revert of the dedup rule cannot stay green."""
    from adapter.merge import load_mfm_faction, merge_faction
    from adapter.bsdata_parser import BSDataParser

    mfm = load_mfm_faction("imperial-agents")
    assert mfm, "MFM imperial-agents.yaml did not load"
    return merge_faction("imperial-agents", mfm, BSDataParser(REPO / "bsdata" / "data"))


def test_mfm_still_lists_ia_units_twice():
    """The data shape this rule exists for is still present.

    29 units are listed twice; 15 of those pairs agree on price, 14 diverge.
    Only the divergent ones are in DUPLICATED — the agreeing pairs are harmless
    either way, which is why the bug was invisible in aggregate.
    """
    dupes = _plain_and_group(yaml.safe_load(MFM_IA.read_text(encoding="utf-8")))
    divergent = {n: v for n, v in dupes.items() if v[0] != v[1]}
    assert divergent == DUPLICATED, "MFM duplicate-name pricing changed upstream"


def test_live_merge_prices_from_the_plain_entry(ia_merged_live):
    """The regression guard: a last-wins map fails here."""
    got = _base_points(ia_merged_live["units"])
    wrong = {n: (got.get(n), plain, grp) for n, (plain, grp) in DUPLICATED.items()
             if got.get(n) != plain}
    assert not wrong, f"merge priced from the groupTitle tier: {wrong}"


def test_live_merge_roster_keeps_every_duplicated_unit(ia_merged_live):
    """The dedup must merge tiers, never drop a unit.

    The plain-over-groupTitle fallback is load-bearing beyond this file: 11
    other factions list 459 units that are group-ONLY (the successors'
    "Space Marines", Ynnari, Harlequins). Deleting the fallback collapses
    those rosters — blood-angels dropped 99 -> 15 units.

    (merged/ is a BSData roster with MFM points attached, so MFM-only units
    such as the Kill Teams and Daemonhost are legitimately absent. The
    invariant here is narrower and is the one the dedup could break.)
    """
    merged_units = {u["name"] for u in ia_merged_live["units"]}
    missing = {n for n in DUPLICATED if n not in merged_units}
    assert not missing, f"dedup dropped duplicated units: {sorted(missing)}"


def test_committed_merged_matches_a_live_merge(ia_merged_live):
    """Guards against a stale regen: committed merged data must equal what the
    pipeline produces now."""
    committed = json.loads(MERGED_IA.read_text(encoding="utf-8"))
    assert _base_points(committed["units"]) == _base_points(ia_merged_live["units"])
