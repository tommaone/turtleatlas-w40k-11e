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
# Context phrases that mention a keyword as a CONDITION, not the target class:
# "within Engagement Range of one or more friendly ADEPTUS ASTARTES VEHICLE
# units" — the VEHICLE there is the friendly unit the target must be near,
# NOT the class of unit the reroll keys off. If we scanned it as a target,
# the reroll would fire on every monster/vehicle instead of only enemies
# adjacent to our transports (Judgement of the Omnissiah false positive).
_RE_CONTEXT_TOKEN = re.compile(r"\bfriendly\b", re.I)
_RE_CONTEXT_EXCLUDING = re.compile(r"\bexcluding\b", re.I)
# "within ... of" is a context cue ONLY when it names a nearby *entity* the
# target must be next to ("within Engagement Range of one or more friendly
# VEHICLE units"). A bare range condition ("targets a unit within 6\" of this
# model and that unit is a MONSTER") is NOT context — the MONSTER is the
# target. The proximity companion ("friendly"/"one or more") separates them.
_RE_WITHIN_OF = re.compile(
    r"\bwithin\b[^.]{0,120}?\bof\b[^.]{0,40}?(?:friendly|one\s+or\s+more)\b", re.I
)


def _target_keywords(desc: str) -> list[str]:
    """Target-class keywords the reroll keys off (from the description text).

    - "friendly ADEPTUS ASTARTES VEHICLE units" (the transports the enemy
        must be near — Judgement of the Cruel)
      - "excluding MONSTERS and VEHICLES" (the reroll fires on everything
        EXCEPT them — Mek Gunz Splat!)
      - "within N\\" of one or more friendly VEHICLE units" (proximity to
        friendly transports — bare "within 6\\\" of this model" is only a
        RANGE condition and does NOT mark the keyword as context) 
    Treating these as targets would fire the reroll on every monster/vehicle
    instead of the rule's real trigger.

    Per-occurrence check: one contextual mention must not wipe a GENUINE
    target-class mention in the same sentence ("targets a MONSTER or VEHICLE").
    """
    out = []
    for kw in _TARGET_KEYWORDS:
        # Allow both singular ("MONSTER") and plural ("MONSTERS") mentions.
        pat = rf"\b{kw.lower()}s?\b"
        for m in re.finditer(pat, desc.lower()):
            # Look back to the start of the clause (sentence boundary), but cap
            # the window — a context cue must be NEAR the keyword, or a genuine
            # far target in the same sentence gets masked.
            head = desc.lower()[:m.start()]
            cut = max(head.rfind(ch) for ch in (".", "!", "?", ";")) + 1
            window = head[cut:]
            if len(window) > 60:
                window = window[-60:]
            ctx = (_RE_CONTEXT_TOKEN.search(window)
                   or _RE_CONTEXT_EXCLUDING.search(window)
                   or _RE_WITHIN_OF.search(window))
            if ctx:
                continue  # contextual mention — not a target class
            out.append(kw)
            break
    return out


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
    # Only class keywords count: "friendly"/"excluding"/"within ... of"
    # mentions are the surrounding rule context, not the target — see
    # _target_keywords. If every mention was context, return None; there is
    # NEVER a default target class (that would fabricate a rule).
    targets = _target_keywords(desc)
    if not targets:
        return None

    return {
        "reroll_hits": hits,
        "reroll_wounds": wounds,
        "reroll_damage": dmg,
        "phase": phase,
        "targets": targets,
        "ability_name": name,
        "raw": desc,
    }


def _target_matches(spec_targets, toughness: int) -> bool:
    """Does a target profile's toughness fall under any spec'd keyword?"""
    from engine.dpp import _anti_keyword_matches
    return any(_anti_keyword_matches(kw, toughness) for kw in spec_targets)