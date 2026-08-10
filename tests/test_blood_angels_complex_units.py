"""End-to-end tests for the complex blood-angels squad-composition units.

Runs the full pipeline (BSData parser -> config generator -> engine alloc
resolution) through the real regenerated config
(data/config/blood-angels/squads.json) and pins the deterministic resolved
loadouts for the BA-specific complex units covered in this iteration.

This iteration migrated blood-angels squads to the complex layer:
- Sanguinary Guard per-model weapon slots (Encarmine Blade/Spear + Inferno
  Pistol/Angelus Boltgun)
- Death Company alloc pools (Eviscerator cap, alternate-weapons slots,
  Jump Pack variants)
- parallel-variant alloc for shared SM squads (Intercessor grenade
  launcher, Devastator heavy weapons, Terminator heavy weapon, Sternguard
  special weapon)
- Outrider alloc pool with the Invader ATV slot-choice variant (the ATV
  itself has no top-level composition entry — kept curated)

Shared SM squads (Intercessor/Terminator/Devastator etc.) ride the same
payloads already pinned in test_space_marines_complex_units.py — here we
pin the BA-specific units plus the BA-catalogue variants.

Per turtle-dojo, STRUCTURE is asserted (alloc distribution, weapon names and
counts, melee reduction), NOT damage numbers — no expected_wounds.

Run: python3 -m pytest tests/test_blood_angels_complex_units.py -v
"""

from collections import Counter
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.ranking import RankingEngine


@pytest.fixture(scope="module")
def ba_engine():
    return RankingEngine("blood-angels")


def _build(engine, name, target):
    res = engine._best_squad_variant(name, target)
    assert res is not None, f"{name} did not resolve"
    return res


def _rcount(res, name):
    return Counter(w.name for w in res["ranged"])[name]


def _mcount(res, name):
    return Counter(w.name for w in res["melee"])[name]


def _alloc(res):
    """Count dict for the first alloc pool of a resolved squad."""
    return dict(res["_alloc_info"][0][1])


