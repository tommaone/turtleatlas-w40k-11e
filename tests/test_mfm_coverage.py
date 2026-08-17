"""Cross-validation tests: MFM (source of truth) vs merged data.

Every unit listed in MFM must:
  1. Exist in the merged JSON for that faction
  2. Have non-empty stats (M, T, Sv, W, LD, OC)
  3. Have at least one weapon (unless on the known allowlist)

These tests catch BSData parser gaps and merge regressions.
"""

import json
import os
import pytest
import yaml
from pathlib import Path

ROOT = Path(__file__).parent.parent
MFM_DIR = ROOT / "mfm" / "data"
MERGED_DIR = ROOT / "data" / "merged"


def _norm(name: str) -> str:
    """Normalize name for cross-source comparison (handles UK/US spelling, case)."""
    n = name.lower().strip().replace("\u2019", "'")
    n = n.replace("armour", "armor")
    n = n.replace("defence", "defense")
    return n


# ── Known weaponless units (legitimate — no weapons in 40k 11e) ─────

# Units that legitimately have no weapons in 40k 11th edition.
# Keyed by MFM faction slug, values are sets of NORMALIZED unit names.
# When adding a new entry: verify the unit truly has no weapons in 40k 11e rules.
# If a unit here gains weapons via a rules update, remove it from this list.
KNOWN_NO_WEAPONS: dict[str, set[str]] = {
    "space-marines": {"drop pod"},
    "space-wolves": {"drop pod"},
    "black-templars": {"drop pod"},
    "blood-angels": {"drop pod"},
    "dark-angels": {"drop pod"},
    "deathwatch": {"drop pod"},
    "astra-militarum": {"aegis defense line", "cyclops demolition vehicle"},
    "tau-empire": {"tidewall shieldline"},
    "chaos-daemons": {"feculent gnarlmaw", "skull altar"},
    "tyranids": {"spore mines", "mucolid spores"},
}


# ── Data loading ────────────────────────────────────────────────────


def _load_mfm_factions():
    """Return list of (faction_name, slug, mfm_units) for all MFM files."""
    result = []
    for mfm_file in sorted(MFM_DIR.glob("*.yaml")):
        if mfm_file.name == "meta.yaml":
            continue
        data = yaml.safe_load(mfm_file.read_text())
        name = data.get("name", mfm_file.stem)
        slug = data.get("slug", mfm_file.stem)
        # MFM lists model-count tiers (e.g. 5- and 10-model Aquila Kill Team)
        # as separate rows with the same unit name. Merged dedupes to one
        # entry per unit, so count unique names only.
        units = sorted({u["name"] for u in data.get("units", [])
                        if not u.get("legends", False)})
        result.append((name, slug, units))
    return result


FACTIONS = _load_mfm_factions()


def _load_merged(slug):
    path = MERGED_DIR / f"{slug}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


# ── Test 1: Every MFM unit exists in merged ──────────────────────────


@pytest.mark.parametrize("name,slug,mfm_units", FACTIONS,
                         ids=[f[0] for f in FACTIONS])
def test_all_mfm_units_in_merged(name, slug, mfm_units):
    """Every unit in MFM must exist in the merged JSON."""
    merged = _load_merged(slug)
    if merged is None:
        pytest.skip(f"No merged file for {slug}")

    merged_map = {_norm(u["name"]): u["name"] for u in merged["units"]}
    missing = []
    for mfm_name in mfm_units:
        if _norm(mfm_name) not in merged_map:
            missing.append(mfm_name)

    assert not missing, (
        f"{name}: {len(missing)} MFM units missing from merged:\n"
        + "\n".join(f"  - {m}" for m in missing[:20])
    )


# ── Test 2: Every MFM unit has stats ─────────────────────────────────


@pytest.mark.parametrize("name,slug,mfm_units", FACTIONS,
                         ids=[f[0] for f in FACTIONS])
def test_all_mfm_units_have_stats(name, slug, mfm_units):
    """Every MFM unit must have non-empty stats (M, T, Sv, W, LD, OC)."""
    merged = _load_merged(slug)
    if merged is None:
        pytest.skip(f"No merged file for {slug}")

    merged_map = {_norm(u["name"]): u for u in merged["units"]}
    empty = []
    for mfm_name in mfm_units:
        mu = merged_map.get(_norm(mfm_name))
        if mu is None:
            continue  # covered by test_all_mfm_units_in_merged
        profile = mu.get("profile") or {}
        stats = profile.get("stats") or {}
        if not stats:
            empty.append(mfm_name)

    assert not empty, (
        f"{name}: {len(empty)} MFM units have empty stats:\n"
        + "\n".join(f"  - {e}" for e in empty[:20])
    )


