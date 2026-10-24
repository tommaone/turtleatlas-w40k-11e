"""Guards for the Key Insights layer of the findings pages.

Failure modes pinned here:

1. Stale detachment roster. The roster used to be hand-written in the expert
   markdown, so an MFM bump left 10e detachments rendering as current 11e
   content. The roster is now L0 data (``data/merged/<fid>.json``) and the
   expert file supplies the rating only -- a name that no longer exists is
   dropped, a roster entry with no expert block stays 'Unrated'.

2. Empty play pattern. The play-pattern regex captured the line AFTER the
   marker, so the "How this army plays" card never rendered for any faction.

3. Rating without its disposition. A band is a claim ABOUT a mission
   ("Strong for Disruption"). Pairing it with whatever the 11e roster lists
   first credits a judgement to a mission the expert never made it for, so
   the rating carries its disposition and only applies when the 11e package
   still queues for that mission.

4. Retired rules leaking back in. "Oath of Moment" may be named as research
   history, never as a live mechanic.

The structural checks fail when a source of truth changes shape. The pinned
ratings in ``PINNED_RATINGS`` fail when a band is changed on purpose -- that
is the point: a band change must be a conscious edit, not a side effect of a
data bump.
"""
import json
import re
import subprocess
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

# One known-rated detachment per maintained faction, with the band and the
# disposition it was judged for. Changing a band on purpose means updating
# this table in the same commit -- an unpinned rating cannot be audited.
PINNED_RATINGS = {
    "space-marines": ("Gladius Task Force", "Strong", "Priority Assets"),
    "dark-angels": ("Gladius Task Force", "Strong", "Priority Assets"),
    "blood-angels": ("Gladius Task Force", "Moderate", "Priority Assets"),
    "space-wolves": ("Gladius Task Force", "Moderate", "Priority Assets"),
    "black-templars": ("Marshal's Household", "Situational", "Priority Assets"),
    "deathwatch": ("Gladius Task Force", "Moderate", "Priority Assets"),
    "orks": ("War Horde", "Strong", "Take and Hold"),
}

# 10e-only detachment names that must never reach an 11e page.
RETIRED_DETACHMENTS = {
    "space-marines": ("Vanguard Spearhead", "Hammer of Avernii"),
    "dark-angels": ("Unforgiven Task Force", "Vengeful Hosts"),
    "blood-angels": ("Liberator Assault Group", "The Angelic Host"),
    "space-wolves": ("Veterans of the Fang", "Saga of the Hunter"),
    "black-templars": ("Companions of Vehemence", "Wrathful Procession"),
    "deathwatch": ("Vanguard Spearhead", "Vengeful Hosts"),
    "orks": ("More Dakka!", "Rollin' Deff"),
}


def _norm(s):
    """Normalise a name for comparison (case, apostrophes, punctuation)."""
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())


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

    def test_dp_and_objectives_come_from_merged_data(self, fid):
        """The rendered card must not carry a hand-written DP or objective."""
        exp = _expert(fid)
        merged = {d["name"]: d for d in _merged_roster(fid)}
        for det in exp["detachments"]:
            src = merged[det["name"]]
            assert det["dp"] == src.get("dp"), (
                f"{fid}: {det['name']} DP {det['dp']} != merged "
                f"{src.get('dp')}")
            assert det["objectives"] == list(src.get("objectives") or []), (
                f"{fid}: {det['name']} objectives differ from merged data")

    def test_roster_keys_are_unique(self, fid):
        """Two roster entries normalising to one key would merge silently."""
        exp = _expert(fid)
        keys = [_norm(d["name"]) for d in exp["detachments"]]
        dupes = {k for k in keys if keys.count(k) > 1}
        assert not dupes, f"{fid}: duplicate detachment keys {sorted(dupes)}"

    def test_rating_is_paired_with_a_served_disposition(self, fid):
        """A band only applies if the 11e package still queues for it."""
        exp = _expert(fid)
        for det in exp["detachments"]:
            if det["rating"] == "Unrated":
                assert not det.get("rating_for"), (
                    f"{fid}: {det['name']} is Unrated but names a disposition")
                continue
            assert det.get("rating_for"), (
                f"{fid}: {det['name']} is rated {det['rating']} without the "
                f"disposition it was judged for")
            served = {_norm(o) for o in det["objectives"]}
            assert _norm(det["rating_for"]) in served, (
                f"{fid}: {det['name']} rated for {det['rating_for']} but the "
                f"11e package queues for {det['objectives']}")

    def test_mismatched_expert_block_keeps_no_rating(self, fid):
        """A block judged for a mission the 11e package dropped is Unrated."""
        exp = _expert(fid)
        for bad in exp.get("mismatched_expert_detachments", []):
            hit = [d for d in exp["detachments"]
                   if _norm(d["name"]) == _norm(bad["name"])]
            assert hit, f"{fid}: {bad['name']} reported mismatched but absent"
            assert hit[0]["rating"] == "Unrated", (
                f"{fid}: {bad['name']} was judged for "
                f"{bad['rated_for']} but is still rated {hit[0]['rating']}")


