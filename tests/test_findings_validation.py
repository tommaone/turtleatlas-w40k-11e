"""Validation tests for findings HTML generation.

Ensures every faction's build_data() output is consistent:
- n_units matches actual unique units in build_data output
- n_units matches compute_ranking() output count
- No unit has a score of 0 or NaN
- Every mission has the same set of unit names
- Metadata keys never appear as unit names
"""

import json
import math
import re
import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.gen_findings_html import (
    FACTIONS,
    MISSIONS,
    build_data,
    _count_ranked_units,
    attach_heuristics,
)
from engine.ranking import RankingEngine

ROOT = Path(__file__).resolve().parent.parent
FINDINGS_ROOT = ROOT / "findings"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _meta_data(data):
    """Unwrap build_data output to the per-meta {mission: [units]} map."""
    # New shape: data = {'meta': {meta: {mission: [units]}}, 'meta_info': [...]}
    inner = data.get("meta") if isinstance(data, dict) else data
    return inner


def _mission_unit_names(data):
    """Return dict mapping mission → set of unit names (union across metas)."""
    union = {}
    for meta in _meta_data(data).values():
        for mission, units in meta.items():
            union.setdefault(mission, set()).update(u["name"] for u in units)
    return union


def _all_meta_units(data):
    """Iterate every (meta, mission) unit list — used by score/metadata checks."""
    for meta in _meta_data(data).values():
        for mission, units in meta.items():
            yield mission, units


def _meta_unit_items(data):
    """Yield (meta_name, mission, units) triples for every list."""
    for meta_name, meta in _meta_data(data).items():
        for mission, units in meta.items():
            yield meta_name, mission, units


# ---------------------------------------------------------------------------
# Tests — run once per faction (parametrized)
# ---------------------------------------------------------------------------

@pytest.fixture(params=sorted(FACTIONS.keys()), ids=sorted(FACTIONS.values()))
def faction_id(request):
    """Yield each faction slug once."""
    return request.param


class TestFindingsConsistency:
    """Core consistency checks for every faction."""

    def test_n_units_matches_build_data(self, faction_id):
        """n_units returned by build_data must equal the number of unique units in output."""
        data, n_units = build_data(faction_id, max_points=2000)
        # Per-meta unique set must match n_units (each meta has the same unit roster)
        for meta, missions in _meta_data(data).items():
            unique_names = set()
            for mission, units in missions.items():
                for u in units:
                    unique_names.add(u["name"])
            assert n_units == len(unique_names), (
                f"{faction_id}: n_units={n_units} but unique units in meta '{meta}'={len(unique_names)}. "
                f"Diff: {unique_names ^ set(range(n_units)) if n_units != len(unique_names) else ''}"
            )

    def test_n_units_matches_ranking(self, faction_id):
        """n_units from build_data must match compute_ranking() output length."""
        e = RankingEngine(faction_id)
        data, n_units = build_data(faction_id, max_points=2000)
        # compute_ranking without mission — same filters as build_data
        ranking = e.compute_ranking(max_points=2000)
        assert n_units == len(ranking), (
            f"{faction_id}: n_units={n_units} but compute_ranking returned {len(ranking)} units"
        )

    def test_no_zero_or_nan_scores(self, faction_id):
        """No unit in any meta/mission should have a score of 0 or NaN."""
        data, _ = build_data(faction_id, max_points=2000)
        for meta, units in _all_meta_units(data):
            for u in units:
                score = u["score"]
                assert score != 0, (
                    f"{faction_id}/meta '{u['name']}' has score=0"
                )
                assert not math.isnan(score), (
                    f"{faction_id}/meta='{meta}/{u['name']}' has NaN score"
                )
                assert not math.isinf(score), (
                    f"{faction_id}/meta='{meta}/{u['name']}' has Inf score"
                )

    def test_all_missions_same_units(self, faction_id):
        """Every mission must contain the same set of unit names (per meta)."""
        data, _ = build_data(faction_id, max_points=2000)
        for meta_name, missions in _meta_data(data).items():
            mission_names = _mission_unit_names({"meta": {meta_name: missions}})
            if not mission_names:
                continue
            # Use the first mission as reference
            ref_mission = MISSIONS[0]
            ref_names = mission_names.get(ref_mission, set())

            for mission in MISSIONS:
                current_names = mission_names.get(mission, set())
                missing = ref_names - current_names
                extra = current_names - ref_names
                assert not missing and not extra, (
                    f"{faction_id}/meta '{meta_name}': mission '{mission}' unit set "
                    f"differs from '{ref_mission}'. "
                    f"Missing: {missing or 'none'}  Extra: {extra or 'none'}"
                )

    def test_no_metadata_keys_as_units(self, faction_id):
        """Metadata keys (_note, _source, etc.) must never appear as unit names."""
        data, _ = build_data(faction_id, max_points=2000)
        for _meta_name, mission, units in _meta_unit_items(data):
            for u in units:
                name = u["name"]
                assert not name.startswith("_"), (
                    f"{faction_id}/meta '{_meta_name}/{mission}': metadata key '{name}' appears as a unit"
                )


