"""Tests for reroll-vs-MONSTER/VEHICLE auto-detection and the damage-reroll math.

Covers the phrasing variants that broke the naive parser:
  - single verb, multiple objects ("re-roll a Hit roll and a Wound roll")
  - per-noun "of 1" attachment ("hit all, wound of 1")
  - phase detection: melee-only, ranged-only (via "shoot"/"shooting phase"),
    and both
  - numeric honesty of _damage_reroll_mean (D6 all-reroll = 4.25,
    reroll-1s = 3.9167, flat = 3.5)

Expected means come from the standard expectation formula, pinned as engine
truth:
  E[D6 all-reroll] = (4+5+6)/6 + (1+2+3)/6 * 3.5 = 4.25
  E[D6 reroll 1s]  = (2+3+4+5+6)/6 + (1/6) * 3.5 = 3.9167
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.dpp import _damage_reroll_mean
from engine.reroll_detect import detect_reroll_ability, _target_matches


# ── Parser: reroll structs ────────────────────────────────────────────

def _spec(desc, name="Ability"):
    return detect_reroll_ability({"name": name, "description": desc})


class TestPhrasingVariants:
    """Each phrasing variant is a regression probe — these all broke before."""

    def test_surge_melee_all_three(self):
        """GMNDK Surge of Wrath: melee-only, full hit/wound/damage reroll."""
        s = _spec("Each time this model makes a melee attack that targets a "
                  "Monster or Vehicle unit, you can re-roll the Hit roll, you "
                  "can re-roll the Wound roll and you can re-roll the Damage roll.",
                  "Surge of Wrath (Psychic)")
        assert s is not None
        assert s["reroll_hits"] == "all"
        assert s["reroll_wounds"] == "all"
        assert s["reroll_damage"] == "all"
        assert s["phase"] == "melee"
        assert "MONSTER" in s["targets"] and "VEHICLE" in s["targets"]

    def test_single_verb_two_objects(self):
        """'re-roll a Hit roll and a Wound roll' — one verb, both objects."""
        s = _spec("Each time this unit makes a ranged attack, you can re-roll "
                  "a Hit roll and a Wound roll. Each time this unit makes an "
                  "attack that targets a Monster or Vehicle unit, you can "
                  "re-roll a Damage roll of 1.")
        assert s is not None
        assert s["reroll_hits"] == "all"
        assert s["reroll_wounds"] == "all"
        assert s["reroll_damage"] == "1s"
        assert s["phase"] == "ranged"

    def test_per_noun_of_one_attachment(self):
        """'of 1' must attach to its OWN noun, not bleed from a later clause."""
        s = detect_reroll_ability({"name": "Mixed", "description":
            "Each time this model shoots, you can re-roll a hit roll and a "
            "wound roll of 1. If that attack targets a Monster or Vehicle "
            "unit..."})
        assert s is not None
        assert s["reroll_hits"] == "all"   # hit roll is not 'of 1'
        assert s["reroll_wounds"] == "1s"  # only the wound roll is

    def test_shoot_phrase_is_ranged(self):
        """'selected to shoot' must classify as ranged, not both."""
        s = detect_reroll_ability({"name": "Tank Hunter", "description":
            "Each time this unit is selected to shoot, you can re-roll the "
            "hit roll and the wound roll. Each time this unit makes an attack "
            "that targets a Monster or Vehicle unit, you can re-roll the "
            "Damage roll."})
        assert s is not None
        assert s["phase"] == "ranged"
        assert s["reroll_hits"] == "all"
        assert s["reroll_wounds"] == "all"
        assert s["reroll_damage"] == "all"

    def test_fight_phrase_is_melee(self):
        """'each time this model fights' must classify as melee, not both."""
        s = detect_reroll_ability({"name": "Furious", "description":
            "Each time this model fights, you can re-roll the Hit roll and "
            "the Wound roll. Each time this model makes an attack that "
            "targets a Monster or Vehicle unit, you can re-roll the Damage "
            "roll."})
        assert s is not None
        assert s["phase"] == "melee"
        assert s["reroll_hits"] == "all"
        assert s["reroll_wounds"] == "all"
        assert s["reroll_damage"] == "all"

    def test_both_phases(self):
        s = _spec("Each time this model makes an attack that targets a "
                  "Character, Monster or Vehicle unit, you can re-roll the "
                  "Wound roll.")
        assert s is not None
        assert s["phase"] == "both"
        assert s["reroll_wounds"] == "all"
        assert s["reroll_hits"] is None

    def test_irrelevant_ability_returns_none(self):
        assert _spec("Aura: friendly units within 6\" get +1 to hit.") is None

    def test_no_rereoll_returns_none(self):
        """Monster/Vehicle mention but no re-roll -> not a reroll ability."""
        assert _spec("This unit can target a Monster or Vehicle even when it "
                     "is in melee.") is None


class TestContextKeywordFalsePositives:
    """KW in a context phrase is a CONDITION, not the target class — must not
    become a pseudo-target (filed follow-up from Shredder pass 1)."""

    def test_friendly_vehicle_is_context(self):
        """Judgement of the Omnissiah: 'friendly VEHICLE units' is the proximity
        condition, not the reroll class — engine must NOT grant the reroll vs
        every vehicle."""
        s = detect_reroll_ability({"name": "Judgement of the Omnissiah",
            "description": "Each time this model makes an attack that targets "
            "an enemy unit within Engagement Range of one or more friendly "
            "VEHICLE units, you can re-roll the wound roll."})
        assert s is None

    def test_excluding_vehicle_is_context(self):
        """Mek Gunz Splat!: the reroll fires on units at Starting Strength
        EXCLUDING monsters/vehicles — the M/V mention is an exclusion."""
        s = _spec("Each time a model in this unit makes a ranged attack that "
                  "targets a unit that is at its Starting Strength (excluding "
                  "MONSTERS and VEHICLES), re-roll a Hit roll of 1.")
        assert s is None

    def test_genuine_target_survives_context_in_same_text(self):
        """Lokhust Heavy Destroyers: one clause excludes M/V, the NEXT clause
        genuinely targets them — the per-occurrence check must keep the real
        class while ignoring the exclusion."""
        s = _spec("Each time a model in this unit makes an attack with an "
                  "enmitic exterminator that targets a unit (excluding MONSTERS "
                  "and VEHICLES), re-roll a Wound roll of 1. Each time a model "
                  "in this unit makes an attack with a gauss destructor against "
                  "a MONSTER or VEHICLE unit, re-roll a Wound roll of 1.")
        assert s is not None
        assert "MONSTER" in s["targets"] and "VEHICLE" in s["targets"]

    def test_far_genuine_target_not_masked(self):
        """A 'friendly/within' cue early in the sentence must not mask a real
        M/V target later in the same sentence."""
        s = _spec("If a friendly VEHICLE unit is within 6\", each time this "
                  "model makes an attack that targets a MONSTER or VEHICLE "
                  "unit, you can re-roll the Wound roll.")
        assert s is not None
        assert "MONSTER" in s["targets"] and "VEHICLE" in s["targets"]

    def test_plural_keyword_matches(self):
        """Descriptions say 'MONSTERS and VEHICLES' (plural) — singleton regex
        must still hit them."""
        s = detect_reroll_ability({"name": "Pl", "description":
            "Each time this model makes an attack that targets a Monster or "
            "Vehicle unit, you can re-roll the Hit roll."})
        assert s is not None
        assert "MONSTER" in s["targets"] and "VEHICLE" in s["targets"]

    def test_all_mentions_context_returns_none(self):
        """Every M/V mention is context — the reroll is a proximity/exclusion
        trigger, not a class reroll. Must return None (no default class)."""
        s = _spec("Each time this unit makes an attack that targets an enemy "
                  "unit within Engagement Range of one or more friendly "
                  "MONSTER or VEHICLE units, you can re-roll the Wound roll. "
                  "Each time this model makes an attack (excluding MONSTERS "
                  "and VEHICLES), you can re-roll the Hit roll.")
        assert s is None


class TestRangeConditionNotContext:
    """A bare 'within X of this model' is a RANGE condition, not a
    friendly-context phrase — the class keyword after it is still the target.
    ('within ... of one or more friendly VEHICLE' IS context, see above.)"""

    def test_range_then_class(self):
        s = _spec("Each time this unit makes an attack against a unit within "
                  "6\" of this model and that unit is a MONSTER or VEHICLE, "
                  "you can re-roll the Hit roll.")
        assert s is not None
        assert "MONSTER" in s["targets"] and "VEHICLE" in s["targets"]

    def test_range_then_class_reverse_order(self):
        s = _spec("Each time this model makes an attack that targets a unit "
                  "within half range of this model's weapon and that unit is "
                  "a MONSTER, you can re-roll the Wound roll.")
        assert s is not None
        assert "MONSTER" in s["targets"]

    def test_class_then_range_kept(self):
        s = _spec("Each time this model makes an attack that targets a "
                  "MONSTER or VEHICLE unit within 12\" of this model, you can "
                  "re-roll the Hit roll.")
        assert s is not None
        assert "MONSTER" in s["targets"] and "VEHICLE" in s["targets"]


# ──(Parser: target matching ──────────────────────────────────────────

class TestTargetMatching:
    def test_monster_vehicle_range(self):
        assert _target_matches(["VEHICLE"], 11)
        assert _target_matches(["MONSTER"], 8)
        assert not _target_matches(["VEHICLE"], 5)   # below vehicle T6
        assert _target_matches(["MONSTER"], 6)      # (6,12) — 6 is in range
        assert not _target_matches(["MONSTER"], 5)  # below monster T6
        assert _target_matches(["INFANTRY"], 4)      # (3,5) range
        assert _target_matches(["CHARACTER"], 10)    # (3,10) range
        assert not _target_matches(["CHARACTER"], 11)

    def test_any_keyword_wins(self):
        assert _target_matches(["MONSTER", "VEHICLE"], 12)
        assert _target_matches(["MONSTER", "VEHICLE"], 6)


# ──(damage-reroll math ────────────────────────────────────────────────

# Pinned from the expectation formulas (single source of truth, see docstring).
ALL_FACTOR = 4.25 / 3.5
ONES_FACTOR = (2 + 3 + 4 + 5 + 6 + 3.5) / 6 / 3.5


class TestDamageRerollMean:
    @pytest.mark.parametrize("raw, mode, expected", [
        ("D6", "all", pytest.approx(4.25 / 3.5)),
        ("D6", "1s", pytest.approx(ONES_FACTOR)),
        ("D6", None, 1.0),
        ("D6+1", "all", pytest.approx(5.25 / 4.5)),
        ("D3", "all", pytest.approx(7 / 6)),       # E: (2+3+2)/3 / 2 = 7/6
        ("D3", "1s", pytest.approx(7 / 6)),        # reroll-1s same for D3
        ("2D6", "all", pytest.approx(4.25 / 3.5)),     # count-scaled, per die
        ("1", None, 1.0),          # flat
        ("3", "all", 1.0),         # flat damage can't be rerolled up
    ])
    def test_factor(self, raw, mode, expected):
        assert _damage_reroll_mean(raw, mode) == expected

    def test_known_means(self):
        """Spot-check the means the engine will present (not recomputed)."""
        assert _damage_reroll_mean("D6", "all") * 3.5 == pytest.approx(4.25, abs=1e-3)
        assert _damage_reroll_mean("D6", "1s") * 3.5 == pytest.approx(3.9167, abs=1e-3)
        assert _damage_reroll_mean("D3", "all") * 2.0 == pytest.approx(2.3333, abs=1e-3)

    def test_unrecognised_shape_returns_flat(self):
        """Unknown dice expressions fall back to flat (no silent boost)."""
        assert _damage_reroll_mean("D12", "all") == 1.0


class TestGeneralizedKeywords:
    """Beyond MONSTER/VEHICLE: CHARACTER / INFANTRY / TITANIC / WALKER / MOUNTED
    rerolls are now detected too (previously gated on M/V only)."""

    def test_character_reroll_detected(self):
        s = _spec("Each time this model makes an attack that targets a "
                  "Character unit, you can re-roll the Wound roll.",
                  "Storm of Silence")
        assert s is not None
        assert s["reroll_wounds"] == "all"
        assert s["targets"] == ["CHARACTER"]

    def test_titanic_reroll_detected(self):
        s = _spec("Each time this model makes a ranged attack that targets a "
                  "Titanic or Towering unit, you can re-roll the Hit roll.",
                  "Titan-killer")
        assert s is not None
        assert s["reroll_hits"] == "all"
        assert s["targets"] == ["TITANIC"]  # Towering is not a class keyword

    def test_walker_keyword_detected(self):
        s = _spec("Each time this model makes an attack that targets a "
                  "Character, Monster or Walker unit, you can re-roll the Hit "
                  "roll and re-roll the Wound roll.", "A Challenge Worthy of Skill")
        assert s is not None
        assert s["reroll_hits"] == "all" and s["reroll_wounds"] == "all"
        assert set(s["targets"]) == {"CHARACTER", "MONSTER", "WALKER"}


class TestUpgradeClauseWeakestWins:
    """'re-roll a 1s ... if target is X, re-roll instead' — the common-case
    mode stays '1s' (under-claim) instead of jumping to a full reroll for the
    whole class (over-claim)."""

    def test_upgrade_stays_ones(self):
        s = _spec("Each time this model makes an attack, re-roll a Hit roll of "
                  "1. If that attack targets a Monster or Vehicle unit, you can "
                  "re-roll the Hit roll instead.")
        assert s is not None
        assert s["reroll_hits"] == "1s"

    def test_permissive_upgrade_keeps_ones(self):
        """Hunter of Souls pattern: 'can re-roll the Hit roll' upgrade for
        Psyker-Characters must not leak 'all' onto plain Characters."""
        s = _spec("Each time this model makes an attack that targets a "
                  "Character unit, re-roll a Hit roll of 1 and re-roll a Wound "
                  "roll of 1. If that attack targets a Psyker Character unit, "
                  "you can re-roll the Hit roll and the Wound roll.",
                  "Hunter of Souls")
        assert s is not None
        assert s["reroll_hits"] == "1s"
        assert s["reroll_wounds"] == "1s"


class TestAuraGrantSkip:
    """A reroll granted to OTHER friendly units (subject 'that X model/unit')
    must NOT be attached to the bearer — over-claim."""

    def test_aura_grant_not_bearer(self):
        s = _spec("While a friendly War Dog model is within 6\" of this model, "
                  "each time that War Dog model makes an attack that targets a "
                  "TITANIC or TOWERING unit, you can re-roll the Hit roll.",
                  "Consumed with Hunger (Aura)")
        assert s is None

    def test_friendly_including_bearer_kept(self):
        """'a friendly Heretic Astartes model' includes the bearer (the model
        is Heretic Astartes) — keep the reroll."""
        s = _spec("At the start of your Shooting phase, select one visible "
                  "enemy Vehicle unit. Until the end of the phase, each time a "
                  "friendly Heretic Astartes model makes an attack that targets "
                  "that unit, re-roll a Wound roll of 1.", "Spirit Thief")
        assert s is not None
        assert s["reroll_wounds"] == "1s"
        assert "VEHICLE" in s["targets"]


class TestKeywordBoundaryNoPluralLeak:
    """[DEVASTATING WOUNDS] / [SUSTAINED HITS] keywords are NOT roll nouns — a
    keyword's 'wound'/'hit' must not be parsed as a rerollable roll."""

    def test_devastating_wounds_not_a_wound_reroll(self):
        s = _spec("Each time this unit declares a charge, this unit can "
                  "re-roll that charge roll. In the Fight phase, if this unit "
                  "is engaged with a CHARACTER unit, this unit's melee attacks "
                  "have [DEVASTATING WOUNDS] and [SUSTAINED HITS 1].",
                  "Sigismund's Heir")
        assert s is None

    def test_hits_wounds_plural_not_matched(self):
        s = _spec("Each time this model destroys an enemy unit, add 1 to this "
                  "unit's WOUNDS characteristic and gain [SUSTAINED HITS 2].")
        assert s is None
        assert _damage_reroll_mean("melta", "all") == 1.0