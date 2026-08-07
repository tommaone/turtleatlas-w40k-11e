"""Shared utilities for the cross-faction verification suite.

The suite is split into two tiers, per the dojo rule that a number without
its target mix is a trap:

  STRICT  — invariants of the engine itself. These can never legitimately
            fail for a correct engine, so they are hard asserts (CI must
            go red). Cheap, fast, every faction.
  TRUTH   — domain expectations auto-derived from weapon stats, but the
            derivation is *interpretation*, not engine output. Failures are
            collected into a report and surfaced as xfails, never blocking.

Every number below comes from the engine (RankingEngine.compute_ranking /
resolve_loadout / _ld_dmg / en.W) — never recomputed by hand. This file only
orchestrates calls; it does not contain damage math.
"""
import sys
from pathlib import Path

# Project root on path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.gen_findings_html import FACTIONS  # canonical 30-faction list

ALL_FACTIONS = sorted(FACTIONS.keys())

# The seven canonical target profiles the engine evaluates against.
TARGETS = ["GEQ", "MEQ", "TEQ", "Light V", "Heavy V", "C'tan", "Knight"]

# Meta presets exposed by _base config (each faction inherits these)
METAS = ["all-comers", "competitive", "infantry", "vehicle", "elite"]


def load_engine(faction: str):
    """Build a RankingEngine for a faction, importing lazily (fast)."""
    from engine.ranking import RankingEngine
    return RankingEngine(faction)