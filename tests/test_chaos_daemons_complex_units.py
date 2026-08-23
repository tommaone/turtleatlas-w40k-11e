"""Regression locks for the Chaos Daemons squad composition migration.

Locks the regenerated chaos-daemons squads to the BSData truth (verified
2026-08-23 via gen_squad_composition --faction chaos-daemons against the
"Chaos - Chaos Daemons" composition):

Regenerated squads (15, flat -> named-model builds):
- Leader/champion variants now carry distinct model entries:
  Bloodletters (9 Bloodletters + 1 Bloodreaper), Bloodcrushers
  (2 Bloodcrushers + 1 Bloodhunter), Daemonettes/Plaguebearers/Horrors
  (Iconbearer + Piper variants), etc.
- Single-model chariots kept flat (no BSData composition):
  Burning Chariot of Tzeentch, Skull Cannon.

STRUCTURE ONLY — no damage values. The engine is the single source of
computation; this test locks the config shape and resolvability, not math.

Run: python3 -m pytest tests/test_chaos_daemons_complex_units.py -v
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.ranking import RankingEngine

CONFIG_DIR = Path(__file__).resolve().parent.parent / "data" / "config"
SQUADS_PATH = CONFIG_DIR / "chaos-daemons" / "squads.json"

REGENERATED = [
    "Beasts Of Nurgle", "Bloodcrushers", "Bloodletters", "Blue Horrors",
    "Daemonettes", "Fiends", "Flamers", "Flesh Hounds", "Hellflayers",
    "Nurglings", "Pink Horrors", "Plague Drones", "Plaguebearers",
    "Screamers", "Seekers",
]

KEPT_FLAT = ["Burning Chariot", "Skull Cannon"]


@pytest.fixture(scope="module")
def cd_engine():
    return RankingEngine("chaos-daemons")


@pytest.fixture(scope="module")
def squads():
    return json.load(open(SQUADS_PATH))


class TestMigrationShape:
    def test_regenerated_units_have_named_models(self, squads):
        for unit in REGENERATED:
            builds = squads[unit]["builds"]
            assert builds, f"{unit}: no builds"
            for b in builds:
                for m in b["models"]:
                    assert "name" in m, f"{unit}: unnamed model in build {b.get('name')}"

    def test_kept_units_stay_flat(self, squads):
        """Single-model chariots have no composition — must keep curated builds."""
        for unit in KEPT_FLAT:
            builds = squads[unit]["builds"]
            assert builds, f"{unit}: no builds"
            for m in builds[0]["models"]:
                assert "name" not in m, (
                    f"{unit}: should stay flat (no BSData composition)"
                )

    def test_leader_variant_distinct_from_base(self, squads):
        """Bloodreaper is a separate model entry, not merged into the pool."""
        models = squads["Bloodletters"]["builds"][0]["models"]
        names = [m["name"] for m in models]
        assert "Bloodletter" in names and "Bloodreaper" in names

    def test_bloodhunter_distinct_from_base(self, squads):
        models = squads["Bloodcrushers"]["builds"][0]["models"]
        names = [m["name"] for m in models]
        assert "Bloodcrusher" in names and "Bloodhunter" in names

    def test_all_units_have_points(self, squads):
        for name, u in squads.items():
            if name.startswith("_"):
                continue
            assert isinstance(u.get("pts"), int), f"{name}: missing pts"


class TestResolvability:
    """Every weapon reference resolves in the catalog — structure, not math."""

    def _resolve(self, engine, squads):
        bad = []
        for name, u in squads.items():
            if name.startswith("_"):
                continue
            for b in u.get("builds", []):
                for m in b.get("models", []):
                    w = m.get("ranged")
                    refs = w if isinstance(w, list) else ([w] if w else [])
                    ml = m.get("melee")
                    refs += ml if isinstance(ml, list) else ([ml] if ml else [])
                    for ref in refs:
                        for cat in ("ranged", "melee"):
                            try:
                                engine.W(ref, unit_name=name, category=cat)
                                break
                            except KeyError:
                                continue
                        else:
                            bad.append((name, ref))
        return bad

    def test_all_weapon_refs_resolve(self, cd_engine, squads):
        bad = self._resolve(cd_engine, squads)
        assert not bad, f"unresolvable weapon refs: {bad}"
