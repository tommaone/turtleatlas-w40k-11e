"""Regression tests for the army-choice guide's first-army recommendations.

Catch the class of bug the user caught on 2026-09-06: World Eaters
recommended as a first army because a roster-wide wounds median (vehicles
included) came out "Durable", while their 2W melee core punishes every
positioning error.

These tests run pure computation (compute()/guide_lines()) — no generated
artifacts are written, so suite runs never touch tracked files.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import army_advisor as aa


def _first_army_names():
    data = aa.compute()
    lines = aa.guide_lines(data)
    names, in_section = [], False
    for ln in lines:
        if ln.startswith("## If this is"):
            in_section = True
            continue
        if in_section and ln.startswith("## "):
            break
        if in_section and ln.startswith("- **"):
            names.append(ln.split("**", 2)[1])
    return names


def test_world_eaters_not_a_first_army():
    # Regression for the exact bug the user caught: statline bulk says
    # "Durable" (median W 8 via vehicles) but the 2W melee core is fragile.
    statline = aa.durability_map()["world-eaters"]
    assert statline["statline_band"] == "Durable"
    assert "World Eaters" not in _first_army_names()


def test_dark_angels_in_first_army():
    names = _first_army_names()
    assert names and "Dark Angels" == names[0]


def test_death_guard_and_custodes_in_first_army():
    names = _first_army_names()
    assert "Death Guard" in names
    assert "Adeptus Custodes" in names


def test_imperial_knights_not_a_first_army():
    assert "Imperial Knights" not in _first_army_names()


def test_only_expert_rated_factions_in_first_army():
    data = aa.compute()
    fit = [x["fid"] for x in data["factions"]
           if x["first_army_fit"] in ("Great", "Good")]
    names = _first_army_names()
    for n in names:
        fid = [x["fid"] for x in data["factions"] if x["name"] == n]
        assert fid and fid[0] in fit, f"{n} listed without expert Great/Good fit"


def test_guide_header_is_fresh():
    data = aa.compute()
    lines = aa.guide_lines(data)
    assert any(f"Generated {aa.GENERATED}" in ln for ln in lines[:4])
    assert not any("2026-08-23" in ln for ln in lines)
    assert data["generated"] == aa.GENERATED


def test_generated_is_a_real_date_not_a_frozen_constant():
    """A hardcoded GENERATED stamps every regeneration with a stale date — the
    same 'MFM v1.4' failure mode, one field over. It must track today, so this
    fails the day someone pins it back to a literal."""
    assert aa.GENERATED == date.today().isoformat(), (
        "GENERATED is not today — it was hardcoded again; use date.today()")


def test_guide_header_names_the_real_mfm_version():
    """The header hardcoded 'MFM v1.4' while the data underneath was v1.5.
    Read the version back out and tie it to the changelog dir, so hardcoding
    any literal version fails."""
    header = "\n".join(aa.guide_lines(aa.compute())[:4])
    m = re.search(r"MFM (v\d+\.\d+)", header)
    assert m, f"no MFM version in the guide header: {header!r}"
    assert m.group(1) == aa.mfm_version(), header


def test_mask_ts_understands_every_advisor_artifact_format():
    """check_artifacts_current classifies stale files as content drift vs a
    revertable timestamp bump using gen_findings_html._mask_ts. If the mask
    does not know the advisor date formats, a date-only regeneration is
    misclassified as real drift — and committing it would be churn."""
    from gen_findings_html import _mask_ts

    cases = {
        "generated 2026-10-15 09:41 UTC": "generated <TS>",                 # faction page
        "*Generated 2026-10-15 from engine outputs*": "*generated <TS> from engine outputs*",
        '"generated": "2026-10-15",': '"generated <TS>",',                  # advisor.json
    }
    for raw, want in cases.items():
        assert _mask_ts(raw) == want, raw


# ---------------------------------------------------------------------------
# points_churn — the changelog restructure (MFM 2026-09)
# ---------------------------------------------------------------------------

def test_points_churn_is_not_silently_zero():
    """The MFM submodule moved entries out of DATA-CHANGELOG.md into
    changelog/v<X.Y>.md, leaving the old path as a pointer. The parser kept
    reading it, returned {}, and zeroed points_churn for all 28 factions —
    with no test failure and no error. Guard the signal, not the mechanism.
    """
    churn = aa.points_churn()
    assert churn, "points_churn() returned nothing — changelog layout changed"

    zeros = [f["fid"] for f in aa.compute()["factions"] if not f["points_churn"]]
    assert not zeros, f"points_churn silently zeroed for {zeros}"


def test_points_churn_reads_every_changelog_version():
    """History is append-only, so these are lower bounds: a v1.6 addition will
    not break the test, but a parser that stops reading v1.0-v1.4 (leaving 1
    mention each) will."""
    churn = aa.points_churn()
    # As of v1.5: 76 Aeldari and 245 Orks bullets across v1.0-v1.4 (verified
    # against the pre-restructure DATA-CHANGELOG.md), plus one v1.5 section.
    assert churn["aeldari"] >= 77, churn.get("aeldari")
    assert churn["orks"] >= 246, churn.get("orks")


def test_changelog_names_match_tiers_after_normalisation():
    """Typographic apostrophes (Emperor’s Children, T’au Empire) must still
    resolve to the ASCII tier names, or the faction silently reads 0."""
    lookup = {aa._norm_name(f["name"]) for f in aa.compute()["factions"]}
    for raw in ("Emperor\u2019s Children", "T\u2019au Empire", "Aeldari"):
        assert aa._norm_name(raw) in lookup, raw


def test_meta_ceiling_is_null_not_fabricated():
    """Retired 2026-08-27. The caveat once claimed it was engine-computed for
    five factions while every value was null — an unreadable contract."""
    data = aa.compute()
    assert all(f["meta_ceiling"] is None for f in data["factions"])
    caveats = " ".join(data["_formula"]["not_modeled"])
    assert "RETIRED" in caveats


def test_advisor_overall_index_is_copied_from_tiers():
    """compare_factions tells agents the two overall figures always agree
    because advisor.overall_index is copied from army_tiers.overall. If the
    advisor ever starts adjusting the index, that contract becomes a lie."""
    data = aa.compute()
    tiers = json.loads((aa.REPO / "findings" / "army_tiers.json").read_text())
    for f in data["factions"]:
        assert f["overall_index"] == tiers[f["fid"]]["overall"], f["fid"]


def test_mfm_version_matches_the_loaded_data():
    """The guide header's MFM version must match the data actually merged. A
    v1.6 changelog file landing before a data regen would otherwise stamp a
    v1.6 claim over v1.5 data, with a green check."""
    merged = json.loads((aa.REPO / "data" / "merged" / "aeldari.json").read_text())
    assert aa.mfm_version().lstrip("v") == merged["version"], merged.get("version")


def test_guide_html_escapes_interpolated_text():
    """The guide page interpolates expert why-text and faction names. A stray
    < or & must be escaped, or the page breaks — or worse, runs script."""
    page = aa.render_guide_html([
        "# Choosing",
        "- **Orks** — if x < y & z <script>alert(1)</script>",
        "> a > b",
    ])
    # data text neutralised
    assert "<script>" not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page
    assert "x &lt; y &amp; z" in page
    assert "<blockquote>a &gt; b</blockquote>" in page
    # our own markup still renders (escape must not eat the <strong> we add)
    assert "<strong>Orks</strong>" in page
