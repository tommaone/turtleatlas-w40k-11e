"""Guard: BSData constraint-based weapon count extraction.

BSData encodes dual-mounted weapons via constraints on entryLinks/SEs:
  min=2, max=2, field="selections", scope="parent"
(e.g. Land Raider Godhammer Lascannon, LR Crusader Hurricane Bolter).

The adapter's _count_from_constraints() extracts these; dedup merges
identical entries found through multiple traversal paths; merge.py's
_weapon_matches() uses exact matching to avoid "Lascannon" matching
"Predator Twin Lascannon".

These tests pin the merged output for vehicles that exercise this path.

Run: python3 -m pytest tests/test_weapon_count_constraints.py -v
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

MERGED_SM = Path(__file__).resolve().parent.parent / "data" / "merged" / "space-marines.json"


@pytest.fixture(scope="module")
def sm_units():
    data = json.load(open(MERGED_SM))
    return {u["name"]: u for u in data["units"]}


def _weapon_count(unit: dict, weapon_name: str) -> int | None:
    """Return count for a weapon in a unit's profile, or None if not found."""
    for w in unit.get("profile", {}).get("weapons", []):
        if w["name"] == weapon_name:
            return w.get("count", 1)
    return None


class TestLandRaider:
    """Godhammer Lascannon is dual-mounted (count=2) via BSData constraint."""

    def test_godhammer_lascannon_count_2(self, sm_units):
        u = sm_units.get("Land Raider")
        assert u is not None, "Land Raider not found in merged SM"
        assert _weapon_count(u, "Godhammer Lascannon") == 2

    def test_godhammer_lascannon_single_entry(self, sm_units):
        """Dedup should produce exactly one Lascannon entry, not two."""
        u = sm_units.get("Land Raider")
        assert u is not None
        names = [w["name"] for w in u["profile"]["weapons"]]
        assert names.count("Godhammer Lascannon") == 1, (
            f"Expected 1 Godhammer Lascannon entry, got {names.count('Godhammer Lascannon')}"
        )


class TestLandRaiderCrusader:
    """Hurricane Bolter is dual-mounted (count=2) via BSData constraint."""

    def test_hurricane_bolter_count_2(self, sm_units):
        u = sm_units.get("Land Raider Crusader")
        assert u is not None, "Land Raider Crusader not found"
        assert _weapon_count(u, "Hurricane Bolter") == 2


class TestLandRaiderRedeemer:
    """Flamestorm Cannon is dual-mounted (count=2) via BSData constraint."""

    def test_flamestorm_cannon_count_2(self, sm_units):
        u = sm_units.get("Land Raider Redeemer")
        assert u is not None, "Land Raider Redeemer not found"
        assert _weapon_count(u, "Flamestorm Cannon") == 2


class TestPredatorAnnihilator:
    """Sponson Lascannon count=2, turret Predator Twin Lascannon count=1."""

    def test_twin_lascannon_count_1(self, sm_units):
        """Twin-linked turret weapon is ONE weapon with Twin-linked keyword, not 2."""
        u = sm_units.get("Predator Annihilator")
        assert u is not None
        assert _weapon_count(u, "Predator Twin Lascannon") == 1

    def test_sponson_lascannon_count_2(self, sm_units):
        u = sm_units.get("Predator Annihilator")
        assert u is not None
        assert _weapon_count(u, "Lascannon") == 2

    def test_sponson_heavy_bolter_count_2(self, sm_units):
        u = sm_units.get("Predator Annihilator")
        assert u is not None
        assert _weapon_count(u, "Heavy Bolter") == 2

    def test_no_duplicate_lascannon_entries(self, sm_units):
        u = sm_units.get("Predator Annihilator")
        assert u is not None
        names = [w["name"] for w in u["profile"]["weapons"]]
        assert names.count("Lascannon") == 1, (
            f"Expected 1 Lascannon entry (dedup), got {names.count('Lascannon')}"
        )


class TestStormraven:
    """Hurricane Bolter + Stormstrike Missiles dual-mounted."""

    def test_hurricane_bolter_count_2(self, sm_units):
        u = sm_units.get("Stormraven Gunship")
        assert u is not None
        assert _weapon_count(u, "Hurricane Bolter") == 2

    def test_stormstrike_missiles_count_2(self, sm_units):
        u = sm_units.get("Stormraven Gunship")
        assert u is not None
        assert _weapon_count(u, "Stormstrike Missiles") == 2