class TestIndexCountMatchesPage:
    """findings/index.html card counts must equal the faction page roster.

    Regression for the old gen_index() regex that skimmed every
    `{"name": "..."}` string in the HTML — it also matched weapon profile
    names (e.g. 'Great cleaver of Khorne - sweep') and detachment names
    (e.g. 'Berzerker Warband'), inflating the index counts beyond the
    ranked roster (which already excludes legends).
    """

    def test_index_card_matches_page_roster(self, faction_id):
        """Index card count == unique units in the page's embedded DATA."""
        idx = (FINDINGS_ROOT / "index.html").read_text(encoding="utf-8")
        m = re.search(
            rf'href="{faction_id}/findings\.html"[^>]*>\s*'
            rf'<span class="fname">[^<]+</span>\s*'
            rf'<span class="fmeta">(\d+) units',
            idx,
        )
        assert m, f"{faction_id}: card missing from findings/index.html"
        page = FINDINGS_ROOT / faction_id / "findings.html"
        roster = _count_ranked_units(page.read_text(encoding="utf-8"))
        assert roster is not None, f"{faction_id}: page DATA unparseable"
        assert int(m.group(1)) == roster, (
            f"{faction_id}: index card says {m.group(1)} units "
            f"but the page renders {roster}"
        )

    def test_page_subtitle_matches_roster(self, faction_id):
        """Page subtitle (build_data's n_units) == embedded DATA roster."""
        page = FINDINGS_ROOT / faction_id / "findings.html"
        txt = page.read_text(encoding="utf-8")
        m = re.search(r'<div class="subtitle">(\d+) datasheets', txt)
        assert m, f"{faction_id}: no subtitle found"
        roster = _count_ranked_units(txt)
        assert roster is not None, f"{faction_id}: page DATA unparseable"
        assert int(m.group(1)) == roster, (
            f"{faction_id}: subtitle says {m.group(1)} datasheets "
            f"but the page renders {roster}"
        )


def _extract_tiers(html: str) -> list:
    """Parse the `var TIERS=...;` payload from findings/index.html."""
    marker = "var TIERS="
    idx = html.find(marker)
    assert idx != -1, "no TIERS payload in index.html"
    return json.JSONDecoder().raw_decode(html, idx + len(marker))[0]


