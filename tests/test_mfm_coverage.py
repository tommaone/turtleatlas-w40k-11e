"""Cross-validation tests: MFM (source of truth) vs merged data.

Every unit listed in MFM must:
  1. Exist in the merged JSON for that faction
  2. Have non-empty stats (M, T, Sv, W, LD, OC)
  3. Have at least one weapon

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


def _load_mfm_factions():
    """Return list of (faction_name, slug, mfm_units) for all MFM files."""
    result = []
    for mfm_file in sorted(MFM_DIR.glob("*.yaml")):
        if mfm_file.name == "meta.yaml":
            continue
        data = yaml.safe_load(mfm_file.read_text())
        name = data.get("name", mfm_file.stem)
        slug = data.get("slug", mfm_file.stem)
        units = [u["name"] for u in data.get("units", [])
                 if "[Legends]" not in u.get("name", "")]
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

    merged_names = {u["name"] for u in merged["units"]}
    missing = sorted(set(mfm_units) - merged_names)

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

    merged_map = {u["name"]: u for u in merged["units"]}
    empty = []
    for mfm_name in mfm_units:
        mu = merged_map.get(mfm_name)
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

@pytest.mark.parametrize("name,slug,mfm_units", FACTIONS,
                         ids=[f[0] for f in FACTIONS])
def test_all_mfm_units_have_weapons(name, slug, mfm_units):
    """Every MFM unit must have at least one weapon profile."""
    merged = _load_merged(slug)
    if merged is None:
        pytest.skip(f"No merged file for {slug}")

    merged_map = {u["name"]: u for u in merged["units"]}
    no_weapons = []
    for mfm_name in mfm_units:
        mu = merged_map.get(mfm_name)
        if mu is None:
            continue
        profile = mu.get("profile") or {}
        weapons = profile.get("weapons") or []
        if not weapons:
            no_weapons.append(mfm_name)

    assert not no_weapons, (
        f"{name}: {len(no_weapons)} MFM units have no weapons:\n"
        + "\n".join(f"  - {w}" for w in no_weapons[:20])
    )


# ── Test 5: Summary stats (print only, never fails) ──────────────────

def test_mfm_coverage_summary(capsys):
    """Print coverage summary across all factions."""
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

        merged_map = {u["name"]: u for u in merged["units"]}
        empty_stats = 0
        missing = 0
        no_weapons = 0

        for mfm_name in mfm_units:
            total_mfm += 1
            mu = merged_map.get(mfm_name)
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
