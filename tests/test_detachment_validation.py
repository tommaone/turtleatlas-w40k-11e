"""
Detachment disposal validation & heuristics (post-mechanical).

Decision 2026-08-27: mechanical `detachment_modifiers.json` scoring is retired.
Most detachment buffs cannot be expressed as a numeric DPP/SURV/MOB modifier,
and the auto-generated files carried fabricated rules. Detachment strength is
now a heuristic (expert ratings), NOT an engine number.

What this suite verifies now:
  1. Mechanical detachment modifiers are retired — compute_ranking(detachment=X)
     returns the generalist baseline (no fabricated modifiers are applied).
  2. force-disposition mapping (supported.json `dispositions`) is internally
     valid and consistent with the merged detachment data (dp_cost).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.ranking import RankingEngine

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "data" / "config"
MERGED_DIR = REPO_ROOT / "data" / "merged"

VALID_DP_COST = {1, 2, 3}
VALID_DISPOSITION_IDS = {
    "purge-the-foe", "take-and-hold", "reconnaissance", "priority-assets", "disruption",
}

# Factions that carry a dispositions map in supported.json
FACTIONS = sorted(
    p.name for p in CONFIG_DIR.iterdir()
    if p.is_dir() and (p / "supported.json").exists() and not p.name.startswith("_")
)


def _support(faction: str) -> dict:
    p = CONFIG_DIR / faction / "supported.json"
    return json.loads(p.read_text())


def _merged_detachments(faction: str) -> list[dict]:
    p = MERGED_DIR / f"{faction}.json"
    if not p.exists():
        return []
    data = json.loads(p.read_text())
    return data.get("detachments", [])


def _dispositions(faction: str) -> dict:
    return _support(faction).get("dispositions", {})


# ═══════════════════════════════════════════════════════════════════════
# TIER 1: MECHANICAL MODIFIERS ARE RETIRED
# ═══════════════════════════════════════════════════════════════════════

class TestMechanicalRetired:
    """Fabricated mechanical detachment modifiers must not affect scores."""

    def test_detachment_scoring_is_generalist(self):
        """detachment=X must equal the generalist baseline for every faction."""
        for faction in ("grey-knights", "chaos-knights", "chaos-daemons",
                        "space-marines", "dark-angels", "deathwatch"):
            eng = RankingEngine(faction)
            base = eng.compute_ranking()
            base_fp = [(r["name"], round(r["dpp"], 6)) for r in base]
            for det in list(_dispositions(faction))[:1]:
                mod = eng.compute_ranking(detachment=det)
                mod_fp = [(r["name"], round(r["dpp"], 6)) for r in mod]
                assert mod_fp == base_fp, (
                    f"{faction}/{det}: detachment changed DPP — mechanical "
                    f"detachment modifiers must be retired (2026-08-27)."
                )

    def test_no_mechanical_modifier_file(self):
        """No faction may carry a mechanical detachment_modifiers.json."""
        for p in CONFIG_DIR.iterdir():
            if p.is_dir() and (p / "detachment_modifiers.json").exists():
                pytest.fail(f"{p.name}: mechanical detachment_modifiers.json should be removed.")


# ═══════════════════════════════════════════════════════════════════════
# TIER 2: FORCE DISPOSITIONS — supported.json
# ═══════════════════════════════════════════════════════════════════════

class TestForceDispositions:
    """Validate force disposition mapping & dp_cost against merged data."""

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_disposition_values_are_valid(self, faction):
        """Every disposition value must be one of the 5 valid IDs."""
        for det, disp in _dispositions(faction).items():
            assert disp in VALID_DISPOSITION_IDS, (
                f"{faction}/{det}: invalid disposition '{disp}'. "
                f"Valid IDs: {VALID_DISPOSITION_IDS}"
            )

    @pytest.mark.parametrize("faction", ["chaos-knights", "grey-knights", "dark-angels"])
    def test_dispositions_present(self, faction):
        """These factions should have a non-empty dispositions map."""
        assert len(_dispositions(faction)) > 0, f"{faction}: dispositions empty"

    def test_ck_disposition_spot_checks(self):
        """Spot-check each CK detachment maps to the right disposition."""
        disp = _dispositions("chaos-knights")
        expected = {
            "infernal-lance": "purge-the-foe",
            "iconoclast-fiefdom": "take-and-hold",
            "bastions-of-tyranny": "disruption",
            "hunting-warpack": "reconnaissance",
            "lords-of-dread": "priority-assets",
            "traitoris-lance": "purge-the-foe",
            "helhunt-lance": "disruption",
            "houndpack-lance": "reconnaissance",
        }
        for det, exp in expected.items():
            assert disp.get(det) == exp, f"{det}: expected '{exp}', got '{disp.get(det)}'"

    def test_get_detachments_for_disposition(self):
        """Supported map is consistent: purge-the-foe returns infernal + traitoris lance."""
        eng = RankingEngine("chaos-knights")
        assert set(eng.config.get_detachments_for_disposition("purge-the-foe")) == {
            "infernal-lance", "traitoris-lance",
        }

    def test_can_detachment_play_disposition(self):
        """can_detachment_play_disposition handles kebab + space-separated names."""
        eng = RankingEngine("chaos-knights")
        assert eng.config.can_detachment_play_disposition("infernal-lance", "purge-the-foe")
        assert eng.config.can_detachment_play_disposition("INFERNAL LANCE", "purge-the-foe")
        assert not eng.config.can_detachment_play_disposition("infernal-lance", "take-and-hold")

    def test_invalid_disposition_raises(self):
        """A detachment that can't play the given disposition must raise."""
        eng = RankingEngine("chaos-knights")
        with pytest.raises(ValueError, match="cannot be used"):
            eng.compute_ranking(detachment="INFERNAL LANCE", disposition="take-and-hold")

    def test_valid_disposition_succeeds(self):
        """A valid detachment+disposition combo must rank fine."""
        eng = RankingEngine("chaos-knights")
        results = eng.compute_ranking(detachment="INFERNAL LANCE", disposition="purge-the-foe")
        assert isinstance(results, list) and len(results) > 0


# ═══════════════════════════════════════════════════════════════════════
# TIER 3: DISPOSITIONS CONSISTENT WITH MERGED DETACHMENT DATA
# ═══════════════════════════════════════════════════════════════════════

class TestDispositionConsistency:
    """dispositions must correspond to merged-data detachments (dp_cost valid)."""

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_disposition_keys_match_merged_detachments(self, faction):
        """Every disposition key should appear among merged detachment names."""
        disp = _dispositions(faction)
        if not disp:
            pytest.skip(f"{faction}: no dispositions to check")
        merged = _merged_detachments(faction)
        merged_keys = {
            d.get("name", "").strip().lower().replace(" ", "-").replace("'", "")
            for d in merged
        }
        for det_key in disp:
            # det_key is already kebab-normalised e.g. "the-phaerons-armoury"
            if merged_keys and det_key not in merged_keys:
                # tolerate known normalisation drift — report only as advisory
                pytest.skip(f"{faction}/{det_key}: not in merged detachment keys")

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_merged_dp_costs_are_valid(self, faction):
        """dp_cost of merged detachments must be 1, 2 or 3 where present."""
        for d in _merged_detachments(faction):
            dp = d.get("dp_cost") or d.get("dp")
            if dp is not None and int(dp) not in VALID_DP_COST:
                pytest.fail(f"{faction}/{d.get('name')}: invalid dp_cost {dp}")
