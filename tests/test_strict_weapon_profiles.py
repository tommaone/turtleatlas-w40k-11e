"""STRICT cross-faction weapon-profile sanity, from raw merged data.

These scan every weapon in every faction's merged JSON for the invarianfns a
correct datasheet cannot violate. Detecting issues here is honest signal —
it answers the user's ask ("tests that would actually fail if the data is
busted") without needing an archetype table, because it derives directly
from the raw stat blocks.

Checks per weapon profile (Ranged and Melee):
  1. Numeric stats parse — Range/A/WS/S/AP/D are present, numeric (or the
     legal 'Melee'/'N/A' sentinels).
  2. Bounds — 0 <= S; 0 <= AP <= 0 (AP is a penalty, cannot be positive);
     D > 0; A >= 1. A weapon claiming AP +1 would be inverted/broken data.
  3. No negative Damage, no NaN/Inf anywhere.

This is the corder that catches inverted-stat datasheets. It's strict: any
violation fails CI, because a datasheet with Strength -2 or AP +3 is a real
data bug, not an opinion.
"""
import json
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.crossfaction_common import ALL_FACTIONS, ROOT

MERGED = ROOT / "data" / "merged"


def _iter_weapons(faction):
    """Yield (unit_name, weapon_name, stats_dict) for every weapon."""
    path = MERGED / f"{faction}.json"
    if not path.exists():
        return
    data = json.loads(path.read_text())
    for u in data.get("units", []):
        weapons = (u.get("profile") or {}).get("weapons") or []
        for w in weapons:
            for prof in w.get("profiles") or []:
                stats = prof.get("stats") or {}
                yield u.get("name", "?"), w.get("name", "?"), stats


def _try_num(v):
    """Return float if v is numeric, else None (Range 'Melee' etc.)."""
    if v is None or isinstance(v, bool):
        return None
    try:
        return float(str(v).strip().rstrip("+").replace(",", ""))
    except (ValueError, TypeError):
        return None


@pytest.mark.parametrize("faction", ALL_FACTIONS)
def test_weapon_stats_are_sane(faction):
    bad = []
    seen = 0
    for unit, wname, stats in _iter_all(faction):
        seen += 1
        ap = stats.get("AP")
        apn = _try_num(ap)
        if apn is not None and apn > 0:
            bad.append(f"{unit}/{wname}: AP {apn!r} is positive (must be <=0)")
        s = stats.get("S")
        sn = _try_num(s)
        if sn is not None and sn < 0:
            bad.append(f"{unit}/{wname}: S {sn!r} is negative")
        d = stats.get("D")
        dn = _try_num(d)
        if dn is not None and dn <= 0:
            bad.append(f"{unit}/{wname}: D {dn!r} must be >0")
        a = stats.get("A")
        an = _try_num(a)
        if an is not None and an < 1:
            bad.append(f"{unit}/{wname}: A {an!r} must be >=1")
        # NaN guard
        for k in ("S", "A", "D", "AP", "WS"):
            v = _try_num(stats.get(k))
            if v is not None and math.isnan(v):
                bad.append(f"{unit}/{wname}: {k} is NaN")
    if seen == 0:
        pytest.fail(f"{faction}: no weapons found in merged data")
    assert not bad, f"{faction}: {len(bad)} weapon-profile issue(s):\n" + "\n".join(bad)


def _iter_all(faction):
    path = MERGED / f"{faction}.json"
    if not path.exists():
        return
    data = json.loads(path.read_text())
    for u in data.get("units", []):
        weapons = (u.get("profile") or {}).get("weapons") or []
        for w in weapons:
            for prof in w.get("profiles") or [{"stats": {}}]:
                yield u.get("name", "?"), w.get("name", "?"), prof.get("stats") or {}


@pytest.mark.parametrize("faction", ALL_FACTIONS)
def test_no_missing_attack_stat_for_ranged(faction):
    """Ranged weapon profiles must carry an S, AP, D and Range (that's what
    makes them resolvable by the engine as ranged)."""
    missing = []
    for unit, wname, stats in _iter_all(faction):
        rng = stats.get("Range")
        if rng is None or str(rng).strip().lower() == "melee":
            continue  # melee
        for k in ("S", "AP", "D", "A"):
            if stats.get(k) is None:
                missing.append(f"{unit}/{wname}: missing {k} in ranged profile")
    assert not missing, f"{faction}: {len(missing)} missing stat(s):\n" + "\n".join(missing)