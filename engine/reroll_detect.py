"""Auto-detection of unit abilities that grant re-rolls vs MONSTER/VEHICLE.

The engine is data-driven: it should not hardcode "Grand Master In Nemesis
Dreadknight has Surge of Wrath". Instead it parses the ability DESCRIPTION
from the merged BSData and derives a conditional reroll modifier. This keeps
a single source of truth (the datasheet text) and automatically covers any
faction's equivalent abilities (Eradicators, Fire Dragons, Sunforge, etc.).

Epistemic boundary (dojo): the parser derives the MECHANIC (which rerolls,
which phase, which target type) from GW text — that is interpretation, so the
logic is conservative: it only claims a reroll when the text is unambiguous,
and it always carries a `condition` string in the returned spec so any human
triaging the report can see exactly what was detected.

Returned spec shape:
    {
      "reroll_hits": "all"|"1s"|None,
      "reroll_wounds": "all"|"1s"|None,
      "reroll_damage": "all"|"1s"|None,
      "phase": "ranged"|"melee"|"both",
      "targets": ["MONSTER", "VEHICLE"] | ["CHARACTER", "MONSTER", "VEHICLE"] ...,
      "ability_name": "Surge of Wrath",
      "raw": "<full description text>",
    }
Returns None when no Monster/Vehicle reroll is present.
"""
import re

# Keywords the ability can target (uppercased, matched against toughness
# ranges via ANTI_KEYWORD_TOUGHNESS in dpp.py).
_TARGET_KEYWORDS = [
    "MONSTER", "VEHICLE", "CHARACTER", "INFANTRY", "TITANIC", "WALKER", "MOUNTED",
]

_RE_HAS_MV = re.compile(r"(monster|vehicle)", re.I)
# A re-roll verb — the START of a reroll clause. Clauses may list several
# rolls after one verb ("you can re-roll a Hit roll and a Wound roll").
_RE_REROLL_VERB = re.compile(r"\bre-?roll\b", re.I)
# A roll-type noun inside a reroll clause ("Hit roll", "wound roll", "damage").
_RE_ROLL_NOUN = re.compile(r"\b(hit|wound|damage)(?:\s+roll)?", re.I)
# "of 1" / "1s" attached to a single noun -> reroll 1s (not all).
_RE_ONES_PER_NOUN = re.compile(r"\b(of\s+1|1s)\b", re.I)
# melee/fight phrasing: "makes a melee attack", "fights", "in the Fight phase"
_RE_MELEE = re.compile(r"\bmelee\b|\bfights?\b|Fight phase", re.I)
# ranged/shooting phrasing: "ranged attack", "shooting phase", "selected to shoot"
_RE_RANGED = re.compile(r"\branged\b|shooting phase|\bshoot(?:s|ing)?\b", re.I)


def detect_reroll_ability(ability: dict) -> dict | None:
    """Parse one ability dict from merged data into a reroll spec (or None)."""
    name = ability.get("name", "")
    desc = ability.get("description", "") or ""
    if not desc or not _RE_HAS_MV.search(desc):
        return None

    # Only act when a reroll is present AND it is conditional on M/V targets.
    if not _RE_REROLL_VERB.search(desc):
        return None

    # Which rerolls does the text grant? Split into clauses, each starting at a
    # re-roll verb. One verb may govern several nouns ("you can re-roll a Hit
    # roll and a Wound roll") — every noun in the same clause gets the same
    # mode. The mode is "1s" only when "of 1"/"1s" is attached to THAT noun
    # (bounded by the next noun in the clause), otherwise "all".
    hits, wounds, dmg = None, None, None
    verbs = list(_RE_REROLL_VERB.finditer(desc))
    for i, vm in enumerate(verbs):
        start = vm.end()
        end = verbs[i + 1].start() if i + 1 < len(verbs) else len(desc)
        clause = desc[start:end]
        nouns = list(_RE_ROLL_NOUN.finditer(clause))
        for j, nm in enumerate(nouns):
            kind = nm.group(1).lower()
            seg_end = nouns[j + 1].start() if j + 1 < len(nouns) else len(clause)
            tail = clause[nm.end():seg_end]
            mode = "1s" if _RE_ONES_PER_NOUN.search(tail) else "all"
            if kind == "hit":
                hits = mode
            elif kind == "wound":
                wounds = mode
            elif kind == "damage":
                dmg = mode

    if hits is None and wounds is None and dmg is None:
        return None

    # Phase: melee-only (Surge of Wrath), ranged-only (Fire Dragons), or both.
    if _RE_MELEE.search(desc) and not _RE_RANGED.search(desc):
        phase = "melee"
    elif _RE_RANGED.search(desc) and not _RE_MELEE.search(desc):
        phase = "ranged"
    else:
        phase = "both"

    # Which target keywords the reroll keys off (from the description text).
    targets = [kw for kw in _TARGET_KEYWORDS
               if re.search(rf"\b{kw.lower()}", desc.lower())]

    return {
        "reroll_hits": hits,
        "reroll_wounds": wounds,
        "reroll_damage": dmg,
        "phase": phase,
        "targets": targets or ["MONSTER", "VEHICLE"],
        "ability_name": name,
        "raw": desc,
    }


def _target_matches(spec_targets, toughness: int) -> bool:
    """Does a target profile's toughness fall under any spec'd keyword?"""
    from engine.dpp import _anti_keyword_matches
    return any(_anti_keyword_matches(kw, toughness) for kw in spec_targets)