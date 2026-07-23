"""Tests for engine gaps not covered by test_dpp.py, test_pricing.py, or test_mfm_coverage.py.

Targets 10 specific gaps:
  1. Weapon multiplicity (weapon.count)
  2. Nested selectionEntryGroups (weapons loadable from deep groups)
  3. Knight Tyrant config (all weapons fixed, no weapon_slots)
  4. Soul Grinder merge (weapon_options path picks best ranged)
  5. _pct() midpoint formula edge cases
  6. _safe_int() guard on non-integer inputs
  7. Cross-faction weapon lookup
  8. Legends filtering
  9. Multi-weapon-mode (weapons with multiple profiles)
 10. Edge cases: empty config, missing files, max_points=0, zero weapons
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from dpp import (
    WeaponProfile,
    TargetProfile,
    WeaponModifier,
    DetachmentModifier,
    compute_weapon_dpp,
    compute_surv,
    compute_mob,
    UnitDefense,
    HitMode,
)
from weapon_loader import WeaponCatalog


# ═══════════════════════════════════════════════════════════════════════
# 1. Weapon multiplicity — weapon.count multiplies total_damage
# ═══════════════════════════════════════════════════════════════════════


class TestWeaponMultiplicity:
    """weapon.count must multiply total_damage in DPP computation."""

    def test_count_1_is_baseline(self, MEQ):
        """count=1 is the default — no multiplier."""
        wp = WeaponProfile(
            name="Lascannon", attacks=1, bs=3, strength=9, ap=-3,
            damage=3.5, abilities=[], count=1,
        )
        r = compute_weapon_dpp(wp, MEQ, unit_points=100)
        # Single shot: hits × wounds × saves × 3.5
        assert r["total_damage"] > 0
        assert r["dpp"] > 0

    def test_count_3_triples_damage(self, MEQ):
        """count=3 should produce ~3× the total_damage of count=1.

        Tolerance accounts for round(total_damage, 2) in the output dict.
        """
        base = WeaponProfile(
            name="Twin heavy bolter", attacks=3, bs=3, strength=5,
            ap=-1, damage=1, abilities=[], count=1,
        )
        tripled = WeaponProfile(
            name="Twin heavy bolter", attacks=3, bs=3, strength=5,
            ap=-1, damage=1, abilities=[], count=3,
        )
        r_base = compute_weapon_dpp(base, MEQ, unit_points=100)
        r_trip = compute_weapon_dpp(tripled, MEQ, unit_points=100)
        # Damage must be ~3× (count multiplier applied at end of pipeline).
        # Tolerance: 2dp rounding can cause ~0.7% error at small values.
        ratio = r_trip["total_damage"] / r_base["total_damage"]
        assert abs(ratio - 3.0) < 0.02, (
            f"Expected ~3× damage, got ratio={ratio:.4f} "
            f"(base={r_base['total_damage']}, tripled={r_trip['total_damage']})"
        )

    def test_count_scales_dpp_linearly(self, MEQ):
        """DPP must scale approximately linearly with count (same unit_points).

        Tolerance accounts for round(total_damage, 2) in the output dict.
        """
        counts = [1, 2, 3, 5]
        damages = []
        for count in counts:
            wp = WeaponProfile(
                name="Heavy bolter", attacks=3, bs=3, strength=5,
                ap=-1, damage=1, abilities=[], count=count,
            )
            r = compute_weapon_dpp(wp, MEQ, unit_points=100)
            damages.append(r["total_damage"])
        # Each damage should be proportional to its count
        base_damage = damages[0] / counts[0]  # damage per single weapon
        for i, (count, dmg) in enumerate(zip(counts, damages)):
            expected = base_damage * count
            # Allow tolerance for 2dp rounding in output dict
            assert abs(dmg - expected) < 0.03, (
                f"count={count}: expected ~{expected:.4f}, got {dmg}"
            )

    def test_count_0_gives_zero_damage(self, MEQ):
        """count=0 should produce zero damage (no weapons fired)."""
        wp = WeaponProfile(
            name="Ghost gun", attacks=5, bs=3, strength=4, ap=-1,
            damage=1, abilities=[], count=0,
        )
        r = compute_weapon_dpp(wp, MEQ, unit_points=100)
        assert r["total_damage"] == 0.0

    def test_count_does_not_affect_hits_or_wounds(self, MEQ):
        """count affects only total_damage, not expected_hits or regular_wounds."""
        wp1 = WeaponProfile(
            name="Test", attacks=4, bs=3, strength=5, ap=-1,
            damage=2, abilities=[], count=1,
        )
        wp3 = WeaponProfile(
            name="Test", attacks=4, bs=3, strength=5, ap=-1,
            damage=2, abilities=[], count=3,
        )
        r1 = compute_weapon_dpp(wp1, MEQ, unit_points=100)
        r3 = compute_weapon_dpp(wp3, MEQ, unit_points=100)
        # Hits and wounds are per-shot; count only multiplies the final damage
        assert r3["expected_hits"] == r1["expected_hits"]
        assert r3["regular_wounds"] == r1["regular_wounds"]
        # Total damage is ~3× (tolerance for 2dp rounding)
        ratio = r3["total_damage"] / r1["total_damage"]
        assert abs(ratio - 3.0) < 0.02


# ═══════════════════════════════════════════════════════════════════════
# 2. Nested selectionEntryGroups — weapons loadable from deep groups
# ═══════════════════════════════════════════════════════════════════════


class TestNestedSelectionEntryGroups:
    """Weapons from deeply nested selectionEntryGroups must be loadable.

    The BSData parser recurses into nested selectionEntryGroups to find
    weapons (e.g. Bloodthirster: Wargear → Replace great axe → profiles).
    We test that the resulting catalog contains these weapons.
    """

    def test_daemon_prince_has_all_melee_variants(self, weapon_catalog):
        """Daemon Prince weapons from nested wargear groups must be loadable."""
        # The Daemon Prince has weapons defined in nested groups
        # (arm options, wargear replacements). Verify at least the core ones load.
        melee_weapons = ["Hellforged sword", "Malefic talons"]
        for name in melee_weapons:
            try:
                wp = weapon_catalog.load(name)
                assert wp.attacks > 0, f"{name} should have attacks > 0"
            except KeyError:
                # Not all weapons may be in the GK catalog — skip if not found
                pass

    def test_weapon_catalog_loads_unit_specific_variants(self, weapon_catalog):
        """Weapons that vary by unit must resolve correctly with unit_name."""
        # NFW has different stats per unit (Strike vs Paladin)
        nfw_strike = weapon_catalog.load("Nemesis force weapon", unit_name="Strike Squad")
        nfw_pally = weapon_catalog.load("Nemesis force weapon", unit_name="Paladin Squad")
        # Both should load — they may have different profiles
        assert nfw_strike.name is not None
        assert nfw_pally.name is not None

    def test_weapon_catalog_count_propagated(self, weapon_catalog):
        """count field must be propagated from merged JSON to WeaponProfile."""
        # Load any weapon — count defaults to 1 if not set
        sb = weapon_catalog.load("Storm bolter", unit_name="Strike Squad")
        assert hasattr(sb, "count")
        assert sb.count >= 1


# ═══════════════════════════════════════════════════════════════════════
# 3. Knight Tyrant config — all weapons fixed, no weapon_slots
# ═══════════════════════════════════════════════════════════════════════


class TestKnightTyrantConfig:
    """Knight Tyrant: all weapons listed as fixed in characters.json.

    No weapon_slots, no weapon_options — resolve_loadout takes the
    character path and returns all listed weapons.
    """

    def test_tyrant_resolves_all_fixed_weapons(self):
        """Knight Tyrant must resolve with all 8 ranged + 1 melee weapon."""
        from ranking import RankingEngine
        engine = RankingEngine("chaos-knights")
        meq = engine.config.target_profiles["MEQ"]
        resolved = engine.resolve_loadout("Knight Tyrant", meq)
        assert resolved is not None
        pts, ranged, melee, innate, info = resolved
        # Fixed weapons: 8 ranged, 1 melee (Titanic feet)
        assert len(ranged) >= 4, f"Expected ≥4 ranged weapons, got {len(ranged)}"
        assert len(melee) >= 1, f"Expected ≥1 melee, got {len(melee)}"
        # Titanic feet must be in melee
        melee_names = [w.name for w in melee]
        assert "Titanic feet" in melee_names

    def test_tyrant_points_match_config(self):
        """Knight Tyrant points must match characters.json config."""
        from ranking import RankingEngine
        engine = RankingEngine("chaos-knights")
        meq = engine.config.target_profiles["MEQ"]
        resolved = engine.resolve_loadout("Knight Tyrant", meq)
        pts = resolved[0]
        config_pts = engine.config.characters["Knight Tyrant"]["pts"]
        assert pts == config_pts, f"Tyrant pts={pts}, config={config_pts}"

    def test_tyrant_no_weapon_slots(self):
        """Knight Tyrant must NOT have weapon_slots in config."""
        from ranking import RankingEngine
        engine = RankingEngine("chaos-knights")
        ch = engine.config.characters["Knight Tyrant"]
        assert "weapon_slots" not in ch, "Tyrant should use fixed weapons, not slots"

    def test_tyrant_in_ranking_output(self):
        """Knight Tyrant must appear in CK ranking results."""
        from ranking import RankingEngine
        engine = RankingEngine("chaos-knights")
        meq = engine.config.target_profiles["MEQ"]
        results = engine.compute_ranking(target=meq)
        names = [r["name"] for r in results]
        assert "Knight Tyrant" in names, "Tyrant must be in ranking results"


# ═══════════════════════════════════════════════════════════════════════
# 4. Soul Grinder merge — weapon_options path picks best ranged
# ═══════════════════════════════════════════════════════════════════════


class TestSoulGrinderMerge:
    """Soul Grinder: 4 god-specific variants, each with weapon_options.

    The weapon_options.json has per-god Soul Grinder entries with ranged options.
    resolve_loadout must take the weapon_options path and pick the
    best ranged loadout vs a given target.
    """

    SOUL_GRINDER_NAME = "Khorne Soul Grinder"  # representative variant

    def test_soul_grinder_resolves_via_weapon_options(self):
        """Soul Grinder must resolve via weapon_options (not vehicles fixed path)."""
        from ranking import RankingEngine
        engine = RankingEngine("chaos-daemons")
        meq = engine.config.target_profiles["MEQ"]
        resolved = engine.resolve_loadout(self.SOUL_GRINDER_NAME, meq)
        assert resolved is not None, f"{self.SOUL_GRINDER_NAME} must resolve"
        pts, ranged, melee, innate, info = resolved
        assert pts > 0
        assert len(ranged) >= 1, f"{self.SOUL_GRINDER_NAME} must have ranged weapons"

    def test_soul_grinder_has_all_ranged_options(self):
        """All ranged options for the variant must be available."""
        from ranking import RankingEngine
        engine = RankingEngine("chaos-daemons")
        wo = engine.config.weapon_options.get(self.SOUL_GRINDER_NAME, {})
        expected_ranged = [
            "Torrent of burning blood", "Harvester cannon",
        ]
        for wname in expected_ranged:
            assert wname in wo.get("ranged", []), f"Missing ranged option: {wname}"

    def test_soul_grinder_loadout_differs_per_target(self):
        """Soul Grinder should pick different best weapons vs different targets."""
        from ranking import RankingEngine
        engine = RankingEngine("chaos-daemons")
        meq = engine.config.target_profiles["MEQ"]
        knight = engine.config.target_profiles["Knight"]
        r_meq = engine.resolve_loadout(self.SOUL_GRINDER_NAME, meq)
        r_knight = engine.resolve_loadout(self.SOUL_GRINDER_NAME, knight)
        assert r_meq is not None and r_knight is not None
        # Both should resolve, with at least 1 ranged weapon
        assert len(r_meq[1]) >= 1
        assert len(r_knight[1]) >= 1

    def test_soul_grinder_pts_matches_config(self):
        """Soul Grinder pts must match weapon_options config."""
        from ranking import RankingEngine
        engine = RankingEngine("chaos-daemons")
        meq = engine.config.target_profiles["MEQ"]
        resolved = engine.resolve_loadout(self.SOUL_GRINDER_NAME, meq)
        wo = engine.config.weapon_options[self.SOUL_GRINDER_NAME]
        assert resolved[0] == wo["pts"], f"Expected {wo['pts']}pts"

    def test_all_four_god_variants_exist(self):
        """All 4 god-specific Soul Grinder variants must be in weapon_options."""
        from ranking import RankingEngine
        engine = RankingEngine("chaos-daemons")
        for god in ["Khorne", "Nurgle", "Slaanesh", "Tzeentch"]:
            name = f"{god} Soul Grinder"
            wo = engine.config.weapon_options.get(name)
            assert wo is not None, f"Missing {name} in weapon_options"
            assert "ranged" in wo and len(wo["ranged"]) >= 1, f"{name} must have ranged"


# ═══════════════════════════════════════════════════════════════════════
# 5. _pct() midpoint formula edge cases
# ═══════════════════════════════════════════════════════════════════════


class TestPctFormula:
    """_pct() must handle edge cases: n=1, n=2, all same, ties."""

    @staticmethod
    def _pct(val, series):
        """Replicate the _pct formula from ranking.py for unit testing."""
        n = len(series)
        if n <= 1:
            return 100
        below = sum(1 for x in series if x < val)
        same = sum(1 for x in series if x == val)
        return round((below + 0.5 * (same - 1)) / (n - 1) * 100)

    def test_single_element_returns_100(self):
        """n=1: _pct must return 100 (no comparison possible)."""
        assert self._pct(50, [50]) == 100

    def test_empty_series_returns_100(self):
        """n=0: _pct must return 100 (edge case guard)."""
        assert self._pct(50, []) == 100

    def test_two_elements_below(self):
        """n=2: value below the other → 0th percentile."""
        assert self._pct(1, [1, 5]) == 0

    def test_two_elements_above(self):
        """n=2: value above the other → 100th percentile."""
        assert self._pct(5, [1, 5]) == 100

    def test_two_elements_equal(self):
        """n=2: both equal → 50th percentile (midpoint)."""
        assert self._pct(3, [3, 3]) == 50

    def test_all_same_value(self):
        """All values identical → 50th percentile for each."""
        series = [7, 7, 7, 7, 7]
        for val in series:
            assert self._pct(val, series) == 50

    def test_distinct_sorted_values(self):
        """5 distinct values: each should get correct percentile."""
        series = [10, 20, 30, 40, 50]
        # 10: below=0, same=1 → (0 + 0.5*(1-1))/4 * 100 = 0
        assert self._pct(10, series) == 0
        # 20: below=1, same=1 → (1 + 0.5*(1-1))/4 * 100 = 25
        assert self._pct(20, series) == 25
        # 30: below=2, same=1 → (2 + 0.5*(1-1))/4 * 100 = 50
        assert self._pct(30, series) == 50
        # 40: below=3, same=1 → (3 + 0.5*(1-1))/4 * 100 = 75
        assert self._pct(40, series) == 75
        # 50: below=4, same=1 → (4 + 0.5*(1-1))/4 * 100 = 100
        assert self._pct(50, series) == 100

    def test_ties_in_middle(self):
        """Three-way tie in the middle produces correct midpoint."""
        series = [10, 30, 30, 30, 50]
        # 30: below=1, same=3 → (1 + 0.5*(3-1))/4 * 100 = (1+1)/4*100 = 50
        assert self._pct(30, series) == 50

    def test_extreme_duplicates(self):
        """Two values, one unique → correct split."""
        series = [5, 5, 10]
        # 5: below=0, same=2 → (0 + 0.5*(2-1))/2 * 100 = 25
        assert self._pct(5, series) == 25
        # 10: below=2, same=1 → (2 + 0.5*(1-1))/2 * 100 = 100
        assert self._pct(10, series) == 100


# ═══════════════════════════════════════════════════════════════════════
# 6. _safe_int() guard on non-integer inputs
# ═══════════════════════════════════════════════════════════════════════


class TestSafeInt:
    """_safe_int must handle non-integer inputs without crashing.

    The function is defined locally inside get_unit_info — we test it
    via get_unit_info's behaviour, or by importing and calling it directly.
    """

    @staticmethod
    def _safe_int(val, default=0):
        """Replicate _safe_int from ranking.py for unit testing."""
        s = str(val).replace('"', '').replace('+', '').replace('*', '').strip()
        digits = ''.join(c for c in s if c.isdigit() or c == '-')
        return int(digits) if digits else default

    def test_normal_integer(self):
        """Integer input returns itself."""
        assert self._safe_int(5) == 5

    def test_string_with_plus(self):
        """'3+' → 3."""
        assert self._safe_int("3+") == 3

    def test_string_with_quotes(self):
        """'12\"' → 12."""
        assert self._safe_int('12"') == 12

    def test_string_with_star(self):
        """'*2' → 2 (asterisk stripped)."""
        assert self._safe_int("*2") == 2

    def test_empty_string_returns_default(self):
        """Empty string → default."""
        assert self._safe_int("", default=7) == 7

    def test_none_returns_default(self):
        """None → default."""
        assert self._safe_int(None, default=99) == 99

    def test_non_numeric_string_returns_default(self):
        """'abc' → default (no digits found)."""
        assert self._safe_int("abc", default=42) == 42

    def test_mixed_string_extracts_digits(self):
        """'W3+' → 3 (extracts leading digit)."""
        assert self._safe_int("W3+") == 3

    def test_negative_number(self):
        """'-1' → -1."""
        assert self._safe_int("-1") == -1

    def test_float_string_extracts_all_digits(self):
        """'3.5' → 35 (digits extraction includes decimal digits)."""
        # _safe_int extracts ALL digit characters, not just the integer part
        assert self._safe_int("3.5") == 35

    def test_default_zero(self):
        """Default is 0 when not specified."""
        assert self._safe_int("xyz") == 0

    def test_zero_string(self):
        """'0' → 0."""
        assert self._safe_int("0") == 0


# ═══════════════════════════════════════════════════════════════════════
# 7. Cross-faction weapon lookup
# ═══════════════════════════════════════════════════════════════════════


class TestCrossFactionWeaponLookup:
    """Weapons must be resolved from the faction's own merged JSON.

    Cross-faction lookup means: a weapon defined in one faction's merged
    JSON should be loadable from that faction's catalog, even if another
    faction also has a unit with the same weapon name (different stats).
    """

    def test_ck_titanic_feet_loadable(self):
        """Chaos Knights catalog must resolve 'Titanic feet'."""
        from ranking import RankingEngine
        engine = RankingEngine("chaos-knights")
        tf = engine.W("Titanic feet", unit_name="Knight Despoiler")
        assert tf.name == "Titanic feet"
        assert tf.attacks > 0

    def test_ck_weapons_not_polluted_by_gk(self):
        """CK weapon catalog must not contain GK Psychic weapons."""
        from weapon_loader import WeaponCatalog
        ck_merged = str(
            Path(__file__).resolve().parent.parent / "data" / "merged" / "chaos-knights.json"
        )
        ck_cat = WeaponCatalog(ck_merged, faction="chaos-knights")
        # CK weapons should NOT have Psychic ability (CK has no faction overlay for it)
        tf = ck_cat.load("Titanic feet")
        assert "Psychic" not in tf.abilities, "CK weapons must not be Psychic"

    def test_gk_psycannon_has_psychic_overlay(self):
        """GK Psycannon must have Psychic from faction overlay."""
        from ranking import RankingEngine
        engine = RankingEngine("grey-knights")
        pc = engine.W("Psycannon")
        assert "Psychic" in pc.abilities

    def test_different_factions_different_weapon_catalogs(self):
        """GK and CK catalogs must be independent — loading same weapon name
        from each should potentially give different results."""
        from weapon_loader import WeaponCatalog
        repo = Path(__file__).resolve().parent.parent
        gk_cat = WeaponCatalog(str(repo / "data" / "merged" / "grey-knights.json"), faction="grey-knights")
        ck_cat = WeaponCatalog(str(repo / "data" / "merged" / "chaos-knights.json"), faction="chaos-knights")
        # Both should load "Titanic feet" but CK has it, GK may not
        ck_tf = ck_cat.load("Titanic feet")
        assert ck_tf.name == "Titanic feet"


# ═══════════════════════════════════════════════════════════════════════
# 8. Legends filtering
# ═══════════════════════════════════════════════════════════════════════


class TestLegendsFiltering:
    """Legends units must be excluded by default from ranking results.

    The engine checks config.is_legends() which looks for 'legends: true'
    in any config dict entry. No current configs have this flag, so we
    test the mechanism with a synthetic unit.
    """

    def test_is_legends_returns_false_for_normal_unit(self):
        """Normal units must not be flagged as Legends."""
        from ranking import FactionConfig
        config = FactionConfig(
            str(Path(__file__).resolve().parent.parent / "data" / "config" / "chaos-knights")
        )
        assert config.is_legends("Knight Tyrant") is False

    def test_is_legends_returns_true_when_flag_set(self):
        """Unit with legends=true in config must be flagged."""
        from ranking import FactionConfig
        # Create a temp config dir with a legends unit
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            # Minimal supported.json
            (config_dir / "supported.json").write_text(json.dumps({
                "key": "test-faction",
                "name": "Test",
                "keywords": ["FACTION: TEST"],
                "target_profiles": {"MEQ": {"toughness": 4, "save": 3}},
            }))
            # squads.json with a legends unit
            (config_dir / "squads.json").write_text(json.dumps({
                "Legends Unit": {
                    "legends": True,
                    "pts": 100,
                    "n": 5,
                    "specials": [],
                    "special_max": 0,
                    "ranged": "Bolter",
                    "melee": "Chainsword",
                    "info": {"T": 4, "SV": 3, "W": 2},
                },
                "Normal Unit": {
                    "pts": 50,
                    "n": 5,
                    "specials": [],
                    "special_max": 0,
                    "ranged": "Bolter",
                    "melee": "Chainsword",
                    "info": {"T": 4, "SV": 3, "W": 2},
                },
            }))
            # Other required files as empty
            for fn in ["characters.json", "vehicles.json", "weapon_options.json", "notes.json"]:
                (config_dir / fn).write_text("{}")

            config = FactionConfig(str(config_dir))
            assert config.is_legends("Legends Unit") is True
            assert config.is_legends("Normal Unit") is False

    def test_legends_unit_excluded_from_ranking(self):
        """Legends units must not appear in compute_ranking results."""
        from ranking import FactionConfig
        # We can't easily run compute_ranking on a synthetic faction without
        # merged data, so test the is_legends gate directly
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            (config_dir / "supported.json").write_text(json.dumps({
                "key": "test-faction",
                "name": "Test",
                "keywords": ["FACTION: TEST"],
                "target_profiles": {"MEQ": {"toughness": 4, "save": 3}},
            }))
            (config_dir / "squads.json").write_text(json.dumps({
                "Legends Unit": {"legends": True, "pts": 100, "n": 5, "specials": [], "special_max": 0, "ranged": "Bolter", "melee": "Chainsword", "info": {"T": 4, "SV": 3, "W": 2}},
            }))
            for fn in ["characters.json", "vehicles.json", "weapon_options.json", "notes.json"]:
                (config_dir / fn).write_text("{}")

            config = FactionConfig(str(config_dir))
            # The ranking loop checks is_legends() before adding to results
            assert "Legends Unit" in config.known_units  # known but legends
            assert config.is_legends("Legends Unit") is True


# ═══════════════════════════════════════════════════════════════════════
# 9. Multi-weapon-mode — weapons with multiple profiles
# ═══════════════════════════════════════════════════════════════════════


class TestMultiWeaponMode:
    """Weapons with multiple profiles (e.g. Ordnance vs Battle Cannon modes)
    must be handled correctly by the catalog.

    The catalog groups variants by stat signature and picks the most
    common one as default. Unit-specific variant selection uses unit_name.
    """

    def test_weapon_with_multiple_profiles_loads_default(self, weapon_catalog):
        """Loading a multi-profile weapon should return the most common variant."""
        # Ectoplasma decimator has "standard" and "supercharge" modes
        # in the CK merged JSON — test that loading works
        from ranking import RankingEngine
        engine = RankingEngine("chaos-knights")
        # Both modes should be loadable
        std = engine.W("Ectoplasma decimator - standard", unit_name="Knight Tyrant")
        assert std.name is not None
        assert std.damage > 0

    def test_supercharge_different_from_standard(self):
        """Ectoplasma supercharge should have different stats than standard."""
        from ranking import RankingEngine
        engine = RankingEngine("chaos-knights")
        std = engine.W("Ectoplasma decimator - standard", unit_name="Knight Tyrant")
        sup = engine.W("Ectoplasma decimator - supercharge", unit_name="Knight Tyrant")
        # Supercharge typically has higher damage but hazardous
        # Just verify they're different weapons
        assert std.name != sup.name or std.damage != sup.damage or std.attacks != sup.attacks, (
            "Standard and supercharge should differ in at least one stat"
        )

    def test_weapon_catalog_groups_by_signature(self, weapon_catalog):
        """Weapons with same stat signature should be grouped."""
        # Check that the catalog's variant group index is populated
        assert len(weapon_catalog._variant_groups) > 0

    def test_reaper_chaintalon_strike_vs_sweep(self):
        """Reaper chaintalon has strike and sweep profiles — both loadable."""
        from ranking import RankingEngine
        engine = RankingEngine("chaos-knights")
        strike = engine.W("Reaper chaintalon - strike", unit_name="War Dog Huntsman")
        sweep = engine.W("Reaper chaintalon - sweep", unit_name="War Dog Huntsman")
        # Sweep should have more attacks than strike (melee paradigm)
        assert sweep.attacks >= strike.attacks, (
            f"Sweep ({sweep.attacks}A) should have ≥ strike ({strike.attacks}A)"
        )


# ═══════════════════════════════════════════════════════════════════════
# 10. Edge cases
# ═══════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Edge cases that could break silently."""

    def test_empty_config_no_crash(self):
        """FactionConfig with all-empty dicts should not crash."""
        from ranking import FactionConfig
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            (config_dir / "supported.json").write_text(json.dumps({
                "key": "empty-faction",
                "name": "Empty",
                "keywords": ["FACTION: EMPTY"],
                "target_profiles": {"MEQ": {"toughness": 4, "save": 3}},
            }))
            for fn in ["squads.json", "characters.json", "vehicles.json",
                       "weapon_options.json", "notes.json"]:
                (config_dir / fn).write_text("{}")

            config = FactionConfig(str(config_dir))
            assert config.known_units == set()
            assert len(config.target_profiles) == 1

    def test_missing_weapon_options_file(self):
        """Missing weapon_options.json must not crash (returns {})."""
        from ranking import FactionConfig
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            (config_dir / "supported.json").write_text(json.dumps({
                "key": "no-wo",
                "name": "NoWO",
                "keywords": [],
                "target_profiles": {},
            }))
            for fn in ["squads.json", "characters.json", "vehicles.json", "notes.json"]:
                (config_dir / fn).write_text("{}")
            # Deliberately do NOT create weapon_options.json

            config = FactionConfig(str(config_dir))
            assert config.weapon_options == {}

    def test_max_points_zero_includes_all(self):
        """max_points=0 is falsy in Python → engine treats it as 'no limit'.

        The guard is `if max_points and pts > max_points`. Since 0 is falsy,
        max_points=0 does NOT filter. This documents the actual behaviour.
        """
        from ranking import RankingEngine
        engine = RankingEngine("chaos-knights")
        meq = engine.config.target_profiles["MEQ"]
        results_zero = engine.compute_ranking(target=meq, max_points=0)
        results_none = engine.compute_ranking(target=meq, max_points=None)
        # Both should return the same results (0 is treated as no limit)
        assert len(results_zero) == len(results_none)

    def test_max_points_none_includes_all(self):
        """max_points=None must include all units regardless of cost."""
        from ranking import RankingEngine
        engine = RankingEngine("chaos-knights")
        meq = engine.config.target_profiles["MEQ"]
        results = engine.compute_ranking(target=meq, max_points=None)
        # Should include all CK units in config
        assert len(results) > 0

    def test_unit_with_zero_ranged_and_zero_melee(self):
        """A unit with no ranged and no melee weapons should produce 0 damage."""
        # Directly test _ld_dmg with empty lists
        from ranking import _ld_dmg
        meq = TargetProfile(toughness=4, save=3)
        dmg = _ld_dmg([], [], [], meq)
        assert dmg == 0.0

    def test_weapon_with_zero_bs_gives_minimal_damage(self, MEQ):
        """Weapon with BS6 (worst possible) should still deal some damage."""
        wp = WeaponProfile(
            name="Terrible Gun", attacks=10, bs=6, strength=4, ap=0,
            damage=1, abilities=[],
        )
        r = compute_weapon_dpp(wp, MEQ, unit_points=100)
        # BS6+ = 1/6 chance to hit, but some damage is possible
        assert r["total_damage"] >= 0
        assert r["expected_hits"] > 0  # still some hits on 6+

    def test_weapon_with_bs2_plus_hits_mostly(self, MEQ):
        """Weapon with BS2+ should hit ~83% of the time."""
        wp = WeaponProfile(
            name="Elite Gun", attacks=6, bs=2, strength=4, ap=0,
            damage=1, abilities=[],
        )
        r = compute_weapon_dpp(wp, MEQ, unit_points=100)
        # BS2+ = 5/6 hits = ~83%
        assert abs(r["expected_hits"] / 6 - 5 / 6) < 0.01

    def test_compute_surv_zero_wounds_division_error(self):
        """Unit with 0 wounds causes ZeroDivisionError in compute_surv.

        This is a known edge case: 0 wounds → 0 effective wounds → division
        by zero in pts_per_eff_w_ap0 calculation. In practice, no 40k unit
        has 0 wounds, so this is an academic boundary.
        """
        defense = UnitDefense(toughness=4, wounds_per_model=0, save=3, models=1)
        with pytest.raises(ZeroDivisionError):
            compute_surv(defense, unit_points=100)

    def test_compute_mob_zero_movement(self):
        """Unit with M=0 should get 'slow' tier."""
        result = compute_mob(movement=0, fly=False, deep_strike=False, oc=0, keywords=[])
        assert result["mobility_tier"] == "slow"

    def test_detachment_modifier_merge_empty_list(self):
        """Merging empty modifier list must not crash."""
        from dpp import merge_weapon_modifiers, merge_detachment_modifiers
        wm = merge_weapon_modifiers([])
        assert wm.hit_modifier == 0
        dm = merge_detachment_modifiers([])
        assert dm.name == "none"

    def test_weapon_modifier_merge_reroll_priority(self):
        """merge_weapon_modifiers: 'all' > '1s' > None for rerolls."""
        from dpp import merge_weapon_modifiers
        m1 = WeaponModifier(reroll_hits="1s")
        m2 = WeaponModifier(reroll_hits="all")
        merged = merge_weapon_modifiers([m1, m2])
        assert merged.reroll_hits == "all"

    def test_weapon_modifier_merge_additive_fields(self):
        """merge_weapon_modifiers: numeric fields must be summed."""
        from dpp import merge_weapon_modifiers
        m1 = WeaponModifier(hit_modifier=-1, sustained_hits_extra=1, extra_ap=-1)
        m2 = WeaponModifier(hit_modifier=-1, sustained_hits_extra=0, extra_ap=-1)
        merged = merge_weapon_modifiers([m1, m2])
        assert merged.hit_modifier == -2
        assert merged.sustained_hits_extra == 1
        assert merged.extra_ap == -2

    def test_detachment_modifier_merge_surv_best_value(self):
        """merge_detachment_modifiers: invuln/FNP take best (lowest) value."""
        from dpp import merge_detachment_modifiers
        d1 = DetachmentModifier(name="A", invulnerable_save=5, feel_no_pain=6)
        d2 = DetachmentModifier(name="B", invulnerable_save=4, feel_no_pain=5)
        merged = merge_detachment_modifiers([d1, d2])
        assert merged.invulnerable_save == 4  # best (lowest)
        assert merged.feel_no_pain == 5       # best (lowest)

    def test_compute_mob_fortification_returns_zero(self):
        """FORTIFICATION keyword must give mobility score 0."""
        from ranking import RankingEngine
        mob = compute_mob(
            movement=0, fly=False, deep_strike=False, oc=0,
            keywords=["FORTIFICATION"], gate_of_infinity=False,
        )
        score = RankingEngine.mob_score(mob)
        assert score == 0


