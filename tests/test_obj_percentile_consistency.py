"""OBJ percentile must be a valid percentile (0-100) in every ranking mode.

Regression guard for the mission-branch inconsistency where the OBJ percentile
*series* capped `wounds_per_model` at 3 but each unit's own OBJ *value* used the
raw wpm — so a high-W unit was scored on its full wound count while the
distribution it was percentiled against capped everyone at 3. That produced
impossible percentiles > 100 (e.g. 102) for high-W units and reordered the
mission rankings.

The invariant is structural, not a magic number: a percentile cannot leave
[0, 100].
"""
import pytest

from engine.ranking import RankingEngine

FACTIONS = ("grey-knights", "chaos-knights", "space-marines")
MISSIONS = (
    "Take and Hold",
    "Purge the Foe",
    "Reconnaissance",
    "Priority Assets",
    "Disruption",
)


@pytest.mark.parametrize("fid", FACTIONS)
def test_obj_percentile_in_bounds_per_mission(fid):
    e = RankingEngine(fid)
    for mission in MISSIONS:
        for u in e.compute_ranking(mission=mission):
            assert 0.0 <= u["_obj_pct"] <= 100.0, (
                f"{fid} / {mission} / {u['name']}: "
                f"_obj_pct={u['_obj_pct']} outside [0, 100]"
            )


@pytest.mark.parametrize("fid", FACTIONS)
def test_obj_percentile_in_bounds_no_mission(fid):
    e = RankingEngine(fid)
    for u in e.compute_ranking():
        assert 0.0 <= u["_obj_pct"] <= 100.0, (
            f"{fid} / no-mission / {u['name']}: "
            f"_obj_pct={u['_obj_pct']} outside [0, 100]"
        )
