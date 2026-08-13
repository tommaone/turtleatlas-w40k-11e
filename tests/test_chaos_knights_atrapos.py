"""Regression lock for the Chaos Cerastus Knight Atrapos dual-profile fix.

Atrapos had the same choice-profile bug as the Knight Tyrant: the config
fixed BOTH '- low intensity' AND '- high intensity' as separate ranged
entries, so ranged damage SUMMED the two profiles instead of maxing over
the group. The fix:

- Config references the GROUP entry ('Atrapos lascutter',
  'Graviton singularity cannon'), never both '- profile' names.
- Engine: _resolve_slots_build passes the declared type as `category` to
  the weapon loader, so DUAL-profile weapons (Singing Spear, Chainsabres,
  Atrapos lascutter) resolve the matching profile per list. Without it the
  first profile wins — the melee list could receive the RANGED profile
  (proven regression: Farseer melee Singing Spear was A1 S9, now A2 S3).

STRUCTURE AND PROFILE SELECTION ONLY — no damage values. The engine is
the single source of computation; these tests lock profile category
selection and group-name resolution, not math.

Run: python3 -m pytest tests/test_chaos_knights_atrapos.py -v
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.ranking import RankingEngine

CONFIG_DIR = Path(__file__).resolve().parent.parent / "data" / "config"
CHAOS_KNIGHTS = CONFIG_DIR / "chaos-knights" / "characters.json"

ATRAPOS = "Chaos Cerastus Knight Atrapos"
LAS = "Atrapos lascutter"
GRAV = "Graviton singularity cannon"


@pytest.fixture(scope="module")
def engine():
    return RankingEngine("chaos-knights")


@pytest.fixture(scope="module")
def atrapos_fixed(engine):
    chars = json.load(open(CHAOS_KNIGHTS))
    build = chars[ATRAPOS]["weapon_options"]["builds"][0]
    return build.get("fixed", [])


class TestAtraposConfig:
    """The config references group entries, never '- profile' names."""

    def test_no_profile_suffixed_entries(self, atrapos_fixed):
        names = [f["name"] for f in atrapos_fixed]
        assert not any(" - " in n for n in names), (
            f"Atrapos fixed must use group names, found profile names: {names}"
        )

    def test_lascutter_group_present(self, atrapos_fixed):
        assert any(f["name"] == LAS for f in atrapos_fixed)

    def test_graviton_group_present(self, atrapos_fixed):
        assert any(f["name"] == GRAV for f in atrapos_fixed)

    def test_singularity_cannon_is_ranged(self, atrapos_fixed):
        g = [f for f in atrapos_fixed if f["name"] == GRAV]
        assert g and all(f.get("type") == "ranged" for f in g)


class TestAtraposDualProfileSelection:
    """Dual-profile lascutter resolves the correct profile per list.

    The lascutter is Ranged (36"/24") AND Melee (A12/A6) with a low/high
    intensity choice. The slots resolver must pass category so the ranged
    list receives ranged profiles and the melee list melee profiles —
    never mixed.
    """

    def _resolve(self, engine):
        chars = json.load(open(CHAOS_KNIGHTS))
        build = chars[ATRAPOS]["weapon_options"]["builds"][0]
        return engine._resolve_slots_build(build, ATRAPOS, engine.resolve_target("MEQ"))

    def test_ranged_lascutter_has_ranged_profile(self, engine):
        r, m, _n = self._resolve(engine)
        las_r = [w for w in r if "lascutter" in w.name.lower()]
        assert las_r, "lascutter should contribute to ranged"
        # Ranged low intensity is 2D6 = A7 avg; melee low is A12. If the
        # category leaked, the ranged list would carry the melee A12 profile.
        assert all(w.attacks < 10 for w in las_r), (
            f"ranged lascutter leaked melee profile: {[(w.name, w.attacks) for w in las_r]}"
        )

    def test_melee_lascutter_has_melee_profile(self, engine):
        r, m, _n = self._resolve(engine)
        las_m = [w for w in m if "lascutter" in w.name.lower()]
        assert las_m, "lascutter should contribute to melee"
        # Melee low intensity is A12 (not the ranged A7). The base profile
        # must be the melee one.
        assert all(w.attacks >= 10 for w in las_m), (
            f"melee lascutter leaked ranged profile: {[(w.name, w.attacks) for w in las_m]}"
        )

    def test_variants_stay_in_category(self, engine):
        """Choice variants (low/high) must be same-category, never mixed."""
        r, m, _n = self._resolve(engine)
        for w in r + m:
            for v in (w.variants or []):
                assert "lascutter" not in w.name.lower() or "lascutter" in v.name.lower()
        las_r = [w for w in r if "lascutter" in w.name.lower()]
        las_m = [w for w in m if "lascutter" in w.name.lower()]
        # Ranged lascutter variant = high intensity RANGED (A D6 = 3.5)
        for w in las_r:
            for v in (w.variants or []):
                assert v.attacks <= 4, f"ranged variant leaked melee stats: {v.name} A{v.attacks}"
        # Melee lascutter variant = high intensity MELEE (A6)
        for w in las_m:
            for v in (w.variants or []):
                assert v.attacks >= 5, f"melee variant leaked ranged stats: {v.name} A{v.attacks}"

    def test_graviton_choice_preserved(self, engine):
        r, m, _n = self._resolve(engine)
        g = [w for w in r if "singularity" in w.name.lower()]
        assert g, "graviton cannon must resolve as ranged"
        assert any(w.variants for w in g), "contained/singularity choice lost"

    def test_resolvable_via_loadout(self, engine):
        for tname in ("GEQ", "MEQ", "Knight"):
            res = engine.resolve_loadout(ATRAPOS, engine.resolve_target(tname))
            assert res is not None
            pts, r, m, inn, info = res
            assert pts == 395
            assert r and m


class TestDualProfileSlotsAcrossFactions:
    """The category pass-through fixes dual-profile weapons everywhere.

    Regression proof: the Farseer's melee Singing Spear must resolve the
    MELEE profile (A2 S3), not the thrown/ranged one (A1 S9).
    """

    @pytest.fixture(scope="module")
    def aeldari(self):
        return RankingEngine("aeldari")

    def _farseer(self, aeldari):
        res = aeldari.resolve_loadout("Farseer", aeldari.resolve_target("MEQ"))
        assert res is not None
        return res

    def test_farseer_singing_spear_melee_profile(self, aeldari):
        res = self._farseer(aeldari)
        pts, r, m, inn, info = res
        spears = [w for w in m if "Singing Spear" in w.name]
        assert spears, "Farseer melee list lost the Singing Spear"
        assert all(w.strength == 3 and w.attacks == 2 for w in spears), (
            f"Singing Spear melee resolved to ranged profile: "
            f"{[(w.name, w.strength, w.attacks) for w in spears]}"
        )

    def test_farseer_singing_spear_ranged_kept(self, aeldari):
        res = self._farseer(aeldari)
        pts, r, m, inn, info = res
        spears = [w for w in r if "Singing Spear" in w.name]
        assert spears and all(w.strength == 9 and w.attacks == 1 for w in spears)