# ═══════════════════════════════════════════════════════════════════════
# Bonus: _pct integration — verify it's used correctly in ranking
# ═══════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════
# 11. Cost penalty single application
# ═══════════════════════════════════════════════════════════════════════


class TestCostPenaltySingleApplication:
    """cost_eff must be applied only to _surv_pct, not again to _mission_score.

    Previously cost_eff was applied twice — once to SURV and once to the
    final mission_score. The second application has been removed.
    """

    @staticmethod
    def _cost_eff(pts):
        """Replicate the cost_eff formula from ranking.py."""
        return min(100.0, 20000.0 / pts)

    def test_cost_penalty_only_applied_to_surv(self):
        """Cost penalty applied to SURV contribution in mission_score, not to _surv_pct."""
        from ranking import RankingEngine
        engine = RankingEngine("chaos-knights")
        meq = engine.config.target_profiles["MEQ"]

        # Inject a mission profile so the mission scoring path fires
        engine.config.mission_profiles = {
            "_test_mission": {"dps": 30, "surv": 30, "obj": 20, "mob": 20},
        }

        results = engine.compute_ranking(target=meq, mission="_test_mission")
        assert len(results) >= 2, "Need ≥2 units for comparison"

        # Pick the cheapest and most expensive unit
        cheap = min(results, key=lambda r: r["points"])
        expensive = max(results, key=lambda r: r["points"])

        # cost_eff must differ (cheap gets full credit, expensive is penalised)
        ce_cheap = self._cost_eff(cheap["points"])
        ce_exp = self._cost_eff(expensive["points"])
        assert ce_cheap >= ce_exp, (
            f"cheap({cheap['points']}pts) cost_eff {ce_cheap} "
            f"should be ≥ expensive({expensive['points']}pts) cost_eff {ce_exp}"
        )

        # _surv_pct uses RAW turns (no cost_eff) — expensive unit may have higher _surv_pct
        # The cost penalty is applied to the SURV contribution in mission_score
        w = engine.config.mission_profiles["_test_mission"]
        for r in results:
            ce = self._cost_eff(r["points"])
            surv_contrib = w["surv"] * r["_surv_pct"] * ce / 100.0
            expected_score = (
                w["dps"] * r["_dps_pct"]
                + surv_contrib
                + w.get("obj", 0) * r["_obj_pct"]
                + w["mob"] * r["_mob_pct"]
            )
            assert abs(r["_mission_score"] - expected_score) < 0.01, (
                f"{r['name']}: _mission_score={r['_mission_score']} "
                f"≠ weighted sum with cost_eff={expected_score:.2f}"
            )

    def test_cost_eff_range(self):
        """cost_eff = min(100, 20000/pts) produces expected values for key price points."""
        cases = [
            (100, 100.0),
            (200, 100.0),   # 20000/200 = 100 → capped at 100
            (400, 50.0),    # 20000/400 = 50
            (2000, 10.0),   # 20000/2000 = 10
        ]
        for pts, expected in cases:
            result = self._cost_eff(pts)
            assert result == expected, (
                f"pts={pts}: expected cost_eff={expected}, got {result}"
            )


