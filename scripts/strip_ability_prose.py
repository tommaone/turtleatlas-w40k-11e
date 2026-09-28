"""Drop ability prose the engine never reads from data/merged/*.json.

AGENTS.md: "This repository contains NO Games Workshop copyrighted rule text" and
"⛔ No verbatim rule text (ability descriptions...)". The merged corpus carried a
`description` on all 2706 abilities — ~530KB of prose — but the engine parses
that text in only three places:

  engine/reroll_detect.py        detect_reroll_ability / detect_army_wide_reroll
  engine/damage_boost_detect.py  detect_damage_boost
  engine/dpp.py                  parse_transport_capacity

Measured over the corpus, 295 of 2706 abilities drive one of those detectors.
The other ~89% of the prose is dead weight: it is committed, it is rule text, and
removing it changes no engine output.

This script keeps `description` only where a detector consumes it, so the
remaining prose is exactly the load-bearing minimum. It is idempotent and
supports --check (exit 1 if any dead prose is present, for CI).

Scope note: this does not make the repo rule-text-free. The 295 retained
descriptions are still prose, and the real fix is to replace prose parsing with
machine-readable fields (transport_capacity, reroll spec) and then drop the
strings entirely. That is a larger engine change, tracked in docs/roadmap.md.

Usage:
    python3 scripts/strip_ability_prose.py            # rewrite in place
    python3 scripts/strip_ability_prose.py --check    # verify only
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))
sys.path.insert(0, str(REPO_ROOT))

from damage_boost_detect import detect_damage_boost  # noqa: E402
from dpp import parse_transport_capacity  # noqa: E402
from reroll_detect import detect_army_wide_reroll, detect_reroll_ability  # noqa: E402


def needs_prose(ability: dict) -> bool:
    """True when a detector consumes this ability's description.

    Any change to the engine's prose parsing must be reflected here, or this
    script will strip text the engine needs. tests/test_no_dead_ability_prose.py
    is the guard in the other direction: it fails if prose is kept that nothing
    reads.
    """
    if detect_reroll_ability(ability) is not None:
        return True
    if detect_army_wide_reroll(ability) is not None:
        return True
    if detect_damage_boost(ability) is not None:
        return True
    if str(ability.get("name", "")).upper() == "TRANSPORT":
        # Only meaningful if a number is actually extractable; a Transport entry
        # with no capacity prose contributes nothing.
        if parse_transport_capacity(ability.get("description")) is not None:
            return True
    return False


def strip_unit(unit: dict) -> tuple[int, int]:
    """Strip dead prose from one unit. Returns (stripped, kept)."""
    stripped = kept = 0
    profile = unit.get("profile") or {}
    for ability in profile.get("abilities") or []:
        if not isinstance(ability, dict):
            continue
        desc = ability.get("description")
        if not desc:
            continue
        if needs_prose(ability):
            kept += 1
        else:
            del ability["description"]
            stripped += 1
    return stripped, kept


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true",
                        help="report dead prose without rewriting (exit 1 if found)")
    args = parser.parse_args()

    total_stripped = total_kept = 0
    dirty: list[str] = []
    for path in sorted((REPO_ROOT / "data" / "merged").glob("*.json")):
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        stripped = kept = 0
        for unit in data.get("units", []):
            s, k = strip_unit(unit)
            stripped += s
            kept += k
        total_stripped += stripped
        total_kept += kept
        if stripped:
            dirty.append(path.name)
            if not args.check:
                # Match the existing merged-file serialization byte-for-byte so the
                # diff shows only the removed descriptions: indent=2,
                # ensure_ascii=False, and NO trailing newline.
                path.write_text(json.dumps(data, indent=2, ensure_ascii=False),
                                encoding="utf-8")

    print(f"  dead prose stripped: {total_stripped}")
    print(f"  prose kept (engine reads it): {total_kept}")
    if dirty:
        print(f"  files affected: {len(dirty)}")
        if args.check:
            print("FAIL: dead ability prose is committed. "
                  "Run: python3 scripts/strip_ability_prose.py")
            return 1
    else:
        print("  clean: no dead ability prose")
    if args.check and not dirty:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
