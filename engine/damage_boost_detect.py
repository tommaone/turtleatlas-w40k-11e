"""Auto-detection of unit abilities that improve damage vs target classes.

The "Rend and Tear class": "Each time a model in this unit makes a melee
attack that targets a Monster or Vehicle unit, until the end of the phase,
improve the Damage characteristic of that attack by 1."

Mirrors reroll_detect.py: parses the merged BSData ability DESCRIPTION and
derives a conditional damage boost. Data-driven — no hardcoded unit names;
any faction's equivalent (Rend and Tear, +1 damage vs MONSTER/VEHICLE
abilities, etc.) is covered automatically.

Epistemic boundary (dojo): the parser derives the MECHANIC (how much damage,
which phase, which target type) from GW text — interpretation, so it is
conservative: it only claims a boost when the text is unambiguous, it takes
the SMALLEST amount found (under-claiming beats over-claiming), and it
always carries a `raw` string so a human can verify what was detected.

Returned spec shape:
    {
      "amount": 1,
      "targets": ["MONSTER", "VEHICLE"],
      "phase": "melee"|"ranged"|"both",
      "ability_name": "Rend and Tear",
      "raw": "<full description text>",
    }
Returns None when no class-keyed damage improvement is present.
"""
import re

from engine.reroll_detect import _target_keywords, _RE_OTHER_SUBJECT

# "improve the Damage characteristic of that attack by 1" (active verb first)
_RE_IMPROVE = re.compile(
    r"\bimprove\b[^.;]{0,120}?\bdamage\b[^.;]{0,60}?\bby\s+(\d+)\b", re.I
)
# "increase the Damage characteristic ... by 1" (active verb first)
_RE_INCREASE = re.compile(
    r"\bincrease\b[^.;]{0,120}?\bdamage\b[^.;]{0,60}?\bby\s+(\d+)\b", re.I
)
# "add 1 to the Damage characteristic"
_RE_ADD_TO = re.compile(
    r"\badd\s+(\d+)\s+to\b[^.;]{0,80}?\bdamage\b", re.I
)
# "... the Damage characteristic ... is increased by 1" (passive)
_RE_PASSIVE = re.compile(
    r"\bdamage\b[^.;]{0,100}?\bis\s+increased\s+by\s+(\d+)\b", re.I
)

# Pre-filter: an attack-keyed damage improvement must at least mention
# damage. (Target-class gating happens via _target_keywords below.)
_RE_HAS_DAMAGE = re.compile(r"\bdamage\b", re.I)

# PURE-DAMAGE gate: reject clauses that ALSO boost Strength or Armour
# Penetration ("improve the Strength, Armour Penetration and Damage
# characteristics by 2" — Tor Garadon's Siege Captain, Sunderer of
# Fortresses). Modeling the D-component of a mixed boost is false
# precision: the engine would claim "+2 damage" while silently ignoring
# the S+2/AP+2 that are half the point. The engine claims exactly what
# the text supports; mixed boosts are a documented known issue, not a
# partial model. (Description-level guard: conservative by design —
# under-claiming beats over-claiming.)
_RE_MIXED = re.compile(
    r"\bstrength\b|\barmou?r penetration\b|\barmour-piercing\b|\bap\b", re.I
)

_RE_MELEE = re.compile(r"\bmelee\b|\bfights?\b|Fight phase", re.I)
_RE_RANGED = re.compile(r"\branged\b|shooting phase|\bshoot(?:s|ing)?\b", re.I)


def _amount(desc: str) -> int | None:
    """Smallest explicit boost amount found (conservative: under-claiming
    beats over-claiming when a text carries multiple conditional clauses)."""
    amounts = []
    for pat in (_RE_IMPROVE, _RE_INCREASE, _RE_ADD_TO, _RE_PASSIVE):
        amounts.extend(int(m.group(1)) for m in pat.finditer(desc))
    return min(amounts) if amounts else None


def detect_damage_boost(ability: dict) -> dict | None:
    """Parse one ability dict from merged data into a damage-boost spec (or None)."""
    name = ability.get("name", "")
    desc = ability.get("description", "") or ""
    if not desc or not _RE_HAS_DAMAGE.search(desc):
        return None

    amount = _amount(desc)
    if amount is None:
        return None

    # Pure-damage gate: a mixed boost (S/AP+D in one clause) is rejected.
    # The D-component alone would misrepresent the ability's damage output.
    if _RE_MIXED.search(desc):
        return None

    # Aura-grant abilities ("each time that <other> model makes an attack",
    # "each time a friendly unit makes an attack") hand the boost to other
    # units, not the bearer — skip entirely.
    if _RE_OTHER_SUBJECT.search(desc):
        return None

    # Which target keywords the boost keys off (from the description text).
    # Contextual mentions ("friendly VEHICLE units", "excluding MONSTERS")
    # are filtered by _target_keywords — never a default target class.
    targets = _target_keywords(desc)
    if not targets:
        return None

    if _RE_MELEE.search(desc) and not _RE_RANGED.search(desc):
        phase = "melee"
    elif _RE_RANGED.search(desc) and not _RE_MELEE.search(desc):
        phase = "ranged"
    else:
        phase = "both"

    return {
        "amount": amount,
        "targets": targets,
        "phase": phase,
        "ability_name": name,
        "raw": desc,
    }