# ── Test 3: Merged unit count >= MFM unit count ──────────────────────


@pytest.mark.parametrize("name,slug,mfm_units", FACTIONS,
                         ids=[f[0] for f in FACTIONS])
def test_merged_count_gte_mfm(name, slug, mfm_units):
    """Merged JSON must have at least as many units as MFM lists."""
    merged = _load_merged(slug)
    if merged is None:
        pytest.skip(f"No merged file for {slug}")

    merged_count = len(merged["units"])
    mfm_count = len(mfm_units)

    assert merged_count >= mfm_count, (
        f"{name}: merged has {merged_count} units but MFM lists {mfm_count}"
    )


# ── Test 4: Every MFM unit has at least one weapon ───────────────────
#    (allowlist for legitimately weaponless units)


@pytest.mark.parametrize("name,slug,mfm_units", FACTIONS,
                         ids=[f[0] for f in FACTIONS])
def test_all_mfm_units_have_weapons(name, slug, mfm_units):
    """Every MFM unit must have at least one weapon profile,
    unless it's in the KNOWN_NO_WEAPONS allowlist."""
    merged = _load_merged(slug)
    if merged is None:
        pytest.skip(f"No merged file for {slug}")

    known = KNOWN_NO_WEAPONS.get(slug, set())
    merged_map = {_norm(u["name"]): u for u in merged["units"]}
    unexpected = []   # no weapons but NOT in allowlist → regression
    stale = []        # IN allowlist but now HAS weapons → allowlist needs cleanup

    for mfm_name in mfm_units:
        mu = merged_map.get(_norm(mfm_name))
        if mu is None:
            continue
        profile = mu.get("profile") or {}
        weapons = profile.get("weapons") or []
        mfm_norm = _norm(mfm_name)

        if not weapons:
            if mfm_norm not in known:
                unexpected.append(mfm_name)
        else:
            if mfm_norm in known:
                stale.append(mfm_name)

    msg = ""
    if unexpected:
        msg += (
            f"{name}: {len(unexpected)} MFM units unexpectedly have no weapons.\n"
            f"  If they are legitimately weaponless, add them to KNOWN_NO_WEAPONS['{slug}'].\n"
            + "\n".join(f"  - {u}" for u in unexpected[:20])
        )
    if stale:
        msg += "\n" if msg else ""
        msg += (
            f"{name}: {len(stale)} units are in KNOWN_NO_WEAPONS['{slug}'] but now have weapons.\n"
            f"  Remove them from the allowlist.\n"
            + "\n".join(f"  - {s}" for s in stale[:10])
        )

    assert not msg, msg


# ── Test 5: Strict 100% coverage guarantee ──────────────────────────


# Snapshot of expected global counts.
# Update these if MFM data changes (new faction / units added).
# If a mismatch occurs, inspect the diff to see if it's a regression or a valid data update,
# then update the snapshot accordingly.
EXPECTED_COVERAGE = {
    "total_mfm": 1437,
    "total_missing": 0,
    "total_empty_stats": 0,
}

# Number of legitimately weaponless units expected per faction slug.
# Update when MFM adds/removes weaponless units.
EXPECTED_NO_WEAPONS: dict[str, int] = {
    "space-marines": 1,
    "space-wolves": 1,
    "black-templars": 1,
    "blood-angels": 1,
    "dark-angels": 1,
    "deathwatch": 1,
    "astra-militarum": 2,
    "tau-empire": 1,
    "chaos-daemons": 2,
    "tyranids": 2,
}


