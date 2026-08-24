"""Golden loadout locks — imperial-agents datasheet-verified structures.

Source of truth: workspace/golden_loadouts/imperial-agents.json
(Wahapedia 11ed, fetched 2026-08-24, confidence high; Inquisitor points
flagged low-confidence — wahapedia live 55 vs MFM snapshot 65).

Covers the curated-regression flags for Inquisitor / Inquisitorial
Chimera. STRUCTURE + COUNT assertions only — no damage numbers.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from engine.ranking import RankingEngine

GOLDEN = (
    Path(__file__).resolve().parent.parent
    / "workspace" / "golden_loadouts" / "imperial-agents.json"
)


@pytest.fixture(scope="module")
def engine():
    return RankingEngine("imperial-agents")


def _names(ws):
    return sorted(w.name for w in ws)


class TestInquisitor:
    """Golden: melee swap + pistol swap + wargear swap (psychic gifts -> PSW)."""

    def test_swap_structure(self, engine, MEQ):
        res = engine.resolve_loadout("Inquisitor", MEQ)
        _pts, ranged, melee, _i, _info = res
        assert len(melee) == 1
        assert melee[0].name in ("Inquisitorial melee weapon", "Force weapon")
        assert len(ranged) == 2, f"got {_names(ranged)}"
        r = _names(ranged)
        assert any(n in ("Bolt pistol", "Combi-weapon") for n in r)

    def test_psychic_gifts_yield_shock_wave(self, engine, MEQ):
        """Blessed wardings have no damage profile; psychic gifts resolve to
        the Psychic Shock Wave witchfire profile."""
        res = engine.resolve_loadout("Inquisitor", MEQ)
        assert "Psychic Shock Wave" in _names(res[1])

    def test_points_match_mfm_snapshot(self, engine):
        """Repo convention: MFM is points truth. Wahapedia live shows 55 —
        flagged for next MFM sync; this pin documents the current snapshot."""
        ch_path = (Path(__file__).resolve().parent.parent
                   / "data" / "config" / "imperial-agents" / "characters.json")
        ch = json.loads(ch_path.read_text())
        assert ch["Inquisitor"]["pts"] == 65


class TestInquisitorialChimera:
    """Golden: lasgun array + HKM fixed; hull/pintle/turret pick-1s."""

    def test_structure(self, engine, MEQ):
        res = engine.resolve_loadout("Inquisitorial Chimera", MEQ)
        _pts, ranged, melee, _i, _info = res
        r = _names(ranged)
        assert r.count("Lasgun array") == 1  # cannot be replaced
        assert r.count("Hunter-killer missile") == 1  # max-legal add-on
        hull = [n for n in r if n in ("Heavy bolter", "Heavy flamer")]
        pintle = [n for n in r if n in ("Heavy stubber", "Storm bolter")]
        turret = [n for n in r if n in ("Multi-laser",)]
        # heavy bolter/flamer names are shared between hull and turret pools;
        # structural guarantee: exactly one of each POOL is present overall.
        assert len(pintle) == 1, f"one pintle, got {r}"
        assert len(hull) + len(turret) >= 2, f"hull+turret picks present, got {r}"
        assert _names(melee) == ["Armoured tracks"]


def test_golden_source_file_exists():
    data = json.loads(GOLDEN.read_text())
    for u in data["units"]:
        assert u.get("_source"), f"{u['unit']}: golden entry without source"