class TestTierList:
    """Army Tier List tab: explainer, tab order, heuristic layer integrity.

    The tier list carries two explicitly-separated layers:
    - L0 numeric (engine output, rules-free) from findings/army_tiers.json
    - STRATEGY-tier heuristics (expert-rated guesswork, NOT engine output)
      attached at render time from resources/experts/<fid>.md
    These tests guard the separation: army_tiers.json stays pure engine
    output, the rendered page carries the labelled heuristic deltas, and the
    tab structure explains why the list is not exact.
    """

    def test_tabs_browse_first(self):
        """Browse Factions is the first (default) tab; tiers second."""
        idx = (FINDINGS_ROOT / "index.html").read_text(encoding="utf-8")
        tabs = re.findall(r'<button class="viewtab[^"]*"[^>]*>([^<]+)</button>', idx)
        assert len(tabs) == 2, f"expected 2 tabs, got {tabs}"
        assert tabs[0] == "Browse Factions", f"Browse must be first, got {tabs}"
        assert tabs[1] == "Army Tier List"
        m = re.search(r'<button class="viewtab active"[^>]*>([^<]+)</button>', idx)
        assert m and m.group(1) == "Browse Factions", (
            "Browse Factions must be the active default tab"
        )
        assert 'id="view-browse"' in idx and 'id="view-tiers" style="display:none"' in idx

    def test_tier_header_explains_limits(self):
        """Header explains what the list is and why it is not exact."""
        idx = (FINDINGS_ROOT / "index.html").read_text(encoding="utf-8")
        for phrase in (
            "What this is",
            "Why it is not exact",
            "L0 datasheet score",
            "11e core-rules fact",
            "BS +1",
            "not</strong> modify saves",
            "standardized 16-footprint layouts",
            "players and TOs report the new tables play",
            "more open / less LoS-blocking",
            "three mission maps (A/B/C)",
            "Codex-vintage skew",
            "not a win-rate model",
            "L0 datasheets only",
            "+ rules heuristics",
            "STRATEGY",
        ):
            assert phrase in idx, f"tier header missing: {phrase!r}"
        # dojo: never ship the unverifiable "more terrain-dense" claim again
        assert "more terrain-dense" not in idx, "unverifiable density claim is back"

    def test_tiers_payload_heuristics_shape(self):
        """Every tier entry carries the labelled heuristic layer."""
        idx = (FINDINGS_ROOT / "index.html").read_text(encoding="utf-8")
        tiers = _extract_tiers(idx)
        assert tiers, "TIERS payload empty"
        for t in tiers:
            assert isinstance(t["h_overall"], (int, float)), t["fid"]
            assert math.isfinite(t["h_overall"]), t["fid"]
            for m in MISSIONS:
                assert m in t["h_missions"], f"{t['fid']} missing {m}"
            assert "**" not in t["h_army"], f"{t['fid']} markdown leaked: {t['h_army']!r}"
            assert isinstance(t["h_army"], str) and isinstance(t["h_top"], str)
        assert any(t["h_overall"] != 0 for t in tiers), (
            "heuristic layer produced no opinions at all"
        )

    def test_army_tiers_json_stays_pure_engine(self):
        """findings/army_tiers.json must not carry heuristic (h_*) fields."""
        tiers = json.loads(
            (FINDINGS_ROOT / "army_tiers.json").read_text(encoding="utf-8")
        )
        assert tiers
        for fid, entry in tiers.items():
            hkeys = [k for k in entry if k.startswith("h_")]
            assert not hkeys, f"{fid}: heuristic fields leaked into engine file: {hkeys}"

    def test_rendered_heuristics_match_fresh_attach(self):
        """Page TIERS == attach_heuristics result (one source, one formula)."""
        tiers = json.loads(
            (FINDINGS_ROOT / "army_tiers.json").read_text(encoding="utf-8")
        )
        fresh = attach_heuristics(json.loads(json.dumps(tiers)))
        idx = (FINDINGS_ROOT / "index.html").read_text(encoding="utf-8")
        rendered = {t["fid"]: t for t in _extract_tiers(idx)}
        for fid, f in fresh.items():
            assert rendered[fid]["h_overall"] == f["h_overall"], fid
            assert rendered[fid]["h_missions"] == f["h_missions"], fid
            assert rendered[fid]["h_top"] == f["h_top"], fid

    def test_rules_heuristics_shift_order(self):
        """With heuristics ON the army order must differ from L0 order."""
        tiers = json.loads(
            (FINDINGS_ROOT / "army_tiers.json").read_text(encoding="utf-8")
        )
        fresh = attach_heuristics(json.loads(json.dumps(tiers)))
        l0 = sorted(tiers, key=lambda fid: -tiers[fid]["overall"])
        adj = sorted(
            tiers,
            key=lambda fid: -(tiers[fid]["overall"] + fresh[fid]["h_overall"]),
        )
        assert [fid for fid in l0] != [fid for fid in adj], (
            "rules heuristics made zero difference to army order"
        )


# ---------------------------------------------------------------------------
# Cross-faction summary (single test, not per-faction)
# ---------------------------------------------------------------------------

class TestFindingsCrossFaction:
    """Checks that span all factions at once."""

    def test_all_factions_produce_data(self):
        """Every faction in FACTIONS must produce non-empty build_data output."""
        failures = []
        for fid in sorted(FACTIONS.keys()):
            try:
                data, n = build_data(fid, max_points=2000)
                if n == 0:
                    failures.append(f"{fid}: 0 units")
            except Exception as e:
                failures.append(f"{fid}: {e}")
        assert not failures, f"Factions with no data or errors: {failures}"

    def test_all_factions_have_five_missions(self):
        """Every faction must produce data for all 5 missions in every meta."""
        for fid in sorted(FACTIONS.keys()):
            data, _ = build_data(fid, max_points=2000)
            metas = _meta_data(data)
            assert metas, f"{fid}: no meta presets in build_data output"
            for meta_name, missions in metas.items():
                assert set(missions.keys()) == set(MISSIONS), (
                    f"{fid}/meta '{meta_name}': expected missions "
                    f"{MISSIONS}, got {list(missions.keys())}"
                )