def test_coverage_is_100_percent():
    """Strict gate: coverage *must* be 100% with no unexplained gaps.

    If this test fails:
    1. Check if MFM data was updated (new units / factions).
    2. Check if a parser regression introduced a gap.
    3. Update EXPECTED_COVERAGE and/or KNOWN_NO_WEAPONS if the change is legitimate.
    """
    total_mfm = 0
    total_missing = 0
    total_empty_stats = 0
    total_no_weapons = 0
    no_wpn_counts: dict[str, int] = {}

    for name, slug, mfm_units in FACTIONS:
        merged = _load_merged(slug)
        if merged is None:
            total_mfm += len(mfm_units)
            total_missing += len(mfm_units)
            continue

        merged_map = {_norm(u["name"]): u for u in merged["units"]}
        nw = 0
        for mfm_name in mfm_units:
            total_mfm += 1
            mu = merged_map.get(_norm(mfm_name))
            if mu is None:
                total_missing += 1
                continue
            profile = mu.get("profile") or {}
            stats = profile.get("stats") or {}
            weapons = profile.get("weapons") or []
            if not stats:
                total_empty_stats += 1
            if not weapons:
                nw += 1

        no_wpn_counts[slug] = nw
        total_no_weapons += nw

    assert total_mfm == EXPECTED_COVERAGE["total_mfm"], (
        f"Total MFM units changed: {total_mfm} vs expected {EXPECTED_COVERAGE['total_mfm']}. "
        "MFM data may have been updated — update EXPECTED_COVERAGE in the test if intentional."
    )
    assert total_missing == EXPECTED_COVERAGE["total_missing"], (
        f"Missing units: {total_missing} vs expected {EXPECTED_COVERAGE['total_missing']}. "
        "A parser regression or data change caused gaps."
    )
    assert total_empty_stats == EXPECTED_COVERAGE["total_empty_stats"], (
        f"Units with empty stats: {total_empty_stats} vs expected {EXPECTED_COVERAGE['total_empty_stats']}. "
        "Parser regression — check stats resolution."
    )

    # Check no-weapon counts per faction against snapshot
    for slug, expected in EXPECTED_NO_WEAPONS.items():
        actual = no_wpn_counts.get(slug, 0)
        assert actual == expected, (
            f"{slug}: expected {expected} no-weapon units, got {actual}. "
            "Update EXPECTED_NO_WEAPONS and/or KNOWN_NO_WEAPONS if legitimate."
        )

    # Any faction not in EXPECTED_NO_WEAPONS must have 0 no-weapons
    for slug, actual in no_wpn_counts.items():
        if slug not in EXPECTED_NO_WEAPONS:
            assert actual == 0, (
                f"{slug}: unexpected no-weapon units ({actual}). "
                "Add them to KNOWN_NO_WEAPONS and EXPECTED_NO_WEAPONS if legitimate."
            )


# ── Test 6: Summary stats (print only, informational) ───────────────


def test_mfm_coverage_summary(capsys):
    """Print coverage summary across all factions (informational)."""
    total_mfm = 0
    total_merged = 0
    total_empty_stats = 0
    total_missing = 0
    total_no_weapons = 0
    rows = []

    for name, slug, mfm_units in FACTIONS:
        merged = _load_merged(slug)
        if merged is None:
            rows.append((name, len(mfm_units), 0, len(mfm_units), 0, 0))
            total_mfm += len(mfm_units)
            total_missing += len(mfm_units)
            continue

        merged_map = {_norm(u["name"]): u for u in merged["units"]}
        empty_stats = 0
        missing = 0
        no_weapons = 0

        for mfm_name in mfm_units:
            total_mfm += 1
            mu = merged_map.get(_norm(mfm_name))
            if mu is None:
                missing += 1
                total_missing += 1
                continue
            profile = mu.get("profile") or {}
            stats = profile.get("stats") or {}
            weapons = profile.get("weapons") or []
            if not stats:
                empty_stats += 1
                total_empty_stats += 1
            if not weapons:
                no_weapons += 1
                total_no_weapons += 1

        merged_count = len(merged["units"])
        total_merged += merged_count
        rows.append((name, len(mfm_units), merged_count, missing, empty_stats, no_weapons))

    lines = ["\n=== MFM COVERAGE SUMMARY ===\n"]
    lines.append(f"{'Faction':<25} {'MFM':>4} {'Mrgd':>5} {'Miss':>5} {'Empty':>6} {'NoWpn':>5}")
    lines.append("-" * 58)
    for name, mfm_c, mrgd, miss, empty, nowpn in sorted(rows, key=lambda x: -(x[3]+x[4])):
        issues = miss + empty
        flag = " !!!" if issues > 10 else " !" if issues > 0 else " OK"
        lines.append(f"{name:<25} {mfm_c:>4} {mrgd:>5} {miss:>5} {empty:>6} {nowpn:>5}{flag}")
    lines.append("-" * 58)
    coverage = (total_mfm - total_empty_stats - total_missing) * 100 // max(total_mfm, 1)
    lines.append(f"{'TOTAL':<25} {total_mfm:>4} {total_merged:>5} {total_missing:>5} {total_empty_stats:>6} {total_no_weapons:>5}")
    lines.append(f"\nCoverage: {coverage}% ({total_mfm - total_empty_stats - total_missing}/{total_mfm})")

    capsys.readouterr()  # clear
    print("\n".join(lines))
