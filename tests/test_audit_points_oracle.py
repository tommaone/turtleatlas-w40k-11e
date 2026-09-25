"""Guard: the audit grades points against MFM, never against BSData.

Repo convention (AGENTS.md / memory/feedback.md): MFM is points truth,
BSData is the wargear/stats source. The audit used to read `pts` from
BSData's sharedSelectionEntry costs, so it compared config prices against
the wrong instrument — and reported imperial-agents drift that was really
MFM's groupTitle pricing tiers, not config error.

This pins the oracle, not the finding count. The count is allowed to move;
what must not move is WHICH source decides whether points are correct.
"""

import importlib.util
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

AUDIT = REPO / "scripts" / "audit_curated_vs_bsdata.py"


def _load_audit():
    spec = importlib.util.spec_from_file_location("audit_curated", AUDIT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_audit_points_oracle_is_mfm_not_bsdata():
    """MFM and BSData disagree for a real unit, so the oracle is observable."""
    audit = _load_audit()

    mfm = audit.load_mfm_points("imperial-agents")
    assert mfm, "MFM points did not load for imperial-agents"
    # MFM base rate after the groupTitle fix.
    assert mfm["inquisitor"] == 55

    curated = {"pts": mfm["inquisitor"], "builds": [{"slots": [], "fixed": []}]}
    bsdata = {"wargear_slots": {"fixed": [], "slots": []}, "pts": 65}

    # Matching MFM price, wrong BSData price: must be clean.
    assert audit.compare("inquisitor", curated, bsdata, mfm) == []

    # MFM says 55, config says 65: must be reported, and must name MFM.
    drifted = audit.compare("inquisitor", {**curated, "pts": 65}, bsdata, mfm)
    kinds = [x["type"] for x in drifted]
    assert kinds == ["POINTS_DRIFT"], kinds
    assert "MFM=55" in drifted[0]["detail"], drifted[0]["detail"]


def test_audit_reports_missing_mfm_entry_with_nearest_match():
    """A curated name MFM does not carry is unverifiable, not silently clean.

    black-templars config says "Emperor's Champion (Anointed)"; MFM says
    "Emperor’S Champion" (capital S is a real scraping artifact upstream).
    The finding must name the candidate so it can be judged.
    """
    audit = _load_audit()
    mfm = audit.load_mfm_points("black-templars")
    curated = {"pts": 100, "builds": [{"slots": [], "fixed": []}]}
    bsdata = {"wargear_slots": {"fixed": [], "slots": []}, "pts": 90}

    found = audit.compare("emperors champion (anointed)", curated, bsdata, mfm)
    assert [x["type"] for x in found] == ["NO_MFM_POINTS"], found
    assert "nearest MFM" in found[0]["detail"] and "90" in found[0]["detail"], found[0]


def test_audit_skips_points_when_faction_has_no_mfm_file():
    """No MFM file means no oracle; the audit must not invent a finding."""
    audit = _load_audit()
    curated = {"pts": 100, "builds": [{"slots": [], "fixed": []}]}
    bsdata = {"wargear_slots": {"fixed": [], "slots": []}, "pts": 90}
    assert audit.compare("anything", curated, bsdata, None) == []


def test_base_points_prefers_plain_over_group_title():
    """The shared resolver must not regress to last-wins."""
    from adapter.mfm_pricing import base_points, iter_base_entries

    units = [
        {"name": "Inquisitor", "pricing": [{"costs": [{"models": 1, "points": 55}]}]},
        {"name": "Inquisitor", "groupTitle": "Every Model Has The Imperium Keyword",
         "pricing": [{"costs": [{"models": 1, "points": 65}]}]},
    ]
    assert base_points(units) == {"Inquisitor": 55}

    # Group-only unit must survive — 11 factions rely on this fallback.
    group_only = [{"name": "Space Marine", "groupTitle": "Space Marines",
                   "pricing": [{"costs": [{"models": 1, "points": 20}]}]}]
    assert base_points(group_only) == {"Space Marine": 20}
    assert [n for n, _ in iter_base_entries(group_only)] == ["Space Marine"]


def test_real_mfm_files_all_resolve():
    """Every faction MFM file must resolve without dropping units."""
    from adapter.mfm_pricing import base_points

    files = sorted((REPO / "mfm" / "data").glob("*.yaml"))
    assert len(files) >= 30, f"expected 30+ MFM faction files, found {len(files)}"
    for path in files:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        units = data.get("units") or []
        resolved = base_points(units)
        priced = [u for u in units if u.get("pricing")]
        # A unit priced upstream must resolve; some units carry no pricing.
        assert len(resolved) == len({u["name"] for u in priced}), \
            f"{path.name}: {len(resolved)} resolved vs {len({u['name'] for u in priced})} priced"
