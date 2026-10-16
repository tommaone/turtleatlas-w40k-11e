"""Golden dataset: tanky archetype units rank highly in Take and Hold.

These units stack defensive abilities multiplicatively (FNP + invuln + DR + high T).
The engine must rank them in the top portion of their faction for Take and Hold.

Bullgryn is the reference archetype — other units should rank similarly high.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from ranking import RankingEngine


# ═══════════════════════════════════════════════════════════════════════
# Tanky archetype definitions — verified via Wahapedia cross-check
# ═══════════════════════════════════════════════════════════════════════

TANKY_UNITS = {
    # Bullgryn: -1D + 4+ invuln + FNP6+ + T6 + SV3+
    ("astra-militarum", "Bullgryn Squad"),
    # Deathwing Knights: -1D (Inner Circle) + 4+ invuln + T5 + SV2+
    ("dark-angels", "Deathwing Knights"),
    # Deathshroud: T7 + SV2+ + 4+ invuln + FNP4+
    ("death-guard", "Deathshroud Terminators"),
    # Custodian Wardens: T6 + SV2+ + 4+ invuln + FNP4+ (Living Fortress)
    ("adeptus-custodes", "Custodian Wardens"),
}

# Tanky units must be in top 15% of their faction
MAX_RANK_PERCENTILE = 0.15

# Minimum Take and Hold mission score (engine-computed)
MIN_TOTAL_SCORE = 60.0


def _get_unit(results, name):
    """Find unit by name in results."""
    return next((r for r in results if r["name"] == name), None)


# ═══════════════════════════════════════════════════════════════════════
# Tests — each tanky unit must rank in top 25% of faction
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("faction,unit_name", sorted(TANKY_UNITS))
class TestTankyArchetypeRanking:
    """Tanky units must rank in top 25% of their faction on Take and Hold."""

    def test_in_top_15_percent(self, faction, unit_name):
        eng = RankingEngine(faction)
        results = eng.compute_ranking(mission="Take and Hold")
        unit = _get_unit(results, unit_name)
        assert unit is not None, f"{unit_name} not found in {faction}"
        rank = results.index(unit) + 1
        n = len(results)
        percentile = rank / n
        assert percentile <= MAX_RANK_PERCENTILE, (
            f"{unit_name} ranks #{rank}/{n} ({percentile:.0%}) — "
            f"expected top {MAX_RANK_PERCENTILE:.0%}"
        )

    def test_above_minimum_score(self, faction, unit_name):
        eng = RankingEngine(faction)
        results = eng.compute_ranking(mission="Take and Hold")
        unit = _get_unit(results, unit_name)
        assert unit is not None
        score = unit["_mission_score"]
        assert score >= MIN_TOTAL_SCORE, (
            f"{unit_name} score {score:.1f} < {MIN_TOTAL_SCORE} minimum"
        )

    def test_has_invuln_save(self, faction, unit_name):
        eng = RankingEngine(faction)
        results = eng.compute_ranking(mission="Take and Hold")
        unit = _get_unit(results, unit_name)
        assert unit is not None
        inv = unit["surv"].get("invuln")
        assert inv is not None, f"{unit_name} has no invuln"

    def test_has_positive_effective_wounds(self, faction, unit_name):
        eng = RankingEngine(faction)
        results = eng.compute_ranking(mission="Take and Hold")
        unit = _get_unit(results, unit_name)
        assert unit is not None
        eW = unit["surv"]["effective_wounds"]
        assert eW["ap4"] > 0, f"{unit_name} has 0 eW vs AP4"


# ═══════════════════════════════════════════════════════════════════════
# Cross-faction comparison — tanky units should outscore squishy ones
# ═══════════════════════════════════════════════════════════════════════

class TestTankyVsSquishy:
    """Tanky archetype units must outscore generic infantry on Take and Hold."""

    def test_bullgryn_outscores_tempestus_scions(self):
        """Bullgryn (T6/invuln/FNP/DR) outscores Tempestus Scions on obj hold."""
        eng = RankingEngine("astra-militarum")
        results = eng.compute_ranking(mission="Take and Hold")
        bullgryn = _get_unit(results, "Bullgryn Squad")
        scions = _get_unit(results, "Tempestus Scions")
        assert bullgryn and scions
        assert bullgryn["_mission_score"] > scions["_mission_score"]

    def test_deathshroud_outscores_poxwalkers(self):
        """Deathshroud (T7/invuln/FNP4+) outscores basic DG infantry."""
        eng = RankingEngine("death-guard")
        results = eng.compute_ranking(mission="Take and Hold")
        ds = _get_unit(results, "Deathshroud Terminators")
        pw = _get_unit(results, "Poxwalkers")
        assert ds and pw
        assert ds["_mission_score"] > pw["_mission_score"]

    def test_custodian_wardens_outscores_guardians(self):
        """Custodian Wardens (T6/invuln/FNP4+) outscores basic Custodes."""
        eng = RankingEngine("adeptus-custodes")
        results = eng.compute_ranking(mission="Take and Hold")
        cw = _get_unit(results, "Custodian Wardens")
        cg = _get_unit(results, "Custodian Guard")
        assert cw and cg
        assert cw["_mission_score"] > cg["_mission_score"]

    def test_deathwing_knights_outscores_intercessors(self):
        """Deathwing Knights (T5/invuln/DR) outscores basic Marines."""
        eng = RankingEngine("dark-angels")
        results = eng.compute_ranking(mission="Take and Hold")
        dw = _get_unit(results, "Deathwing Knights")
        inter = _get_unit(results, "Intercessor Squad")
        if dw and inter:
            assert dw["_mission_score"] > inter["_mission_score"]


# ═══════════════════════════════════════════════════════════════════════
# SURV component tests — defensive abilities must be correctly modeled
# ═══════════════════════════════════════════════════════════════════════

class TestTankySurvComponents:
    """Verify SURV sub-components for tanky units."""

    def test_bullgryn_has_fnp6(self):
        eng = RankingEngine("astra-militarum")
        results = eng.compute_ranking(mission="Take and Hold")
        bullgryn = _get_unit(results, "Bullgryn Squad")
        assert bullgryn["surv"]["fnp"] == "6+"

    def test_bullgryn_has_invuln4(self):
        eng = RankingEngine("astra-militarum")
        results = eng.compute_ranking(mission="Take and Hold")
        bullgryn = _get_unit(results, "Bullgryn Squad")
        assert bullgryn["surv"]["invuln"] == "4+"

    def test_deathshroud_has_fnp4(self):
        eng = RankingEngine("death-guard")
        results = eng.compute_ranking(mission="Take and Hold")
        ds = _get_unit(results, "Deathshroud Terminators")
        assert ds["surv"]["fnp"] == "4+"

    def test_custodian_wardens_has_fnp4(self):
        eng = RankingEngine("adeptus-custodes")
        results = eng.compute_ranking(mission="Take and Hold")
        cw = _get_unit(results, "Custodian Wardens")
        assert cw["surv"]["fnp"] == "4+"

    def test_deathwing_knights_have_invuln4(self):
        eng = RankingEngine("dark-angels")
        results = eng.compute_ranking(mission="Take and Hold")
        dw = _get_unit(results, "Deathwing Knights")
        assert dw["surv"]["invuln"] == "4+"

    def test_tanky_units_high_eW_ap4(self):
        """All tanky units have high effective wounds vs AP4+."""
        for faction, unit_name in TANKY_UNITS:
            eng = RankingEngine(faction)
            results = eng.compute_ranking(mission="Take and Hold")
            unit = _get_unit(results, unit_name)
            eW4 = unit["surv"]["effective_wounds"]["ap4"]
            assert eW4 > 10, (
                f"{unit_name} eW(ap4)={eW4} — expected >10 for tanky archetype"
            )
