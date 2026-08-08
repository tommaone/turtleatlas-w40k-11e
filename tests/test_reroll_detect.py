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
        assert _damage_reroll_mean("melta", "all") == 1.0