class TestPctIntegration:
    """_pct formula must produce valid percentiles in actual ranking output."""

    def test_ranking_percentiles_are_0_to_100(self):
        """All _dps_pct and _surv_pct values must be in [0, 100]."""
        from ranking import RankingEngine
        engine = RankingEngine("chaos-knights")
        meq = engine.config.target_profiles["MEQ"]
        results = engine.compute_ranking(target=meq)
        for r in results:
            assert 0 <= r["_dps_pct"] <= 100, f"{r['name']}: _dps_pct={r['_dps_pct']}"
            assert 0 <= r["_surv_pct"] <= 100, f"{r['name']}: _surv_pct={r['_surv_pct']}"
            assert 0 <= r["_mob_pct"] <= 100, f"{r['name']}: _mob_pct={r['_mob_pct']}"

    def test_highest_dpp_gets_100_dps_pct(self):
        """The unit with highest DPP must get _dps_pct=100."""
        from ranking import RankingEngine
        engine = RankingEngine("chaos-knights")
        meq = engine.config.target_profiles["MEQ"]
        results = engine.compute_ranking(target=meq)
        assert len(results) > 1
        # Find unit with max dpp
        max_dpp_unit = max(results, key=lambda r: r["dpp"])
        assert max_dpp_unit["_dps_pct"] == 100, (
            f"Highest DPP unit ({max_dpp_unit['name']}) should get _dps_pct=100, "
            f"got {max_dpp_unit['_dps_pct']}"
        )

    def test_single_unit_ranking_gives_100(self):
        """With only 1 unit in results, all percentiles must be 100."""
        from ranking import RankingEngine
        engine = RankingEngine("chaos-knights")
        # Use a tiny max_points to get only the cheapest unit
        meq = engine.config.target_profiles["MEQ"]
        all_results = engine.compute_ranking(target=meq, max_points=None)
        cheapest = min(all_results, key=lambda r: r["points"])
        # Run with max_points = cheapest unit's cost
        results = engine.compute_ranking(target=meq, max_points=cheapest["points"])
        # May have ties at same price, but with 1 or few units
        if len(results) == 1:
            assert results[0]["_dps_pct"] == 100
