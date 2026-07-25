"""Validation tests for findings HTML generation.

Ensures every faction's build_data() output is consistent:
- n_units matches actual unique units in build_data output
- n_units matches compute_ranking() output count
- No unit has a score of 0 or NaN
- Every mission has the same set of unit names
- Metadata keys never appear as unit names
"""

import math
import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.gen_findings_html import FACTIONS, MISSIONS, build_data
from engine.ranking import RankingEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _all_unit_names(data):
    """Extract all unique unit names from build_data output across all missions."""
    names = set()
    for mission, units in data.items():
        for u in units:
            names.add(u["name"])
    return names


def _mission_unit_names(data):
    """Return dict mapping mission → set of unit names."""
    return {m: {u["name"] for u in units} for m, units in data.items()}


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
        unique_names = _all_unit_names(data)
        assert n_units == len(unique_names), (
            f"{faction_id}: n_units={n_units} but unique units in data={len(unique_names)}. "
            f"Diff: {set(range(n_units)) ^ unique_names if n_units != len(unique_names) else ''}"
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
        """No unit in any mission should have a score of 0 or NaN."""
        data, _ = build_data(faction_id, max_points=2000)
        for mission, units in data.items():
            for u in units:
                score = u["score"]
                assert score != 0, (
                    f"{faction_id}/{mission}: unit '{u['name']}' has score=0"
                )
                assert not math.isnan(score), (
                    f"{faction_id}/{mission}: unit '{u['name']}' has NaN score"
                )
                assert not math.isinf(score), (
                    f"{faction_id}/{mission}: unit '{u['name']}' has Inf score"
                )

    def test_all_missions_same_units(self, faction_id):
        """Every mission must contain the same set of unit names."""
        data, _ = build_data(faction_id, max_points=2000)
        mission_names = _mission_unit_names(data)
        if not mission_names:
            pytest.skip(f"{faction_id}: no missions with data")

        # Use the first mission as reference
        ref_mission = MISSIONS[0]
        ref_names = mission_names.get(ref_mission, set())

        for mission in MISSIONS:
            current_names = mission_names.get(mission, set())
            missing = ref_names - current_names
            extra = current_names - ref_names
            assert not missing and not extra, (
                f"{faction_id}: mission '{mission}' unit set differs from '{ref_mission}'. "
                f"Missing: {missing or 'none'}  Extra: {extra or 'none'}"
            )

    def test_no_metadata_keys_as_units(self, faction_id):
        """Metadata keys (_note, _source, etc.) must never appear as unit names."""
        data, _ = build_data(faction_id, max_points=2000)
        for mission, units in data.items():
            for u in units:
                name = u["name"]
                assert not name.startswith("_"), (
                    f"{faction_id}/{mission}: metadata key '{name}' appears as a unit"
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
        """Every faction must produce data for all 5 missions."""
        for fid in sorted(FACTIONS.keys()):
            data, _ = build_data(fid, max_points=2000)
            assert set(data.keys()) == set(MISSIONS), (
                f"{fid}: expected missions {MISSIONS}, got {list(data.keys())}"
            )
