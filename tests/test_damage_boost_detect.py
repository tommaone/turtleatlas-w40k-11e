"""Regression locks for the conditional damage-boost detector.

The "Rend and Tear class": abilities that improve ONLY the Damage
characteristic against a target class (Monster/Vehicle/Titanic).

Each phrasing variant is a regression probe — these all broke before.
The pure-damage gate is the epistemic boundary: mixed boosts (S/AP+D in
one clause, e.g. Tor Garadon's Siege Captain) are REJECTED rather than
partially modeled, because a D-component-only claim would misrepresent
the ability's damage output.

STRUCTURE ONLY — no damage values. The engine is the single source of
computation; this test locks the detector's parse decisions.

Run: python3 -m pytest tests/test_damage_boost_detect.py -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.damage_boost_detect import detect_damage_boost


def _spec(desc, name="Ability"):
    return detect_damage_boost({"name": name, "description": desc})


class TestPhrasingVariants:
    """Each phrasing variant is a regression probe — these all broke before."""

    def test_rend_and_tear_melee(self):
        """World Eaters Exalted Eightbound: melee-only, +1 vs MONSTER/VEHICLE."""
        s = _spec("Each time a model in this unit makes a melee attack that "
                  "targets a Monster or Vehicle unit, until the end of the "
                  "phase, improve the Damage characteristic of that attack by 1.",
                  "Rend and Tear")
        assert s is not None
        assert s["amount"] == 1
        assert s["phase"] == "melee"
        assert "MONSTER" in s["targets"] and "VEHICLE" in s["targets"]

    def test_add_one_to_damage(self):
        """Orks Mozrog 'Da Bigger Dey Iz…': 'add 1 to the Damage characteristic'
        — active verb form, no phase qualifier → both."""
        s = _spec("Each time this model makes an attack that targets a Monster "
                  "or Vehicle unit, add 1 to the Damage characteristic of that "
                  "attack. Each time this model makes an attack that targets a "
                  "Titanic unit, add 2 to the Damage characteristic of that "
                  "attack instead.",
                  "Da Bigger Dey Iz\u2026")
        assert s is not None
        assert s["amount"] == 1          # conservative: min of the clauses
        assert s["phase"] == "both"
        assert "MONSTER" in s["targets"] and "TITANIC" in s["targets"]

    def test_increase_by_two(self):
        """'increase the Damage characteristic of that attack by 2' → amount 2."""
        s = _spec("Each time this model makes an attack that targets a Vehicle "
                  "unit, increase the Damage characteristic of that attack by 2.",
                  "Big Boom")
        assert s is not None
        assert s["amount"] == 2
        assert s["targets"] == ["VEHICLE"]

    def test_passive_is_increased(self):
        """'the Damage characteristic ... is increased by 1' — passive form."""
        s = _spec("Each time this model makes a melee attack that targets a "
                  "Monster unit, the Damage characteristic of that attack is "
                  "increased by 1.",
                  "Monster Hunter")
        assert s is not None
        assert s["amount"] == 1
        assert s["phase"] == "melee"

    def test_ranged_only_boost(self):
        """Shooting-phase wording classifies as ranged, not both."""
        s = _spec("Each time this unit is selected to shoot, while it is "
                  "targeting a Vehicle unit, improve the Damage characteristic "
                  "of its attacks by 1.",
                  "Tank Bustas")
        assert s is not None
        assert s["phase"] == "ranged"
        assert s["targets"] == ["VEHICLE"]


class TestPureDamageGate:
    """Mixed boosts (S/AP+D in one clause) are REJECTED, not partially modeled.

    Modeling the D-component of a mixed boost is false precision: the engine
    would claim '+2 damage' while silently ignoring the S+2/AP+2 that are
    half the point of the ability.
    """

    def test_strength_ap_and_damage_rejected(self):
        """Tor Garadon 'Siege Captain': Strength, AP AND Damage → reject."""
        s = _spec("Each time this model makes an attack that targets a Monster, "
                  "Vehicle, or Fortification unit, improve the Strength, Armour "
                  "Penetration and Damage characteristics of that attack by 2.",
                  "Siege Captain")
        assert s is None

    def test_strength_and_damage_rejected(self):
        """Acastus Knight Asterius 'Sunderer of Fortresses': Strength AND Damage
        → reject (the S+1 changes wound rolls; D+1 alone misrepresents it)."""
        s = _spec("Each time this model makes an attack that targets a Vehicle, "
                  "improve the Strength and Damage characteristics of that "
                  "attack by 1.",
                  "Sunderer of Fortresses")
        assert s is None


class TestNegative:
    """Cases that must NOT produce a damage-boost spec."""

    def test_no_amount(self):
        """'improve the Damage characteristic' without 'by N' → no spec."""
        s = _spec("Each time this model makes an attack that targets a Monster "
                  "unit, improve the Damage characteristic of that attack.")
        assert s is None

    def test_no_damage_mention(self):
        """Ability with no damage improvement at all → no spec."""
        s = _spec("This model can be attached to the following unit: "
                  "- Aggressor Squad", "Leader")
        assert s is None

    def test_aura_grant_other_subject(self):
        """Boost granted to OTHER units (friendly unit attacks) → no spec."""
        s = _spec("Each time a friendly unit makes an attack that targets a "
                  "Monster or Vehicle unit, add 1 to the Damage characteristic "
                  "of that attack.",
                  "Aura of Gore")
        assert s is None

    def test_no_target_class(self):
        """'targets a unit' (generic) — no class keyword → no spec."""
        s = _spec("Each time this model makes an attack that targets a unit, "
                  "improve the Damage characteristic of that attack by 1.")
        assert s is None

    def test_reroll_damage_is_not_a_boost(self):
        """'re-roll the Damage roll' changes variance, not the characteristic."""
        s = _spec("Each time this model makes a melee attack, you can re-roll "
                  "the Damage roll.", "Furious")
        assert s is None
