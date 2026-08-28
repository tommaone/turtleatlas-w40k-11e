"""Structural lock: no stray bare-duplicate fixed weapon entries.

A build's fixed list must not contain BOTH a suffixed profile (e.g.
"Manreaper - strike") AND a bare family name ("manreaper") that resolves
to the same catalog profile. Two weapons entries that load the same engine
profile double-count that weapon in the loadout (ranged lists are summed,
melee lists spam `m_counts`).

Legitimate exception: the bare name may be a DISTINCT catalog profile
(co-existing with the suffixed melee pair). Example: Avatar Of Khaine has
"The Wailing Doom" (Ranged Weapons profile) plus "The Wailing Doom - Strike"
and "- Sweep" (Melee Weapons profiles) — three distinct profiles, not a dup.
"""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

SUFFIX_RE = re.compile(
    r"^(.*?)\s*-\s*(strike|sweep|witchfire|focused witchfire|standard|"
    r"supercharged|low intensity|dispersed|frag|krak)\s*$",
    re.I,
)

# Fixed on fix/daemon-character-wargear (regenerated configs, single
# "Hellforged weapons" base name). Remove this exemption once that branch
# merges and the old suffixed+bare pair is gone from these units.
DAEMON_PRINCE_EXEMPT = {
    ("death-guard", "Daemon Prince Of Nurgle"),
    ("death-guard", "Daemon Prince Of Nurgle With Wings"),
    ("emperors-children", "Daemon Prince Of Slaanesh"),
    ("emperors-children", "Daemon Prince Of Slaanesh With Wings"),
    ("thousand-sons", "Daemon Prince Of Tzeentch"),
    ("thousand-sons", "Daemon Prince Of Tzeentch With Wings"),
    ("world-eaters", "Daemon Prince Of Khorne"),
    ("world-eaters", "Daemon Prince Of Khorne With Wings"),
}


def _exact_profile_names(faction: str) -> set[str]:
    """Exact catalog profile names for a faction (angled-name stripped)."""
    names = set()
    merged = json.loads((ROOT / f"data/merged/{faction}.json").read_text())
    for unit in merged.get("units", []):
        for weapon in (unit.get("profile") or {}).get("weapons", []):
            for profile in weapon.get("profiles", []):
                names.add(profile.get("name", "").replace("\u27a4 ", "").strip())
    return names


def _iter_fixed_entries():
    """Yield (faction, unit, build_index, fixed_names) for config build files."""
    for pattern in (
        "data/config/*/characters.json",
        "data/config/*/squads.json",
        "data/config/*/vehicles.json",
    ):
        for path in sorted((ROOT / pattern).glob(pattern)):
            faction = path.parts[-3]
            data = json.loads(path.read_text())
            for unit, unit_config in data.items():
                if unit.startswith("_"):
                    continue
                builds = (unit_config.get("weapon_options") or {}).get("builds") or []
                for bi, build in enumerate(builds):
                    names = [f.get("name", "") for f in build.get("fixed", [])]
                    yield faction, unit, bi, names


def _violations():
    """Return remaining (faction, unit, name, base) violations."""
    found = []
    for faction, unit, bi, names in _iter_fixed_entries():
        if (faction, unit) in DAEMON_PRINCE_EXEMPT:
            continue
        exact = _exact_profile_names(faction)
        for name in names:
            match = SUFFIX_RE.match(name)
            if not match:
                continue
            base = match.group(1)
            if (
                any(other.lower() == base.lower() for other in names if other != name)
                and base not in exact
            ):
                found.append((faction, unit, bi, name, base))
    return found


def test_no_stray_bare_weapon_duplicates():
    """Every suffixed fixed weapon with a bare family twin in the same build
    is either a distinct catalog profile or a violation."""
    violations = _violations()
    assert violations == [], (
        "Stray bare-duplicate fixed weapon entries (double-counted profiles):\n"
        + "\n".join(
            f"  {f}{u} build {bi}: {n!r} + bare {b!r}"
            for f, u, bi, n, b in violations
        )
        or " "
    )