"""Guard: BSData constraint-based weapon count + engine expansion.

Covers three layers:
1. Merged data: adapter extracts BSData constraints (count=2 on entries)
2. Engine expansion: fixed entries, slot choices, duplicate detection
3. Loadout display: _loadout_desc shows correct Nx prefix

BSData encodes dual-mounted weapons via constraints on entryLinks/SEs:
  min=2, max=2, field="selections", scope="parent"

Config may also encode multiplicity via:
- fixed[].count (e.g. "2 Soulshatter lascannon")
- slot.choices[].count (e.g. "2 Heavy Bolter" on sponsons)
- duplicate fixed entries (e.g. 2x Hurricane Bolter entries)

The engine must NOT double-count when both merged data AND config encode
the same multiplicity.

Run: python3 -m pytest tests/test_weapon_count_constraints.py -v
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from engine.ranking import RankingEngine

# ── Fixtures ────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def meq():
    from tests.conftest import _target_from_cfg
    return _target_from_cfg("MEQ")


def _loadout(slug, name, meq):
    """Resolve a loadout and return the loadout description string."""
    eng = RankingEngine(slug)
    res = eng.resolve_loadout(name, meq)
    assert res is not None, f"{name} not found in {slug}"
    pts, ranged, melee, innate, info = res
    return RankingEngine._loadout_desc(ranged, melee, innate), ranged, melee


def _weapon_counts(slug, name, meq):
    """Return {weapon_name: count} from the resolved loadout."""
    _, ranged, melee = _loadout(slug, name, meq)
    counts = {}
    for w in ranged:
        counts[w.name] = counts.get(w.name, 0) + w.count
    for w in melee:
        counts[w.name] = counts.get(w.name, 0) + w.count
    return counts


# ── SM Land Raiders (BSData constraint → merged count=2, no config count) ──

class TestSMLandRaider:
    """Godhammer Lascannon: BSData constraint count=2, config fixed entry has no count."""

    def test_loadout_shows_2x(self, meq):
        ld, _, _ = _loadout("space-marines", "Land Raider", meq)
        assert "2×Godhammer Lascannon" in ld

    def test_weapon_count_2(self, meq):
        wc = _weapon_counts("space-marines", "Land Raider", meq)
        assert wc.get("Godhammer Lascannon") == 2


class TestSMLandRaiderCrusader:
    """Hurricane Bolter: BSData constraint count=2."""

    def test_loadout_shows_2x(self, meq):
        ld, _, _ = _loadout("space-marines", "Land Raider Crusader", meq)
        assert "2×Hurricane Bolter" in ld

    def test_weapon_count_2(self, meq):
        wc = _weapon_counts("space-marines", "Land Raider Crusader", meq)
        assert wc.get("Hurricane Bolter") == 2


class TestSMLandRaiderRedeemer:
    """Flamestorm Cannon: BSData constraint count=2."""

    def test_loadout_shows_2x(self, meq):
        ld, _, _ = _loadout("space-marines", "Land Raider Redeemer", meq)
        assert "2×Flamestorm Cannon" in ld

    def test_weapon_count_2(self, meq):
        wc = _weapon_counts("space-marines", "Land Raider Redeemer", meq)
        assert wc.get("Flamestorm Cannon") == 2


# ── SM Predator Annihilator (slot choice count=2 + merged count=2) ──────

class TestSMPredatorAnnihilator:
    """Sponson weapons: config slot choice count=2, merged data count=2.
    Engine must NOT double-count (4× → correct 2×)."""

    def test_loadout_shows_2x_heavy_bolter(self, meq):
        ld, _, _ = _loadout("space-marines", "Predator Annihilator", meq)
        assert "2×Heavy Bolter" in ld

    def test_twin_lascannon_count_1(self, meq):
        """Twin-linked turret: count=1 (not 2)."""
        wc = _weapon_counts("space-marines", "Predator Annihilator", meq)
        assert wc.get("Predator Twin Lascannon") == 1

    def test_sponson_heavy_bolter_count_2(self, meq):
        wc = _weapon_counts("space-marines", "Predator Annihilator", meq)
        assert wc.get("Heavy Bolter") == 2


# ── SM Stormraven (duplicate fixed entries + merged count=2) ────────────

class TestSMStormraven:
    """Hurricane Bolter + Stormstrike: config lists 2 duplicate fixed entries,
    merged data has count=2. Engine must use duplicate detection to avoid 4×."""

    def test_loadout_shows_2x_hurricane(self, meq):
        ld, _, _ = _loadout("space-marines", "Stormraven Gunship", meq)
        assert "2×Hurricane Bolter" in ld

    def test_loadout_shows_2x_stormstrike(self, meq):
        ld, _, _ = _loadout("space-marines", "Stormraven Gunship", meq)
        assert "2×Stormstrike" in ld

    def test_hurricane_count_2(self, meq):
        wc = _weapon_counts("space-marines", "Stormraven Gunship", meq)
        assert wc.get("Hurricane Bolter") == 2

    def test_stormstrike_count_2(self, meq):
        wc = _weapon_counts("space-marines", "Stormraven Gunship", meq)
        # Name may vary — check prefix
        stormstrike = sum(v for k, v in wc.items() if "Stormstrike" in k)
        assert stormstrike == 2


# ── CSM Chaos Land Raider (fixed count=2 + merged count=2) ─────────────

class TestCSMChaosLandRaider:
    """Soulshatter lascannon: config fixed count=2, merged data count=2.
    Engine must NOT double-count (4× → correct 2×)."""

    def test_loadout_shows_2x(self, meq):
        ld, _, _ = _loadout("chaos-space-marines", "Chaos Land Raider", meq)
        assert "2×Soulshatter lascannon" in ld

    def test_weapon_count_2(self, meq):
        wc = _weapon_counts("chaos-space-marines", "Chaos Land Raider", meq)
        assert wc.get("Soulshatter lascannon") == 2


# ── CSM Venomcrawler (fixed count=2 + merged count=2) ──────────────────

class TestCSMVenomcrawler:
    """Excruciator cannon: config fixed count=2, merged data count=2."""

    def test_loadout_shows_2x(self, meq):
        ld, _, _ = _loadout("chaos-space-marines", "Venomcrawler", meq)
        assert "2×Excruciator cannon" in ld

    def test_weapon_count_2(self, meq):
        wc = _weapon_counts("chaos-space-marines", "Venomcrawler", meq)
        assert wc.get("Excruciator cannon") == 2


# ── CSM Defiler (slot choice count=2 + merged count=2) ─────────────────

class TestCSMDefiler:
    """Excruciator cannon slot choice count=2, merged data count=2."""

    def test_loadout_shows_2x(self, meq):
        ld, _, _ = _loadout("chaos-space-marines", "Defiler", meq)
        assert "2×Excruciator cannon" in ld

    def test_weapon_count_2(self, meq):
        wc = _weapon_counts("chaos-space-marines", "Defiler", meq)
        assert wc.get("Excruciator cannon") == 2


# ── Aeldari (slot choice count=2 + merged count=2) ─────────────────────

class TestAeldariCrimsonHunter:
    """Starcannon: slot choice count=2, merged data count=2."""

    def test_loadout_shows_2x(self, meq):
        ld, _, _ = _loadout("aeldari", "Crimson Hunter", meq)
        assert "2×Starcannon" in ld

    def test_weapon_count_2(self, meq):
        wc = _weapon_counts("aeldari", "Crimson Hunter", meq)
        assert wc.get("Starcannon") == 2


class TestAeldariStarweaver:
    """Shuriken Cannon: BSData constraint count=2."""

    def test_loadout_shows_2x(self, meq):
        ld, _, _ = _loadout("aeldari", "Starweaver", meq)
        assert "2×Shuriken Cannon" in ld

    def test_weapon_count_2(self, meq):
        wc = _weapon_counts("aeldari", "Starweaver", meq)
        assert wc.get("Shuriken Cannon") == 2


# ── Orks (slot choice count=3 + merged count) ──────────────────────────

class TestOrksDeffDread:
    """Skorcha: slot choice count=3."""

    def test_loadout_shows_3x(self, meq):
        ld, _, _ = _loadout("orks", "Deff Dread", meq)
        assert "3×Skorcha" in ld

    def test_weapon_count_3(self, meq):
        wc = _weapon_counts("orks", "Deff Dread", meq)
        assert wc.get("Skorcha") == 3


# ── Necrons (merged count=2, no config count) ──────────────────────────

class TestNecronsDoomsdayArk:
    """Gauss flayer array: BSData constraint count=2."""

    def test_loadout_shows_2x(self, meq):
        ld, _, _ = _loadout("necrons", "Doomsday Ark", meq)
        assert "2×Gauss flayer array" in ld

    def test_weapon_count_2(self, meq):
        wc = _weapon_counts("necrons", "Doomsday Ark", meq)
        assert wc.get("Gauss flayer array") == 2


class TestNecronsGhostArk:
    """Gauss flayer array: BSData constraint count=2."""

    def test_loadout_shows_2x(self, meq):
        ld, _, _ = _loadout("necrons", "Ghost Ark", meq)
        assert "2×Gauss flayer array" in ld

    def test_weapon_count_2(self, meq):
        wc = _weapon_counts("necrons", "Ghost Ark", meq)
        assert wc.get("Gauss flayer array") == 2


# ── Chaos Knights (merged count=2) ─────────────────────────────────────

class TestChaosKnightsDespoiler:
    """Twin meltagun: BSData constraint count=2."""

    def test_no_4x_weapons(self, meq):
        """No weapon should show 4× or higher — that signals double-counting."""
        ld, _, _ = _loadout("chaos-knights", "Knight Despoiler", meq)
        import re
        for m in re.finditer(r'(\d+)×', ld):
            num = int(m.group(1))
            assert num <= 3, f"Unexpected count {num} in loadout: {ld}"
