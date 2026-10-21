"""Guards for the Key Insights layer of the findings pages.

Two failure modes are pinned here:

1. Stale detachment roster. The roster used to be hand-written in the expert
   markdown, so an MFM bump left 10e detachments rendering as current 11e
   content. The roster is now L0 data (``data/merged/<fid>.json``) and the
   expert file supplies the rating only -- a name that no longer exists is
   dropped, a roster entry with no expert block stays 'Unrated'.

2. Empty play pattern. The play-pattern regex captured the line AFTER the
   marker, so the "How this army plays" card never rendered for any faction.

These are structural checks: they fail when a source of truth changes shape,
not when a rating or a word changes.
"""
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.gen_findings_html import (  # noqa: E402
    FACTIONS,
    MISSIONS,
    gen_html,
    parse_expert_assessment,
)

MERGED = ROOT / "data" / "merged"
EXPERTS = ROOT / "resources" / "experts"
RATINGS = {"Strong", "Moderate", "Situational", "Weak", "Unrated"}

# Factions whose disposition-fit table is maintained in full (one row per
# mission). Single-unit factions legitimately carry a one-row table.
MAINTAINED_DISPOSITION_TABLES = (
    "space-marines", "dark-angels", "blood-angels", "space-wolves",
    "black-templars", "deathwatch", "orks",
)


@pytest.fixture(params=sorted(FACTIONS.keys()), ids=sorted(FACTIONS.values()))
def fid(request):
    """Yield each faction slug once."""
    return request.param


def _expert(fid):
    """Parsed expert assessment for a faction, or skip."""
    exp = parse_expert_assessment(fid)
    if not exp:
        pytest.skip(f"{fid}: no expert assessment")
    return exp


def _merged_roster(fid):
    """Detachment roster as L0 truth, or skip if the faction has no merged data."""
    path = MERGED / f"{fid}.json"
    if not path.is_file():
        pytest.skip(f"{fid}: no merged data")
    merged = json.loads(path.read_text(encoding="utf-8"))
    return merged.get("detachments", [])


class TestKeyInsightsRoster:
    """The rendered roster is L0 data, not hand-written prose."""

    def test_roster_matches_merged_data(self, fid):
        exp = _expert(fid)
        want = [d.get("name") for d in _merged_roster(fid)]
        got = [d["name"] for d in exp["detachments"]]
        assert got == want, (
            f"{fid}: rendered detachment roster drifted from "
            f"data/merged/{fid}.json")

    def test_every_roster_entry_carries_a_rating_band(self, fid):
        exp = _expert(fid)
        for det in exp["detachments"]:
            assert det["rating"] in RATINGS, (
                f"{fid}: {det['name']} has rating {det['rating']!r}")

    def test_unrated_list_matches_roster(self, fid):
        exp = _expert(fid)
        unrated = sorted(d["name"] for d in exp["detachments"]
                         if d["rating"] == "Unrated")
        assert unrated == sorted(exp["unrated_detachments"]), (
            f"{fid}: unrated list disagrees with the rendered roster")

    def test_no_dropped_detachment_leaks_into_the_roster(self, fid):
        """A detachment that no longer exists in 11e must not be rendered."""
        exp = _expert(fid)
        rendered = {d["name"] for d in exp["detachments"]}
        for name in exp["stale_expert_detachments"]:
            assert name not in rendered, (
                f"{fid}: stale detachment {name!r} is still rendered")


class TestKeyInsightsProse:
    """Army rule and play pattern are parsed out of the expert file."""

    def test_play_pattern_is_not_empty(self, fid):
        exp = _expert(fid)
        assert exp["play_pattern"].strip(), (
            f"{fid}: no play pattern parsed -- the card would render empty")

    def test_play_pattern_is_not_duplicated_in_the_army_rule(self, fid):
        exp = _expert(fid)
        assert "Play pattern" not in exp["army_rule"], (
            f"{fid}: play pattern bullet left in the army-rule text")

    def test_disposition_fit_rows_are_valid(self, fid):
        exp = _expert(fid)
        seen = []
        for row in exp["disposition_fit"]:
            assert row["mission"] in MISSIONS, (
                f"{fid}: unknown mission {row['mission']!r}")
            assert row["fit"] in {"Strong", "Moderate", "Situational", "Weak"}
            assert row["why"].strip()
            seen.append(row["mission"])
        assert len(seen) == len(set(seen)), (
            f"{fid}: disposition fit table repeats a mission: {seen}")

    @pytest.mark.parametrize("fid", MAINTAINED_DISPOSITION_TABLES)
    def test_maintained_disposition_table_covers_every_mission(self, fid):
        exp = _expert(fid)
        assert len(exp["disposition_fit"]) == 5, (
            f"{fid}: maintained disposition fit table has "
            f"{len(exp['disposition_fit'])} rows, expected 5")

    def test_retired_army_rule_is_marked_as_retired(self, fid):
        """A retired rule may be named, but never as current."""
        exp = _expert(fid)
        text = "\n".join([
            exp["army_rule"],
            exp["play_pattern"],
            "\n".join(r["why"] for r in exp["disposition_fit"]),
        ])
        for line in text.splitlines():
            if "Oath of Moment" not in line:
                continue
            assert "RETIRED" in line, (
                f"{fid}: Oath of Moment named without a retired marker: {line!r}")


class TestKeyInsightsHtml:
    """The generated page carries the same payload."""

    def test_page_payload_matches_the_parser(self, fid):
        exp = _expert(fid)
        out = gen_html("Faction", {"meta": {}, "meta_info": []}, 0, fid=fid)
        match = re.search(r'const EXPERT=(.*?);\nconst ', out, re.S)
        assert match, "const EXPERT= blob not found"
        payload = json.loads(match.group(1))
        assert payload["play_pattern"] == exp["play_pattern"]
        assert [d["name"] for d in payload["detachments"]] == [
            d["name"] for d in exp["detachments"]]
        assert payload["unrated_count"] == len(
            [d for d in exp["detachments"] if d["rating"] == "Unrated"])

    def test_page_payload_has_no_stale_diagnostic(self, fid):
        out = gen_html("Faction", {"meta": {}, "meta_info": []}, 0, fid=fid)
        match = re.search(r'const EXPERT=(.*?);\nconst ', out, re.S)
        payload = json.loads(match.group(1))
        assert "stale_expert_detachments" not in payload, (
            f"{fid}: generator diagnostic leaked into the page payload")