class TestBloodAngelsComplexUnits:
    """Real-config regression pins: exact resolved loadout per complex unit."""

    def test_sanguinary_guard_slots_meq(self, ba_engine, MEQ):
        """Sanguinary Guard n=3: one model entry with per-model slots, no
        alloc pool. vs MEQ the ranged slot takes Inferno Pistol (melta
        profile beats Angelus Boltgun on 3+ saves) and the melee slot keeps
        the Encarmine Blade default."""
        res = _build(ba_engine, "Sanguinary Guard", MEQ)
        assert res.get("_alloc_info") is None
        assert _rcount(res, "Inferno Pistol") == 3
        assert _rcount(res, "Angelus Boltgun") == 0
        assert _mcount(res, "Encarmine Blade") == 3
        assert len(res["ranged"]) == 3
        assert len(res["melee"]) == 3

    def test_sanguinary_guard_slots_geq(self, ba_engine, GEQ):
        """vs GEQ the ranged slot flips to Angelus Boltgun (torrent
        anti-horde beats melta overkill on 1W models); melee unchanged."""
        res = _build(ba_engine, "Sanguinary Guard", GEQ)
        assert _rcount(res, "Angelus Boltgun") == 3
        assert _rcount(res, "Inferno Pistol") == 0
        assert _mcount(res, "Encarmine Blade") == 3

    def test_death_company_marines_alloc(self, ba_engine, MEQ):
        """Death Company Marines n=5: alloc fills the Eviscerator cap (1),
        2 base marines (Heavy Bolt Pistol + Astartes Chainsword), 2
        alternate-weapons marines (Inferno Pistol + Power fist vs MEQ)."""
        res = _build(ba_engine, "Death Company Marines", MEQ)
        assert _alloc(res) == {
            "Death Company Marine w/Eviscerator": 1,
            "Death Company Marine": 2,
            "Death Company Marine w/ alternate weapons": 2,
        }
        assert _rcount(res, "Heavy Bolt Pistol") == 2
        assert _rcount(res, "Inferno Pistol") == 2
        assert _mcount(res, "Eviscerator") == 1
        assert _mcount(res, "Astartes Chainsword") == 2
        assert _mcount(res, "Power fist") == 2
        assert len(res["melee"]) == 5

    def test_death_company_marines_jump_packs_alloc(self, ba_engine, MEQ, GEQ):
        """Death Company Marines With Jump Packs n=5: the alternate-weapons
        variant (max 7) takes the whole squad budget vs both MEQ and GEQ.
        Slot picks are target-dependent: Inferno Pistol + Power fist vs MEQ,
        Hand flamer + Power weapon vs GEQ."""
        res = _build(ba_engine, "Death Company Marines With Jump Packs", MEQ)
        assert _alloc(res) == {"Death Company Marine w/ alternate weapons": 5}
        assert _rcount(res, "Inferno Pistol") == 5
        assert _mcount(res, "Power fist") == 5

        res_geq = _build(ba_engine, "Death Company Marines With Jump Packs", GEQ)
        assert _alloc(res_geq) == {"Death Company Marine w/ alternate weapons": 5}
        assert _rcount(res_geq, "Hand flamer") == 5
        assert _mcount(res_geq, "Power weapon") == 5

    def test_death_company_intercessors_alloc(self, ba_engine, MEQ):
        """Death Company Intercessors n=5: 3 base Death Company Intercessors
        (slot flips to Astartes Chainsword & Heavy Bolt Pistol vs MEQ),
        1 melee-weapon Intercessor (Power fist), 1 alternate-pistol
        Intercessor (Plasma pistol — scores its supercharge profile)."""
        res = _build(ba_engine, "Death Company Intercessors", MEQ)
        assert _alloc(res) == {
            "Death Company Intercessor": 3,
            "Intercessor w/ melee weapon": 1,
            "Intercessor w/ alternate pistol": 1,
        }
        assert _rcount(res, "Heavy Bolt Pistol") == 4
        assert _rcount(res, "Plasma pistol - standard") == 1
        assert _mcount(res, "Astartes Chainsword") == 4
        assert _mcount(res, "Power fist") == 1
        assert len(res["melee"]) == 5

    def test_death_company_marines_bolt_rifles_alloc(self, ba_engine, MEQ):
        """Death Company Marines With Bolt Rifles n=5: 2 Bolt Rifle marines,
        1 Eviscerator (cap), 2 alternate-weapons marines (Inferno Pistol +
        Power Fist vs MEQ)."""
        res = _build(ba_engine, "Death Company Marines With Bolt Rifles", MEQ)
        assert _alloc(res) == {
            "Death Company Marine w/Bolt Rifle": 2,
            "Death Company Marine w/Eviscerator": 1,
            "Death Company Marine w/ alternate weapons": 2,
        }
        assert _rcount(res, "Bolt Rifle") == 2
        assert _rcount(res, "Inferno Pistol") == 2
        assert _mcount(res, "Eviscerator") == 1
        assert _mcount(res, "Power Fist") == 2
        assert len(res["melee"]) == 5

    def test_vanguard_veterans_alloc(self, ba_engine, MEQ):
        """Vanguard Veteran Squad With Jump Packs n=5: 3 base Vanguard
        Veterans + 1 Plasma Pistol & Master-crafted Power Weapon in the alloc
        pool (count 4), plus 1 sergeant with slots (Inferno Pistol +
        Master-crafted Power Weapon vs MEQ)."""
        res = _build(ba_engine, "Vanguard Veteran Squad With Jump Packs", MEQ)
        assert _alloc(res) == {
            "Vanguard Veterans with Jump Packs": 3,
            "Vanguard Veteran w/Plasma Pistol & Master-crafter Power Weapon": 1,
        }
        assert _rcount(res, "Inferno Pistol") == 4
        assert _rcount(res, "Plasma pistol - standard") == 1
        assert _mcount(res, "Vanguard Veteran Weapon") == 3
        assert _mcount(res, "Master-crafted Power Weapon") == 2
        assert len(res["melee"]) == 5

    def test_terminator_squad_alloc(self, ba_engine, MEQ):
        """Terminator Squad n=5: 3 Power Fist terminators + 1 Heavy Weapon
        terminator (Assault Cannon vs MEQ) in the pool, plus 1 sergeant
        (Power fist slot). Storm bolters on the 4 non-special bodies."""
        res = _build(ba_engine, "Terminator Squad", MEQ)
        assert _alloc(res) == {
            "Terminator w/ Power Fist": 3,
            "Terminator w/ Heavy Weapon": 1,
        }
        assert _rcount(res, "Storm bolter") == 4
        assert _rcount(res, "Assault Cannon") == 1
        assert _mcount(res, "Power fist") == 5
        assert len(res["melee"]) == 5

    def test_devastator_squad_alloc(self, ba_engine, MEQ):
        """Devastator Squad n=5: the heavy-weapon variant (max 4) takes the
        whole 4-model budget vs MEQ and its slot picks Plasma cannon (the
        supercharge choice profile beats Multi-melta vs 2W MEQ); the
        sergeant keeps Close combat weapon."""
        res = _build(ba_engine, "Devastator Squad", MEQ)
        assert _alloc(res) == {"Devastator Marine w/ Heavy Weapon": 4}
        assert _rcount(res, "Plasma cannon - standard") == 4
        assert _mcount(res, "Close combat weapon") == 5
        assert len(res["melee"]) == 5

    def test_stern_guard_alloc(self, ba_engine, MEQ):
        """Sternguard Veteran Squad n=5: 3 Bolt Rifle veterans + 1 Special
        Weapon veteran (Sternguard Heavy Bolter vs MEQ), plus 1 sergeant
        (Power fist slot)."""
        res = _build(ba_engine, "Sternguard Veteran Squad", MEQ)
        assert _alloc(res) == {
            "Sternguard Veteran w/ Bolt Rifle": 3,
            "Sternguard Veteran w/ Special Weapon": 1,
        }
        assert _rcount(res, "Sternguard Bolt Rifle") == 4
        assert _rcount(res, "Sternguard Heavy Bolter") == 1
        assert _mcount(res, "Close combat weapon") == 4
        assert _mcount(res, "Power fist") == 1

    def test_shared_sm_squad_rides_ba_payload(self, ba_engine, MEQ):
        """A shared SM squad (Intercessor) resolves through the BA config the
        same way it does in SM/DA — grenade launcher not worth vs MEQ,
        Sergeant takes Plasma pistol + Power fist."""
        res = _build(ba_engine, "Intercessor Squad", MEQ)
        assert _alloc(res) == {"Intercessor": 4}
        assert _rcount(res, "Bolt Rifle") == 4
        assert _rcount(res, "Plasma pistol - standard") == 1
        assert _mcount(res, "Power fist") == 1

    def test_invader_atv_kept_curated(self):
        """Invader ATV has no top-level BSData composition entry (it is an
        Outrider slot-choice variant) — it is KEPT with its curated discrete
        builds, not rewritten to Default+alloc."""
        import json
        cfg = json.loads(
            (Path(__file__).resolve().parent.parent
             / "data/config/blood-angels/squads.json").read_text(encoding="utf-8")
        )
        builds = cfg["Invader Atv"]["builds"]
        assert builds[0]["name"] == "Melee"
        assert any(b["name"] == "Multi-melta" for b in builds)
        assert not any("alloc" in m for b in builds for m in b["models"])

    def test_no_legends_in_config(self):
        """No [Legends] entries pollute the BA config — every key matches a
        current-edition catalogue entry."""
        import json
        cfg = json.loads(
            (Path(__file__).resolve().parent.parent
             / "data/config/blood-angels/squads.json").read_text(encoding="utf-8")
        )
        assert not any("Legends" in k for k in cfg)
