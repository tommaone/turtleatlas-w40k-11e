"""Verify all Battleline units have correct OC values.

In 10e Warhammer 40k, most Battleline units have OC=2. However, some units
have lower OC due to their nature (swarms, poorly disciplined troops).
These exceptions are documented explicitly below.

If BSData source data is updated (e.g. new library revisions), this test
will fail — alerting us to re-verify the exceptions.
"""
import json
from pathlib import Path

MERGED_DIR = Path(__file__).parent.parent / "data" / "merged"

# Known Battleline units with OC != 2 and their expected values.
# These are verified against BSData source (Daemons Library rev=9,
# Chaos Space Marines rev=5) — no better source value exists.
KNOWN_EXCEPTIONS: dict[str, str] = {
    "Blue Horrors": "1",   # Daemons Library rev=9: fragile scream entities
    "Cultist Mob": "1",    # Chaos Space Marines rev=5: barely trained cultists
    "Nurglings": "0",      # Daemons Library rev=9: swarm creatures
}


def _all_merged_files() -> list[Path]:
    return sorted(MERGED_DIR.glob("*.json"))


def _iter_battleline_units():
    """Yield (name, oc_value, source_file) for every Battleline unit."""
    for fpath in _all_merged_files():
        with open(fpath) as f:
            data = json.load(f)
        for unit in data["units"]:
            profile = unit.get("profile") or {}
            keywords = profile.get("keywords") or []
            if "Battleline" not in keywords:
                continue
            stats = profile.get("stats") or {}
            oc = str(stats.get("OC", "?"))
            yield (unit["name"], oc, fpath.name)


def test_all_known_exceptions_accounted_for():
    """Every Battleline unit with OC != 2 must be in KNOWN_EXCEPTIONS."""
    seen = set()
    for name, oc, src in _iter_battleline_units():
        if oc != "2":
            key = (name, oc)
            assert name in KNOWN_EXCEPTIONS, (
                f"Unexpected Battleline OC={oc} for '{name}' in {src}. "
                f"If this is a new BSData value, add it to KNOWN_EXCEPTIONS."
            )
            assert KNOWN_EXCEPTIONS[name] == oc, (
                f"Battleline '{name}': expected OC={KNOWN_EXCEPTIONS[name]} "
                f"but found OC={oc} in {src}. Update test or investigate."
            )
            seen.add(key)

    # Make sure every known exception was actually seen
    for name, expected_oc in KNOWN_EXCEPTIONS.items():
        assert (name, expected_oc) in seen, (
            f"KNOWN_EXCEPTION '{name}' with OC={expected_oc} not found "
            f"in any merged file. Remove or update the exception."
        )


def test_all_other_battleline_have_oc_2():
    """All Battleline units not in exceptions must have OC=2."""
    failures = []
    for name, oc, src in _iter_battleline_units():
        if name not in KNOWN_EXCEPTIONS and oc != "2":
            failures.append(f"{name} OC={oc} in {src}")
    assert not failures, (
        f"Battleline units with unexpected OC != 2:\n" +
        "\n".join(f"  {f}" for f in failures)
    )


def test_battleline_oc_coverage_summary():
    """Print a summary of Battleline OC distribution for manual review."""
    from collections import Counter
    counts: Counter[str] = Counter()
    exceptions_found = set()
    all_names = set()
    for name, oc, src in _iter_battleline_units():
        counts[oc] += 1
        all_names.add(name)
        if oc != "2":
            exceptions_found.add((name, oc))

    print(f"\nBattleline units total: {sum(counts.values())} "
          f"across {len(all_names)} unique names")
    for oc in sorted(counts, key=str):
        print(f"  OC={oc}: {counts[oc]}")
    if exceptions_found:
        print("Verified exceptions:")
        for name, oc in sorted(exceptions_found):
            print(f"  {name}: OC={oc}")
