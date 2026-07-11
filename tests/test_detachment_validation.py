"""
Tier 1 + Tier 2: Detachment modifier validation & engine integration tests.

Validates:
  - JSON structure (schema, fields, dp_cost, unit_filter match)
  - Engine applies modifiers without crash
  - DPP/SURV/MOB delta is as expected
  - Identifies inert fields (defined but not implemented in engine)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from engine.dpp import DetachmentModifier
from engine.ranking import RankingEngine

REPO_ROOT = Path(__file__).resolve().parent.parent
VALID_AFFECTS = {"dpp", "surv", "mob"}
VALID_DP_COST = {1, 2, 3}
VALID_DISPOSITION_IDS = {"purge-the-foe", "take-and-hold", "reconnaissance", "priority-assets", "disruption"}

# Cached merged data for checking unit weapon counts
_MERGED_CACHE: dict[str, list[str]] = {}


def _unit_has_weapons(faction: str, unit_name: str) -> bool:
    """Check if a unit has any weapon profiles in the merged data."""
    global _MERGED_CACHE
    if faction not in _MERGED_CACHE:
        path = REPO_ROOT / "data" / "merged" / f"{faction}.json"
        with open(path) as f:
            data = json.load(f)
        _MERGED_CACHE[faction] = {}
        for u in data.get("units", []):
            name = u.get("name", "")
            profile = u.get("profile")
            if profile:
                weapons = profile.get("weapons", [])
                has_w = any(w.get("profiles") or w.get("stats") for w in weapons)
                _MERGED_CACHE[faction][name] = has_w
            else:
                _MERGED_CACHE[faction][name] = False
    return _MERGED_CACHE[faction].get(unit_name, False)

# Fields that DetachmentModifier supports but the engine may not apply
INERT_FIELDS = {
    "stealth": "surv",           # not used in compute_surv
    "cover_save": "surv",        # not used in compute_surv
    "advance_and_charge": "mob", # not used in mob computation
    "fallback_and_shoot": "mob", # not used in mob computation
    "fallback_and_charge": "mob",# not used in mob computation
    "assault": "dpp",            # not passed to to_weapon_modifier
    "heavy_ignore": "dpp",       # not passed to to_weapon_modifier
}

FACTIONS = ["grey-knights", "chaos-knights", "chaos-daemons"]

# Expected detachment counts per faction
EXPECTED_COUNTS = {
    "grey-knights": 9,
    "chaos-knights": 8,
    "chaos-daemons": 9,
}


# ═══════════════════════════════════════════════════════════════════════
# Helper
# ═══════════════════════════════════════════════════════════════════════

def _load_detachment_json(faction: str) -> dict:
    """Load the raw detachment_modifiers.json for a faction."""
    p = REPO_ROOT / "data" / "config" / faction / "detachment_modifiers.json"
    if not p.exists():
        return {"detachments": {}}
    with open(p) as f:
        return json.load(f)


def _all_faction_units(faction: str) -> list[str]:
    """Get all known unit names for a faction."""
    eng = RankingEngine(faction)
    return list(eng.config.known_units)


def _all_unit_keywords(faction: str) -> dict[str, list[str]]:
    """Get all unit names with their keywords from merged data."""
    eng = RankingEngine(faction)
    result = {}
    for unit in eng.data["units"]:
        name = unit["name"]
        profile = unit.get("profile")
        if profile is None:
            continue
        kws = [k.upper() for k in profile.get("keywords", [])]
        if name in eng.config.known_units:
            result[name] = kws
    return result


def _filter_matches_unit(filter_str: str, unit_name: str, unit_keywords: list[str]) -> bool:
    """Check if a filter string matches a unit by name or keyword."""
    f = filter_str.upper()
    if f in unit_name.upper():
        return True
    return any(f == kw for kw in unit_keywords)


# ═══════════════════════════════════════════════════════════════════════
# TIER 1: STRUCTURAL VALIDATION
# ═══════════════════════════════════════════════════════════════════════

class TestTier1Structural:
    """JSON schema & data integrity checks."""

    def test_all_factions_have_detachment_file(self):
        """Every faction must have a detachment_modifiers.json."""
        for f in FACTIONS:
            p = REPO_ROOT / "data" / "config" / f / "detachment_modifiers.json"
            assert p.exists(), f"{f} missing detachment_modifiers.json"

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_detachment_count(self, faction):
        """Each faction must have the expected number of detachments."""
        data = _load_detachment_json(faction)
        dets = data.get("detachments", {})
        expected = EXPECTED_COUNTS[faction]
        assert len(dets) == expected, (
            f"{faction}: expected {expected} detachments, got {len(dets)}: {list(dets.keys())}"
        )

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_no_unknown_fields(self, faction):
        """Every field in every choice must be a known DetachmentModifier field."""
        known = {
            "name", "affects", "unit_filter", "condition", "description",
            # DPP
            "hit_modifier", "reroll_hits", "reroll_wounds", "plus1_to_wound",
            "sustained_hits_extra", "lethal_hits", "extra_ap", "ignore_cover",
            "assault", "heavy_ignore",
            # SURV
            "invulnerable_save", "feel_no_pain", "stealth", "cover_save",
            # MOB
            "movement_bonus", "advance_and_charge", "fallback_and_shoot",
            "fallback_and_charge",
        }
        # These are top-level keys in the detachment entry, not in choices
        top_level = {"dp_cost"}

        data = _load_detachment_json(faction)
        dets = data.get("detachments", {})

        errors = []
        for det_name, det_data in dets.items():
            # Check top-level keys
            for k in det_data:
                if k not in top_level and k not in ("choices",):
                    errors.append(f"{faction}/{det_name}: unknown top-level key '{k}'")

            choices = det_data.get("choices", [])
            for i, c in enumerate(choices):
                for k in c:
                    if k not in known:
                        errors.append(f"{faction}/{det_name}/choice[{i}]: unknown field '{k}'")

        assert not errors, "\n".join(errors)

    def _validate_modifier_field(self, faction, det_name, choice_idx, field, value, all_units):
        """Validate a single modifier field value."""
        errors = []

        if field == "name":
            if not isinstance(value, str) or len(value) == 0:
                errors.append(f"{faction}/{det_name}/choice[{choice_idx}]: name empty or not string")

        elif field == "affects":
            if value not in VALID_AFFECTS:
                errors.append(f"{faction}/{det_name}/choice[{choice_idx}]: affects='{value}' not in {VALID_AFFECTS}")

        elif field == "dp_cost":
            if value not in VALID_DP_COST:
                errors.append(f"{faction}/{det_name}: dp_cost={value} not in {VALID_DP_COST}")

        elif field == "unit_filter":
            if not isinstance(value, list):
                errors.append(f"{faction}/{det_name}/choice[{choice_idx}]: unit_filter not a list")
            else:
                # Check at least partial match against actual units
                for filt in value:
                    if not isinstance(filt, str) or len(filt) < 2:
                        errors.append(f"{faction}/{det_name}/choice[{choice_idx}]: filter '{filt}' too short")
                        continue
                    # Check filter matches at least one unit
                    matches = [u for u in all_units if filt.lower() in u.lower()]
                    if not matches:
                        errors.append(
                            f"{faction}/{det_name}/choice[{choice_idx}]: filter '{filt}' matches NO units "
                            f"(available: {[u for u in all_units if filt.split()[0].lower() in u.lower()][:3] or 'no close match'})"
                        )

        elif field == "condition":
            if not isinstance(value, str):
                errors.append(f"{faction}/{det_name}/choice[{choice_idx}]: condition not a string")

        return errors

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_field_values_valid(self, faction):
        """Validate field values across all detachments.

        unit_filter is checked against BOTH unit names and keywords from merged data.
        """
        data = _load_detachment_json(faction)
        dets = data.get("detachments", {})
        all_units = _all_faction_units(faction)
        unit_kw_map = _all_unit_keywords(faction)

        errors = []
        for det_name, det_data in dets.items():
            # Validate dp_cost
            dp_cost = det_data.get("dp_cost", None)
            if dp_cost is not None:
                errors.extend(self._validate_modifier_field(faction, det_name, -1, "dp_cost", dp_cost, all_units))

            choices = det_data.get("choices", [])
            assert len(choices) >= 1, f"{faction}/{det_name}: no choices"
            for i, c in enumerate(choices):
                for field, value in c.items():
                    if field == "unit_filter":
                        # Check against names + keywords (not just names)
                        for filt in value:
                            if not isinstance(filt, str) or len(filt) < 2:
                                errors.append(f"{faction}/{det_name}/choice[{i}]: filter '{filt}' too short")
                                continue
                            # Check filter matches at least one unit by name OR keyword
                            name_matches = [u for u in all_units if filt.lower() in u.lower()]
                            kw_matches = [
                                u for u, kws in unit_kw_map.items()
                                if filt.upper() in kws
                            ]
                            if not name_matches and not kw_matches:
                                errors.append(
                                    f"{faction}/{det_name}/choice[{i}]: filter '{filt}' matches NO units "
                                    f"(by name or keyword)"
                                )
                    else:
                        errors.extend(
                            self._validate_modifier_field(faction, det_name, i, field, value, all_units)
                        )

        assert not errors, "\n".join(errors[:30])  # cap at 30 errors

    def _check_duplicate_filters(self, faction):
        """Check for obviously redundant unit_filters."""
        data = _load_detachment_json(faction)
        dets = data.get("detachments", {})
        all_units = _all_faction_units(faction)

        issues = []
        for det_name, det_data in dets.items():
            choices = det_data.get("choices", [])
            for i, c in enumerate(choices):
                filt = c.get("unit_filter")
                if not filt:
                    # No filter = applies to all. Check if the description implies a filter
                    desc = c.get("description", "").lower()
                    if any(kw in desc for kw in ["only", "unit", "model", "character"]) and "all" not in desc:
                        issues.append(
                            f"{faction}/{det_name}/choice[{i}]: no unit_filter but description implies restriction"
                        )
        return issues

    def test_duplicate_filters(self):
        """Check for potentially missing unit_filters."""
        all_issues = []
        for f in FACTIONS:
            all_issues.extend(self._check_duplicate_filters(f))
        # This is advisory only — don't fail the test
        if all_issues:
            pytest.skip("Advisory: " + "; ".join(all_issues[:5]))


# ═══════════════════════════════════════════════════════════════════════
# TIER 2: ENGINE INTEGRATION
# ═══════════════════════════════════════════════════════════════════════

class TestTier2EngineIntegration:
    """Modifiers must apply correctly through the engine."""

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_each_modifier_applies_without_crash(self, faction):
        """Every modifier choice applies without raising."""
        eng = RankingEngine(faction)
        all_units = list(eng.config.known_units)

        for det in eng.list_detachments_with_modifiers():
            choices = eng.get_detachment_modifiers(det)
            for ci, _ in enumerate(choices):
                # Run ranking with this detachment + choice
                try:
                    results = eng.compute_ranking(
                        target=eng.config.target_profiles.get("MEQ"),
                        detachment=det,
                        detachment_choice=ci,
                    )
                    assert isinstance(results, list)
                except Exception as e:
                    pytest.fail(f"{faction}/{det}/choice[{ci}]: ranking crashed: {e}")

    # Modifier fields that the engine currently IGNORES (inert)
    INERT_FIELDS = {
        "stealth", "cover_save",
        "advance_and_charge", "fallback_and_shoot", "fallback_and_charge",
        "assault", "heavy_ignore",
    }

    def _check_modifier_delta(self, faction, det_name, choice_idx, target_name="MEQ"):
        """Check that a modifier actually changes DPP/SURV/MOB vs no modifier.

        Uses whatever metric matches the modifier's `affects` field.
        Also checks if the modifier ONLY uses inert fields (defined but not applied by engine).
        """
        eng = RankingEngine(faction)
        target = eng.config.target_profiles.get(target_name)

        # No modifier baseline
        base = eng.compute_ranking(target=target)
        base_map = {r["name"]: r for r in base}

        # With modifier
        modded = eng.compute_ranking(target=target, detachment=det_name, detachment_choice=choice_idx)
        mod_map = {r["name"]: r for r in modded}

        choice = eng.get_detachment_modifiers(det_name)[choice_idx]

        # Check if this choice ONLY uses inert fields
        # Exclude methods/callables, private attrs, and metadata fields
        choice_fields = {k for k in dir(choice)
                         if not k.startswith("_")
                         and not callable(getattr(choice, k))
                         and getattr(choice, k)
                         and k not in ("name", "affects", "unit_filter", "condition", "description")}
        only_inert = choice_fields and choice_fields.issubset(self.INERT_FIELDS | {"description"})

        deltas = []
        for name in base_map:
            if name not in mod_map:
                continue
            b = base_map[name]
            m = mod_map[name]

            if choice.affects == "dpp":
                delta = m["dpp"] - b["dpp"]
                if abs(delta) > 0.0001:
                    deltas.append(f"{name}: dpp {b['dpp']:.4f} → {m['dpp']:.4f} ({delta:+.4f})")
            elif choice.affects == "surv":
                b_eh = b["surv"]["effective_wounds"].get("ap4", 0)
                m_eh = m["surv"]["effective_wounds"].get("ap4", 0)
                delta = m_eh - b_eh
                if abs(delta) > 0.01:
                    deltas.append(f"{name}: eW(ap4) {b_eh:.2f} → {m_eh:.2f} ({delta:+.2f})")
            else:  # mob
                if b["mob"] != m["mob"]:
                    b_tier = b["mob"].get("mobility_tier", "")
                    m_tier = m["mob"].get("mobility_tier", "")
                    b_mov = b["mob"].get("movement", "")
                    m_mov = m["mob"].get("movement", "")
                    deltas.append(f"{name}: {b_tier} ({b_mov}) → {m_tier} ({m_mov})")

        return deltas, only_inert

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_each_modifier_has_effect(self, faction):
        """Every modifier choice must actually change the output for at least one unit.

        Exceptions: modifiers that ONLY use inert fields (fields the engine doesn't apply yet).
        """
        eng = RankingEngine(faction)

        inert_only_issues = []
        real_issues = []
        for det in eng.list_detachments_with_modifiers():
            choices = eng.get_detachment_modifiers(det)
            for ci, c in enumerate(choices):
                deltas, only_inert = self._check_modifier_delta(faction, det, ci)
                if not deltas:
                    # Try with a different target
                    for alt_target in ["TEQ", "Light V", "GEQ"]:
                        if alt_target in eng.config.target_profiles:
                            deltas, only_inert = self._check_modifier_delta(faction, det, ci, alt_target)
                            if deltas:
                                break
                    if not deltas:
                        msg = f"{faction}/{det}/choice[{ci}] ({c.name}): no DPP/SURV/MOB delta (affects={c.affects})"
                        if only_inert:
                            inert_only_issues.append(msg)
                        else:
                            real_issues.append(msg)

        # Report inert-only issues as warning
        if inert_only_issues:
            print(f"\n  [INERT] {len(inert_only_issues)} modifiers use only inert fields:")
            for msg in inert_only_issues:
                print(f"    {msg}")

        assert not real_issues, "\n".join(real_issues[:10])

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_unit_filter_correctly_scopes(self, faction):
        """Unit-filtered modifiers should only affect matching units.

        Checks against both unit names and keywords. Only tests modifiers
        with NON-inert fields (fields the engine actually applies).
        """
        eng = RankingEngine(faction)
        all_units = list(eng.config.known_units)
        unit_kw_map = _all_unit_keywords(faction)

        issues = []
        for det in eng.list_detachments_with_modifiers():
            choices = eng.get_detachment_modifiers(det)
            for ci, c in enumerate(choices):
                if not c.unit_filter:
                    continue

                # Check if this modifier uses inert fields only — skip if so
                active_fields = {"affects"}
                if c.hit_modifier: active_fields.add("hit_modifier")
                if c.reroll_hits: active_fields.add("reroll_hits")
                if c.reroll_wounds: active_fields.add("reroll_wounds")
                if c.plus1_to_wound: active_fields.add("plus1_to_wound")
                if c.sustained_hits_extra: active_fields.add("sustained_hits_extra")
                if c.lethal_hits: active_fields.add("lethal_hits")
                if c.extra_ap: active_fields.add("extra_ap")
                if c.ignore_cover: active_fields.add("ignore_cover")
                if c.invulnerable_save: active_fields.add("invulnerable_save")
                if c.feel_no_pain: active_fields.add("feel_no_pain")
                if c.movement_bonus: active_fields.add("movement_bonus")
                inert_f = {"stealth", "cover_save", "advance_and_charge",
                           "fallback_and_shoot", "fallback_and_charge", "assault", "heavy_ignore",
                           "name", "unit_filter", "condition", "description"}
                active = active_fields - {"affects"}
                if active.issubset(inert_f):
                    continue  # skip — only inert fields

                # Units that should be affected (name OR keyword match)
                expected = set()
                for filt in c.unit_filter:
                    filt_upper = filt.upper()
                    for u in all_units:
                        if filt.lower() in u.lower():
                            expected.add(u)
                    for u, kws in unit_kw_map.items():
                        if filt_upper in kws:
                            expected.add(u)

                # Get the right metric key
                if c.affects == "dpp":
                    metric = "dpp"
                elif c.affects == "surv":
                    metric = "surv"
                else:
                    metric = "mob"

                # Run ranking with and without modifier
                base = eng.compute_ranking(target=eng.config.target_profiles.get("MEQ"))
                modded = eng.compute_ranking(
                    target=eng.config.target_profiles.get("MEQ"),
                    detachment=det,
                    detachment_choice=ci,
                )
                base_map = {r["name"]: r for r in base}
                mod_map = {r["name"]: r for r in modded}

                for name in base_map:
                    if name not in mod_map:
                        continue
                    b = base_map[name]
                    m = mod_map[name]
                    changed = b != m

                    # DPP modifiers can't affect units with no weapons (e.g. Fortifications)
                    if c.affects == "dpp" and not _unit_has_weapons(faction, name):
                        continue

                    if name in expected and not changed:
                        issues.append(
                            f"{faction}/{det}/choice[{ci}]: {name} should be affected (filter={c.unit_filter}) "
                            f"but all values unchanged"
                        )
                    elif name not in expected and changed:
                        # Only flag as "should NOT be affected" if the change is in the right affects domain
                        if c.affects == "dpp" and abs(m["dpp"] - b["dpp"]) > 0.0001:
                            issues.append(
                                f"{faction}/{det}/choice[{ci}]: {name} should NOT be affected "
                                f"(filter={c.unit_filter}) but dpp changed: {b['dpp']:.4f} → {m['dpp']:.4f}"
                            )
                        elif c.affects == "surv" and m["surv"] != b["surv"]:
                            issues.append(
                                f"{faction}/{det}/choice[{ci}]: {name} should NOT be affected "
                                f"(filter={c.unit_filter}) but surv changed"
                            )

        assert not issues, "\n".join(issues[:15])


# ═══════════════════════════════════════════════════════════════════════
# TIER 2.5: INERT FIELD DETECTION
# ═══════════════════════════════════════════════════════════════════════

class TestTier25InertFields:
    """Fields defined in JSON but NOT implemented in engine compute paths."""

    def test_identify_inert_fields(self):
        """Identify which modifier fields are stored but never applied by the engine.

        This does not fail — it reports. Inert fields are design debt.
        """
        eng = RankingEngine('grey-knights')  # any faction works

        import inspect
        sig = inspect.signature(DetachmentModifier.__init__)
        all_fields = set(sig.parameters.keys()) - {"self"}

        # Fields that ARE applied in compute_ranking:
        # DPP via to_weapon_modifier: hit_modifier, sustained_hits_extra, lethal_hits,
        #   reroll_hits, reroll_wounds, plus1_to_wound, extra_ap, ignore_cover
        # SURV in compute_ranking: invulnerable_save, feel_no_pain
        # MOB in compute_ranking: movement_bonus
        applied_dpp = {"hit_modifier", "sustained_hits_extra", "lethal_hits",
                       "reroll_hits", "reroll_wounds", "plus1_to_wound",
                       "extra_ap", "ignore_cover"}
        applied_surv = {"invulnerable_save", "feel_no_pain"}
        applied_mob = {"movement_bonus"}
        applied = applied_dpp | applied_surv | applied_mob
        # name, affects, unit_filter, condition are metadata, not effect fields
        metadata = {"name", "affects", "unit_filter", "condition"}

        inert = all_fields - applied - metadata
        assert inert == {
            "stealth", "cover_save",
            "advance_and_charge", "fallback_and_shoot", "fallback_and_charge",
            "assault", "heavy_ignore",
        }, f"Inert fields changed: {inert}"

        # Report which factions use inert fields
        all_inert_use = {}
        for faction in FACTIONS:
            data = _load_detachment_json(faction)
            for det_name, det_data in data.get("detachments", {}).items():
                for ci, c in enumerate(det_data.get("choices", [])):
                    for field in inert:
                        if field in c:
                            key = f"{faction}/{det_name}/choice[{ci}]"
                            all_inert_use.setdefault(field, []).append(key)

        if all_inert_use:
            report = ["INERT FIELDS USED (stored in JSON but NOT applied by engine):"]
            for field, locations in sorted(all_inert_use.items()):
                report.append(f"  {field}:")
                for loc in locations[:5]:  # cap at 5 per field
                    report.append(f"    - {loc}")
                if len(locations) > 5:
                    report.append(f"    ... and {len(locations)-5} more")
            pytest.skip("Inert fields: " + "\n".join(report))


# ═══════════════════════════════════════════════════════════════════════
# TIER 3: FORCE DISPOSITIONS
# ═══════════════════════════════════════════════════════════════════════

class TestTier3ForceDispositions:
    """Validate force disposition mapping and engine gating."""

    def test_ck_has_8_dispositions(self):
        """Chaos Knights must have exactly 8 disposition entries (one per detachment)."""
        from engine.ranking import RankingEngine
        eng = RankingEngine("chaos-knights")
        assert len(eng.config.dispositions) == 8, (
            f"Expected 8 dispositions, got {len(eng.config.dispositions)}: "
            f"{list(eng.config.dispositions.keys())}"
        )

    def test_all_disposition_values_are_valid(self):
        """Every disposition value must be one of the 5 valid IDs."""
        from engine.ranking import RankingEngine
        eng = RankingEngine("chaos-knights")
        for det, disp in eng.config.dispositions.items():
            assert disp in VALID_DISPOSITION_IDS, (
                f"Detachment '{det}' has invalid disposition '{disp}'. "
                f"Valid IDs: {VALID_DISPOSITION_IDS}"
            )

    def test_gk_dispositions_not_empty(self):
        """Grey Knights must also have dispositions loaded."""
        from engine.ranking import RankingEngine
        eng = RankingEngine("grey-knights")
        assert len(eng.config.dispositions) > 0, "Grey Knights dispositions empty"

    @pytest.mark.parametrize("detachment,expected_disposition", [
        ("infernal-lance", "purge-the-foe"),
        ("iconoclast-fiefdom", "take-and-hold"),
        ("bastions-of-tyranny", "disruption"),
        ("hunting-warpack", "reconnaissance"),
        ("lords-of-dread", "priority-assets"),
        ("traitoris-lance", "purge-the-foe"),
        ("helhunt-lance", "disruption"),
        ("houndpack-lance", "reconnaissance"),
    ])
    def test_ck_disposition_spot_checks(self, detachment, expected_disposition):
        """Spot-check each CK detachment maps to the right disposition."""
        from engine.ranking import RankingEngine
        eng = RankingEngine("chaos-knights")
        actual = eng.config.dispositions.get(detachment)
        assert actual == expected_disposition, (
            f"{detachment}: expected '{expected_disposition}', got '{actual}'"
        )

    def test_invalid_disposition_raises(self):
        """Using a detachment that can't play the given disposition must raise ValueError."""
        from engine.ranking import RankingEngine
        eng = RankingEngine("chaos-knights")
        with pytest.raises(ValueError, match="cannot be used"):
            eng.compute_ranking(
                detachment="INFERNAL LANCE",
                disposition="take-and-hold",
            )

    def test_valid_disposition_succeeds(self):
        """Using a valid detachment+disposition combo must not raise."""
        from engine.ranking import RankingEngine
        eng = RankingEngine("chaos-knights")
        results = eng.compute_ranking(
            detachment="INFERNAL LANCE",
            disposition="purge-the-foe",
        )
        assert isinstance(results, list)
        assert len(results) > 0

    def test_no_disposition_backward_compat(self):
        """compute_ranking without disposition must still work (backward compat)."""
        from engine.ranking import RankingEngine
        eng = RankingEngine("chaos-knights")
        results = eng.compute_ranking(detachment="INFERNAL LANCE")
        assert isinstance(results, list)
        assert len(results) > 0

    def test_get_detachments_for_disposition(self):
        """get_detachments_for_disposition returns the right detachments."""
        from engine.ranking import RankingEngine
        eng = RankingEngine("chaos-knights")
        purge_dets = eng.config.get_detachments_for_disposition("purge-the-foe")
        assert set(purge_dets) == {"infernal-lance", "traitoris-lance"}

    def test_can_detachment_play_disposition(self):
        """can_detachment_play_disposition works with kebab-case and space-separated names."""
        from engine.ranking import RankingEngine
        eng = RankingEngine("chaos-knights")
        assert eng.config.can_detachment_play_disposition("infernal-lance", "purge-the-foe")
        assert eng.config.can_detachment_play_disposition("INFERNAL LANCE", "purge-the-foe")
        assert not eng.config.can_detachment_play_disposition("infernal-lance", "take-and-hold")

    def test_compute_disposition_ranking(self):
        """compute_disposition_ranking evaluates all valid detachments for a disposition."""
        from engine.ranking import RankingEngine
        eng = RankingEngine("chaos-knights")
        results = eng.compute_disposition_ranking("purge-the-foe")
        assert isinstance(results, dict)
        # Should have 2 entries: infernal-lance and traitoris-lance
        assert len(results) == 2, f"Expected 2 detachments, got {len(results)}: {list(results.keys())}"
        for det_name, r in results.items():
            assert isinstance(r, list), f"{det_name}: expected list, got {type(r)}"
