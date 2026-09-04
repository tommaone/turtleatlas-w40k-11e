"""Golden loadout locks — aeldari Wraithknight.

Source of truth: tests/golden_loadouts/aeldari.json
(Wahapedia 11ed + BSData Aeldari Library, fetched 2026-08-24, high confidence).

Verdict applied (regression report line 19): the 5d21b52 single 'Primary Arm'
slot omitted the scattershield entirely; the regenerated Left Arm/Right Arm
structure matches BSData exactly (Left: heavy wraithcannon | scattershield;
Right: suncannon | heavy wraithcannon) — KEPT.

Additional datasheet truth applied here: 'Secondary Weapons' is an up-to-two
group (BSData group max=2, each option max=2 -> duplicates legal), modelled
as two slots without no_duplicates.

KNOWN LIMITATION (roadmap Known Issues #4): Scattershield grants a
CONDITIONAL 4+ invulnerable save; static info blocks cannot express
loadout-dependent INV, so info carries none rather than an unconditional
claim. Scattershield also has no weapon profile, so its branch never scores.

STRUCTURE + COUNT assertions only — damage values stay engine-derived.
"""

import json
import sys
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from engine.ranking import RankingEngine

GOLDEN = Path(__file__).resolve().parent / "golden_loadouts" / "aeldari.json"


@pytest.fixture(scope="module")
def engine():
    return RankingEngine("aeldari")


class TestWraithknight:
    """Golden: titanic feet melee; <=1 suncannon; <=2 HWC; exactly 2 secondaries."""

    def test_titanic_feet_melee(self, engine, MEQ):
        res = engine.resolve_loadout("Wraithknight", MEQ)
        assert res is not None
        _pts, _r, melee, _i, _info = res
        assert any(w.name.lower() == "titanic feet" for w in melee)

    def test_suncannon_max_one(self, engine, MEQ):
        """Right arm holds at most one suncannon."""
        res = engine.resolve_loadout("Wraithknight", MEQ)
        _pts, ranged, _m, _i, _info = res
        counts = Counter(w.name for w in ranged)
        assert counts["Suncannon"] <= 1

    def test_heavy_wraithcannon_max_two(self, engine, MEQ):
        """One per arm maximum."""
        res = engine.resolve_loadout("Wraithknight", MEQ)
        _pts, ranged, _m, _i, _info = res
        counts = Counter(w.name for w in ranged)
        assert counts["Heavy Wraithcannon"] <= 2

    def test_secondaries_exactly_two(self, engine, MEQ):
        """Up to TWO secondary weapons — max-legal modelling fills both."""
        res = engine.resolve_loadout("Wraithknight", MEQ)
        _pts, ranged, _m, _i, _info = res
        counts = Counter(w.name for w in ranged)
        sec = sum(counts[g] for g in ("Scatter Laser", "Shuriken Cannon",
                                      "Starcannon"))
        assert sec == 2, f"two secondary weapon slots filled, got {sec}"

    def test_no_scattershield_in_scored_ranged(self, engine, MEQ):
        """Scattershield has no weapon profile — its slot branch cannot score.
        Documented gap, must not appear as a fake ranged entry."""
        res = engine.resolve_loadout("Wraithknight", MEQ)
        _pts, ranged, _m, _i, _info = res
        assert all(w.name != "Scattershield" for w in ranged)


def test_golden_source_file_exists():
    data = json.loads(GOLDEN.read_text())
    for u in data["units"]:
        assert u.get("_source"), f"{u['unit']}: golden entry without source"
