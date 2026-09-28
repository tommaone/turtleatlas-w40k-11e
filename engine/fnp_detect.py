"""Detect a unit's Feel No Pain value.

Same prose-parsing job as reroll_detect / damage_boost_detect, for the one
modifier `data/config/*/supported.json` still derives from ability text: the
wound threshold a unit ignores. The datasheet states it as "Feel No Pain 2+",
but BSData splits that across the ability name and its description, and after
the merge-time derivation the description is gone — so the value has to be
derived while the text is still available and stored as `fnp`.

`scripts/gen_config.py` used to own this regex. It now imports
`parse_fnp_source` from here so there is one implementation: the merge derives
the field with it, and the config generator reads the field with it as a
fallback for hand-built ability dicts.
"""

import re

# Substrings that mark a text as a Feel No Pain-style wound-ignore statement.
FNP_KEYWORDS = ("feel no pain", "fnp", "disgusting resilience", "nurgling resilience")

# "2+", "3+" — the value is the digit immediately before the plus.
_RE_N_PLUS = re.compile(r"(\d)\+")

# Below 2 or above 6 is not a 11e wound-ignore threshold; treat it as no value
# rather than writing a nonsense number into config.
MIN_FNP, MAX_FNP = 2, 6


def parse_fnp_source(text: str) -> int | None:
    """The FNP value stated in `text`, or None if it states none."""
    if not isinstance(text, str) or not text:
        return None
    if not any(kw in text.lower() for kw in FNP_KEYWORDS):
        return None
    m = _RE_N_PLUS.search(text)
    if not m:
        return None
    val = int(m.group(1))
    return val if MIN_FNP <= val <= MAX_FNP else None


def detect_fnp(ability: dict) -> int | None:
    """The FNP value for one ability dict, preferring the merge-derived field.

    Name and description are searched together, because BSData splits the
    statement across them: the keyword in one, the "N+" in the other. Searching
    only the description misses "Feel No Pain" + "ignore 4+ wounds".
    """
    derived = ability.get("fnp")
    if derived is not None:
        return derived if isinstance(derived, int) else None
    return parse_fnp_source(
        f"{ability.get('name', '')} {ability.get('description') or ''}"
    )


def detect_fnp_from_abilities(abilities) -> int | None:
    """First FNP value found across an ability list (field or prose)."""
    if not isinstance(abilities, list):
        return None
    for ability in abilities:
        if isinstance(ability, dict):
            if (val := detect_fnp(ability)) is not None:
                return val
        elif isinstance(ability, str):
            if (val := parse_fnp_source(ability)) is not None:
                return val
    return None
