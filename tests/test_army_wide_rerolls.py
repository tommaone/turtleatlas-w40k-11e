"""Golden tests for army-wide (targets: ALL) reroll detection + application.

War plan Phase 1 gate. Three goldens required:
1. generic aura ("re-roll hit rolls of 1") — detected, applied always-on
2. positional aura ("within 6\" of an objective marker") — detected but
   positional=True, engine must NOT apply it
3. army-wide damage reroll — reroll_damage='all'

Plus exclusion probes for the false-positive classes found in the corpus
survey (charge/advance rolls, single rerolls, reanimation dice, conditional
target properties).

STRUCTURE/INVARIANT only — no inline damage numbers. Relative assertions
compare the SAME engine function with and without a spec, so there is one
source of computation.

Run: python3 -m pytest tests/test_army_wide_rerolls.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from engine.reroll_detect import detect_army_wide_reroll, detect_reroll_ability
from engine import ranking as ranking_mod


class TestDetectorGoldens:
    def test_generic_aura_hit_ones(self):
        spec = detect_army_wide_reroll({
            "name": "Pan-spectral Scanning",
            "description": "Each time a model in this unit makes a ranged "
                           "attack, re-roll a Hit roll of 1.",
        })
        assert spec is not None
        assert spec["reroll_hits"] == "1s"
        assert spec["reroll_wounds"] is None
        assert spec["targets"] == ["ALL"]
        assert spec["phase"] == "ranged"
        assert spec["positional"] is False

    def test_positional_aura_detected_but_flagged(self):
        spec = detect_army_wide_reroll({
            "name": "Hallowed Aura",
            "description": "While this model is within 6\" of an objective "
                           "marker, each time this model makes an attack you "
                           "can re-roll the Hit roll.",
        })
        assert spec is not None
        assert spec["positional"] is True

    def test_army_wide_damage_reroll(self):
        spec = detect_army_wide_reroll({
            "name": "Brutal Efficiency",
            "description": "Each time this model makes an attack, you can "
                           "re-roll the Damage roll.",
        })
        assert spec is not None
        assert spec["reroll_damage"] == "all"
        assert spec["phase"] == "both"

    def test_melee_only_wound_reroll(self):
        """Brother-Captain Eye of Judgement pattern."""
        spec = detect_army_wide_reroll({
            "name": "Eye of Judgement (Psychic)",
            "description": "Each time this model makes an attack, you can "
                           "re-roll the Wound roll.",
        })
        assert spec is not None
        assert spec["reroll_wounds"] == "all"
        assert spec["phase"] == "both"


class TestDetectorExclusions:
    def test_charge_roll_not_an_attack_reroll(self):
        assert detect_army_wide_reroll({
            "name": "Unstoppable Valour",
            "description": "You can re-roll Charge rolls made for this "
                           "model's unit.",
        }) is None

    def test_single_reroll_excluded(self):
        """'re-roll one Hit roll' has no honest mode — under-claim by skipping."""
        assert detect_army_wide_reroll({
            "name": "Crystal Matrix",
            "description": "Each time this model is selected to shoot, you "
                           "can re-roll one Hit roll and you can re-roll one "
                           "Wound roll when resolving this model's attacks.",
        }) is None

    def test_reanimation_dice_not_a_wound_roll(self):
        assert detect_army_wide_reroll({
            "name": "Their Number is Legion",
            "description": "Each time this unit's Reanimation Protocols "
                           "activate, you can re-roll the dice to see how "
                           "many wounds are regenerated.",
        }) is None

    def test_class_keyword_belongs_to_other_detector(self):
        desc = {"name": "X", "description":
                "Each time this model makes an attack that targets a unit "
                "that can Fly, you can re-roll the Hit roll."}
        # FLY is not in _TARGET_KEYWORDS, but 'can Fly' is a condition cue —
        # army-wide detector must flag it positional, never apply silently.
        spec = detect_army_wide_reroll(desc)
        assert spec is not None
        assert spec["positional"] is True

    def test_closest_eligable_is_conditional(self):
        spec = detect_army_wide_reroll({
            "name": "Decisive Destruction",
            "description": "Each time a model in this unit makes a ranged "
                           "attack that targets the closest eligible target, "
                           "re-roll a Hit roll of 1.",
        })
        assert spec is not None
        assert spec["positional"] is True

    def test_no_self_subject_skipped(self):
        assert detect_army_wide_reroll({
            "name": "Other Subject",
            "description": "Each time that War Dog model makes an attack, "
                           "you can re-roll the Hit roll.",
        }) is None


class TestEngineApplication:
    """The ALL-target spec must raise damage vs any target; positional must not.

    MEQ fixture comes from conftest — never inline target stats (duplicated
    truth). Relative assertions compare the SAME engine function with and
    without a spec, so numbers are engine-derived, not hand-computed.
    """

    def test_ld_dmg_monotonic_under_army_spec(self, MEQ, storm_bolter):
        ranged = [storm_bolter]
        base = ranking_mod._ld_dmg(ranged, [], [], MEQ, None)
        spec_all = {"reroll_hits": "all", "reroll_wounds": None,
                    "reroll_damage": None, "phase": "ranged",
                    "targets": ["ALL"], "positional": False}
        boosted = ranking_mod._ld_dmg_conditional(
            ranged, [], [], MEQ, None, {"targets": [], "phase": "neither"},
            "ranged", always_spec=spec_all)
        assert boosted > base

    def test_ones_spec_geq_base(self, MEQ, storm_bolter):
        ranged = [storm_bolter]
        base = ranking_mod._ld_dmg(ranged, [], [], MEQ, None)
        spec_1s = {"reroll_hits": "1s", "reroll_wounds": None,
                   "reroll_damage": None, "phase": "ranged",
                   "targets": ["ALL"], "positional": False}
        out = ranking_mod._ld_dmg_conditional(
            ranged, [], [], MEQ, None, {"targets": [], "phase": "neither"},
            "ranged", always_spec=spec_1s)
        assert out >= base

    def test_positional_spec_never_applies(self, MEQ, storm_bolter):
        ranged = [storm_bolter]
        base = ranking_mod._ld_dmg(ranged, [], [], MEQ, None)
        spec_pos = {"reroll_hits": "all", "reroll_wounds": None,
                    "reroll_damage": None, "phase": "ranged",
                    "targets": ["ALL"], "positional": True}
        out = ranking_mod._ld_dmg_conditional(
            ranged, [], [], MEQ, None, {"targets": [], "phase": "neither"},
            "ranged", always_spec=spec_pos)
        assert out == base

    def test_wrong_phase_spec_never_applies(self, MEQ, storm_bolter):
        """A melee-only army-wide reroll must not touch ranged damage."""
        ranged = [storm_bolter]
        base = ranking_mod._ld_dmg(ranged, [], [], MEQ, None)
        spec_melee = {"reroll_hits": "all", "reroll_wounds": None,
                      "reroll_damage": None, "phase": "melee",
                      "targets": ["ALL"], "positional": False}
        out = ranking_mod._ld_dmg_conditional(
            ranged, [], [], MEQ, None, {"targets": [], "phase": "neither"},
            "ranged", always_spec=spec_melee)
        assert out == base