class TestKeyInsightsPins:
    """Deliberate edits are pinned; data bumps cannot move a band silently."""

    @pytest.mark.parametrize("fid", sorted(PINNED_RATINGS))
    def test_pinned_rating_still_holds(self, fid):
        name, band, rated_for = PINNED_RATINGS[fid]
        exp = _expert(fid)
        hit = [d for d in exp["detachments"] if _norm(d["name"]) == _norm(name)]
        assert hit, f"{fid}: pinned detachment {name!r} is not in the roster"
        assert hit[0]["rating"] == band, (
            f"{fid}: {name} is rated {hit[0]['rating']}, pinned as {band} -- "
            f"update PINNED_RATINGS in the same commit as the band change")
        assert hit[0]["rating_for"] == rated_for, (
            f"{fid}: {name} is rated for {hit[0]['rating_for']}, pinned as "
            f"{rated_for}")

    @pytest.mark.parametrize("fid", sorted(RETIRED_DETACHMENTS))
    def test_retired_detachment_never_renders(self, fid):
        exp = _expert(fid)
        rendered = {_norm(d["name"]) for d in exp["detachments"]}
        for name in RETIRED_DETACHMENTS[fid]:
            assert _norm(name) not in rendered, (
                f"{fid}: 10e detachment {name!r} is still rendered as 11e")


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

    def test_oath_of_moment_is_never_live_in_the_whole_file(self, fid):
        """Whole-file scan: a live Oath claim needs a 10e/retired marker."""
        path = EXPERTS / f"{fid}.md"
        if not path.is_file():
            pytest.skip(f"{fid}: no expert file")
        for lineno, line in enumerate(path.read_text(encoding="utf-8")
                                     .splitlines(), 1):
            if "Oath of Moment" not in line:
                continue
            assert ("RETIRED" in line or "10e record" in line), (
                f"{fid}:{lineno}: Oath of Moment named as current: {line!r}")


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
        assert "mismatched_expert_detachments" not in payload, (
            f"{fid}: generator diagnostic leaked into the page payload")

    def test_page_payload_carries_the_rating_disposition(self, fid):
        """The rendered card must show which disposition a band was judged for."""
        exp = _expert(fid)
        out = gen_html("Faction", {"meta": {}, "meta_info": []}, 0, fid=fid)
        match = re.search(r'const EXPERT=(.*?);\nconst ', out, re.S)
        payload = json.loads(match.group(1))
        for det in payload["detachments"]:
            src = next(d for d in exp["detachments"] if d["name"] == det["name"])
            assert det.get("rating_for") == src.get("rating_for"), (
                f"{fid}: {det['name']} lost its rated disposition on the page")
            if det["rating"] == "Unrated":
                assert not det.get("rating_for"), (
                    f"{fid}: {det['name']} is Unrated on the page but carries "
                    f"a disposition")


class TestGeneratedPageScript:
    """The page script must parse -- a broken template kills the whole page."""

    def test_generated_page_script_parses(self, fid, tmp_path):
        page = ROOT / "findings" / fid / "findings.html"
        if not page.is_file():
            pytest.skip(f"{fid}: no generated page")
        script = re.search(r"<script>(.*)</script>", page.read_text(encoding="utf-8"),
                           re.S)
        assert script, f"{fid}: generated page has no script block"
        js = tmp_path / "page.js"
        js.write_text(script.group(1), encoding="utf-8")
        proc = subprocess.run(["node", "--check", str(js)],
                              capture_output=True, text=True)
        if proc.returncode == 127:  # node not installed
            pytest.skip("node is not available")
        assert proc.returncode == 0, (
            f"{fid}: generated page script does not parse:\n{proc.stderr}")
