"""Verify all Battleline units have correct OC values.

In 11e Warhammer 40k, most Battleline units have OC=2. However, some units
have lower OC due to their nature (swarms, poorly disciplined troops,
faction-book daemons). These exceptions are documented explicitly below.

Exceptions are keyed by (unit name, merged source file) because the same
name can legitimately appear in more than one faction's merged data with
different OC (e.g. Blue Horrors: 11e Thousand Sons book = OC 0, generic
daemons library = OC 1).

If BSData source data is updated (e.g. new library revisions), this test
will fail — alerting us to re-verify the exceptions.
"""
import json
from pathlib import Path

MERGED_DIR = Path(__file__).parent.parent / "data" / "merged"

# Known Battleline units with OC != 2, keyed by (unit name, source file).
# Verification status is per-entry:
#   - WE/EC/TS daemon entries: 11e faction-book values (BSData 11e +
#     Wahapedia 11e cross-check).
#   - chaos-daemons.json entries: generic daemons library values. These are
#     the correct Chaos Daemons army stats (OC 2 for Battleline), not stale.
#     The faction-specific books have different OC for summoned/attached versions.
#   - Nurglings / Cultist Mob: current BSData values.
KNOWN_EXCEPTIONS: dict[tuple[str, str], str] = {
    ("Blue Horrors", "thousand-sons.json"): "0",        # 11e TS book: summoned version
    ("Blue Horrors", "chaos-daemons.json"): "1",        # generic daemons library: army version
    ("Bloodletters", "world-eaters.json"): "1",         # 11e WE book: summoned version
    ("Daemonettes", "emperors-children.json"): "1",     # 11e EC book: summoned version
    ("Pink Horrors", "thousand-sons.json"): "1",        # 11e TS book: summoned version
    ("Nurglings", "chaos-daemons.json"): "0",           # current BSData value
    ("Cultist Mob", "chaos-space-marines.json"): "1",   # current BSData value
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
            key = (name, src)
            assert key in KNOWN_EXCEPTIONS, (
                f"Unexpected Battleline OC={oc} for '{name}' in {src}. "
                f"If this is a new BSData value, add it to KNOWN_EXCEPTIONS."
            )
            assert KNOWN_EXCEPTIONS[key] == oc, (
                f"Battleline '{name}' in {src}: expected OC={KNOWN_EXCEPTIONS[key]} "
                f"but found OC={oc}. Update test or investigate."
            )
            seen.add(key)

    # Make sure every known exception was actually seen
    for key, expected_oc in KNOWN_EXCEPTIONS.items():
        assert key in seen, (
            f"KNOWN_EXCEPTION {key} with OC={expected_oc} not found "
            f"in any merged file. Remove or update the exception."
        )


def test_all_other_battleline_have_oc_2():
    """All Battleline units not in exceptions must have OC=2."""
    failures = []
    for name, oc, src in _iter_battleline_units():
        if (name, src) not in KNOWN_EXCEPTIONS and oc != "2":
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
