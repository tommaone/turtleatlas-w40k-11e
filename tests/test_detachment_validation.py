"""
Detachment disposal validation & heuristics (post-mechanical).

Decision 2026-08-27: mechanical `detachment_modifiers.json` scoring is retired.
Most detachment buffs cannot be expressed as a numeric DPP/SURV/MOB modifier,
and the auto-generated files carried fabricated rules. Detachment strength is
now a heuristic (expert ratings), NOT an engine number.

What this suite verifies now:
  1. Mechanical detachment modifiers are retired — compute_ranking(detachment=X)
     returns the generalist baseline (no fabricated modifiers are applied).
  2. force-disposition mapping (supported.json `dispositions`) is internally
     valid and consistent with the merged detachment data (dp_cost).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.ranking import RankingEngine
from scripts.gen_detach_review_html import (
    ATLAS_DIR, FACTIONS as ATLAS_FACTIONS, render_faction, render_index,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "data" / "config"
MERGED_DIR = REPO_ROOT / "data" / "merged"

VALID_DP_COST = {1, 2, 3}
VALID_DISPOSITION_IDS = {
    "purge-the-foe", "take-and-hold", "reconnaissance", "priority-assets", "disruption",
}

# Factions that carry a dispositions map in supported.json
FACTIONS = sorted(
    p.name for p in CONFIG_DIR.iterdir()
    if p.is_dir() and (p / "supported.json").exists() and not p.name.startswith("_")
)


def _support(faction: str) -> dict:
    p = CONFIG_DIR / faction / "supported.json"
    return json.loads(p.read_text())


def _merged_detachments(faction: str) -> list[dict]:
    p = MERGED_DIR / f"{faction}.json"
    if not p.exists():
        return []
    data = json.loads(p.read_text())
    return data.get("detachments", [])


def _dispositions(faction: str) -> dict:
    return _support(faction).get("dispositions", {})


# ═══════════════════════════════════════════════════════════════════════
# TIER 1: MECHANICAL MODIFIERS ARE RETIRED
# ═══════════════════════════════════════════════════════════════════════

class TestMechanicalRetired:
    """Fabricated mechanical detachment modifiers must not affect scores."""

    def test_detachment_scoring_is_generalist(self):
        """detachment=X must equal the generalist baseline for every faction."""
        for faction in ("grey-knights", "chaos-knights", "chaos-daemons",
                        "space-marines", "dark-angels", "deathwatch"):
            eng = RankingEngine(faction)
            base = eng.compute_ranking()
            base_fp = [(r["name"], round(r["dpp"], 6)) for r in base]
            for det in list(_dispositions(faction))[:1]:
                mod = eng.compute_ranking(detachment=det)
                mod_fp = [(r["name"], round(r["dpp"], 6)) for r in mod]
                assert mod_fp == base_fp, (
                    f"{faction}/{det}: detachment changed DPP — mechanical "
                    f"detachment modifiers must be retired (2026-08-27)."
                )

    def test_no_mechanical_modifier_file(self):
        """No faction may carry a mechanical detachment_modifiers.json."""
        for p in CONFIG_DIR.iterdir():
            if p.is_dir() and (p / "detachment_modifiers.json").exists():
                pytest.fail(f"{p.name}: mechanical detachment_modifiers.json should be removed.")


# ═══════════════════════════════════════════════════════════════════════
# TIER 2: FORCE DISPOSITIONS — supported.json
# ═══════════════════════════════════════════════════════════════════════

class TestForceDispositions:
    """Validate force disposition mapping & dp_cost against merged data."""

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_disposition_values_are_valid(self, faction):
        """Every disposition value must be one of the 5 valid IDs."""
        for det, disp in _dispositions(faction).items():
            assert disp in VALID_DISPOSITION_IDS, (
                f"{faction}/{det}: invalid disposition '{disp}'. "
                f"Valid IDs: {VALID_DISPOSITION_IDS}"
            )

    @pytest.mark.parametrize("faction", ["chaos-knights", "grey-knights", "dark-angels"])
    def test_dispositions_present(self, faction):
        """These factions should have a non-empty dispositions map."""
        assert len(_dispositions(faction)) > 0, f"{faction}: dispositions empty"

    def test_ck_disposition_spot_checks(self):
        """Spot-check each CK detachment maps to its MFM objective disposition."""
        disp = _dispositions("chaos-knights")
        expected = {
            "infernal-lance": "priority-assets",
            "iconoclast-fiefdom": "take-and-hold",
            "bastions-of-tyranny": "priority-assets",
            "hunting-warpack": "reconnaissance",
            "lords-of-dread": "take-and-hold",
            "traitoris-lance": "purge-the-foe",
            "helhunt-lance": "disruption",
            "houndpack-lance": "reconnaissance",
        }
        for det, exp in expected.items():
            assert disp.get(det) == exp, f"{det}: expected '{exp}', got '{disp.get(det)}'"

    def test_get_detachments_for_disposition(self):
        """Supported map is consistent: purge-the-foe returns only traitoris lance."""
        eng = RankingEngine("chaos-knights")
        assert set(eng.config.get_detachments_for_disposition("purge-the-foe")) == {
            "traitoris-lance",
        }

    def test_can_detachment_play_disposition(self):
        """can_detachment_play_disposition handles kebab + space-separated names."""
        eng = RankingEngine("chaos-knights")
        assert eng.config.can_detachment_play_disposition("infernal-lance", "priority-assets")
        assert eng.config.can_detachment_play_disposition("INFERNAL LANCE", "priority-assets")
        assert not eng.config.can_detachment_play_disposition("infernal-lance", "purge-the-foe")

    def test_invalid_disposition_raises(self):
        """A detachment that can't play the given disposition must raise."""
        eng = RankingEngine("chaos-knights")
        with pytest.raises(ValueError, match="cannot be used"):
            eng.compute_ranking(detachment="INFERNAL LANCE", disposition="purge-the-foe")

    def test_valid_disposition_succeeds(self):
        """A valid detachment+disposition combo must rank fine."""
        eng = RankingEngine("chaos-knights")
        results = eng.compute_ranking(detachment="TRAITORIS LANCE", disposition="purge-the-foe")
        assert isinstance(results, list) and len(results) > 0


# ═══════════════════════════════════════════════════════════════════════
# TIER 3: DISPOSITIONS CONSISTENT WITH MERGED DETACHMENT DATA
# ═══════════════════════════════════════════════════════════════════════

class TestDispositionConsistency:
    """dispositions must correspond to merged-data detachments (dp_cost valid)."""

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_disposition_keys_match_merged_detachments(self, faction):
        """Every disposition key should appear among merged detachment names."""
        disp = _dispositions(faction)
        if not disp:
            pytest.skip(f"{faction}: no dispositions to check")
        merged = _merged_detachments(faction)
        if not merged:
            pytest.skip(f"{faction}: no merged detachments to check")
        merged_keys = {
            d.get("name", "").strip().lower().replace(" ", "-")
            .replace("'", "").replace("\u2019", "")
            for d in merged
        }
        for det_key in disp:
            # det_key is already kebab-normalised e.g. "the-phaerons-armoury"
            # (apostrophes stripped — straight AND curly)
            assert det_key in merged_keys, (
                f"{faction}/{det_key}: disposition key has no merged detachment "
                f"(derived from normalize-for-catalog; update key or merged data)"
            )

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_merged_dp_costs_are_valid(self, faction):
        """dp_cost of merged detachments must be 1, 2 or 3 where present."""
        for d in _merged_detachments(faction):
            dp = d.get("dp_cost") or d.get("dp")
            if dp is not None and int(dp) not in VALID_DP_COST:
                pytest.fail(f"{faction}/{d.get('name')}: invalid dp_cost {dp}")


# ═══════════════════════════════════════════════════════════════════════
# TIER 4: HEURISTIC DETACHMENT SCAFFOLD — detachments.json (L2)
# ═══════════════════════════════════════════════════════════════════════

def _slugify(name: str) -> str:
    """Kebab slug matching scripts/generate_detachments_heuristic.py (apostrophes
    stripped — straight AND curly)."""
    return (
        name.strip().lower().replace(" ", "-")
        .replace("'", "").replace("\u2019", "")
    )


def _heuristic_detachments(faction: str) -> dict:
    p = CONFIG_DIR / faction / "detachments.json"
    if not p.exists():
        return {}
    data = json.loads(p.read_text())
    return data.get("detachments", {})


class TestHeuristicScaffold:
    """detachments.json (L2 heuristic scaffold) must be complete & L0-traceable."""

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_heuristic_file_exists_when_merged_detachments(self, faction):
        """Every faction with merged detachments ships a detachments.json."""
        if _merged_detachments(faction):
            assert (CONFIG_DIR / faction / "detachments.json").exists(), (
                f"{faction}: merged detachments present but no detachments.json"
            )

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_heuristic_entries_match_merged(self, faction):
        """Every heuristic entry maps 1:1 to a merged detachment (slug + dp_cost)."""
        merged = {_slugify(d.get("name", "")): d for d in _merged_detachments(faction)}
        heur = _heuristic_detachments(faction)
        for slug, entry in heur.items():
            assert slug in merged, (
                f"{faction}/{slug}: heuristic entry has no merged detachment"
            )
            mdp = merged[slug].get("dp") or merged[slug].get("dp_cost")
            assert entry.get("dp_cost") == int(mdp), (
                f"{faction}/{slug}: dp_cost {entry.get('dp_cost')} != merged {mdp}"
            )

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_every_merged_detachment_has_heuristic_entry(self, faction):
        """No merged detachment may be missing from the heuristic scaffold."""
        merged = {_slugify(d.get("name", "")) for d in _merged_detachments(faction)}
        heur = set(_heuristic_detachments(faction))
        missing = merged - heur
        assert not missing, f"{faction}: merged detachments missing from scaffold: {sorted(missing)}"

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_heuristic_dispositions_valid_and_consistent(self, faction):
        """Heuristic disposition must be valid and match supported.json map."""
        for slug, entry in _heuristic_detachments(faction).items():
            disp = entry.get("disposition")
            assert disp in VALID_DISPOSITION_IDS, (
                f"{faction}/{slug}: invalid heuristic disposition {disp!r}"
            )
            sup_disp = _dispositions(faction).get(slug)
            assert disp == sup_disp, (
                f"{faction}/{slug}: heuristic disposition {disp!r} != "
                f"supported.json {sup_disp!r}"
            )

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_dispositions_are_objective_derived(self, faction):
        """supported.json dispositions must equal the merged MFM objective
        (gen_config.py derives them: objective lower -> kebab). Stale curated
        values drift from the MFM revision — lock them to truth."""
        disp = _dispositions(faction)
        if not disp:
            pytest.skip(f"{faction}: no dispositions to check")
        for det in _merged_detachments(faction):
            slug = _slugify(det.get("name", ""))
            obj = (det.get("objective") or "").strip().lower().replace(" ", "-")
            if not obj:
                continue
            assert disp.get(slug) == obj, (
                f"{faction}/{slug}: supported disposition {disp.get(slug)!r} != "
                f"merged objective-derived {obj!r}"
            )

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_heuristic_entries_are_l0_traceable(self, faction):
        """Every heuristic entry names its L0 source; scaffold is not expert."""
        for slug, entry in _heuristic_detachments(faction).items():
            assert entry.get("source"), f"{faction}/{slug}: missing L0 source"
            assert "strength" not in entry, (
                f"{faction}/{slug}: scaffold must not carry expert strength ratings"
            )
            assert "best_for" not in entry, (
                f"{faction}/{slug}: scaffold must not carry expert best_for"
            )


# ═══════════════════════════════════════════════════════════════════════
# TIER 5: L2 ENRICHMENT (EXPERT REVIEW) GATE
# ═══════════════════════════════════════════════════════════════════════

L2_STRENGTHS = {"Strong", "Moderate", "Situational", "Weak"}
L2_SCAFFOLD_FIELDS = {
    "_id", "_slug", "name", "dp_cost", "disposition", "objective", "source",
}
L2_EXPERT_FIELDS = {
    # Static L2 facts only (lego bricks). Unit roles, combos, play_style and
    # army tips are composed LIVE from L0-L3 at query time — never stored here
    # (distillate-of-distillate = knowledge base poison).
    "rule", "strength", "strength_notes", "limitations",
}
# Paraphrase cannot quote the (GW-copyrighted) rule text; 600 chars is more
# than a real summary needs and far less than verbatim detachment rules.
L2_RULE_TEXT_MAX = 600
L2_SOURCE_TOKENS = ("wahapedia", "newrecruit", "mfm", "merged", "battle report")


def _traces_to_source(notes: str) -> bool:
    """Traceable = cites an L0/analyst source: a URL or a known token."""
    lowered = notes.lower()
    return "http://" in lowered or "https://" in lowered or any(
        t in lowered for t in L2_SOURCE_TOKENS
    )


def _meta(faction: str) -> dict:
    p = CONFIG_DIR / faction / "detachments.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text()).get("_meta", {})


class TestL2Enrichment:
    """Expert L2 fields follow the schema; reviewed files are complete.

    Rules (docs/detachment-info-architecture.md §5 + AGENTS.md IP):
      - `rule.text` is a short PARAPHRASE flagged `_paraphrase: true` — never
        verbatim GW rule text (copyright). `affects` lists keywords/units.
      - `strength` ∈ {Strong, Moderate, Situational, Weak} and ALWAYS ships
        with `strength_notes` (traceable) + `limitations`.
      - `_meta.human_reviewed: true` flips the review gate: the file must be
        COMPLETE — every entry rated and sourced. No partial enrichment: an
        unreviewed file may carry no expert fields at all.
      - L2 is static FACTS only. Unit roles/combos/play_style (best_units,
        scoring_units, support_units, hammer_units, spam, combos, play_style)
        are NOT stored — the LLM composes them live from L0-L3 bricks.
    """

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_no_unknown_fields(self, faction):
        allowed = L2_SCAFFOLD_FIELDS | L2_EXPERT_FIELDS
        for slug, entry in _heuristic_detachments(faction).items():
            unknown = set(entry) - allowed
            assert not unknown, f"{faction}/{slug}: unknown fields {sorted(unknown)}"

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_scaffold_entries_stay_l0_clean(self, faction):
        """Unreviewed files carry scaffold fields ONLY — no half-done ratings."""
        if _meta(faction).get("human_reviewed"):
            return
        for slug, entry in _heuristic_detachments(faction).items():
            extra = set(entry) - L2_SCAFFOLD_FIELDS
            assert not extra, (
                f"{faction}/{slug}: unreviewed entry has L2 fields {sorted(extra)} "
                f"— commit reviews atomically with human_reviewed=true"
            )

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_strength_requires_justification(self, faction):
        for slug, entry in _heuristic_detachments(faction).items():
            if "strength" not in entry:
                continue
            assert entry["strength"] in L2_STRENGTHS, (
                f"{faction}/{slug}: strength {entry['strength']!r} not in {L2_STRENGTHS}"
            )
            notes = (entry.get("strength_notes") or "").strip()
            assert len(notes) >= 20, (
                f"{faction}/{slug}: strength without a real strength_notes justification"
            )
            lims = entry.get("limitations")
            assert isinstance(lims, list) and lims, (
                f"{faction}/{slug}: strength requires non-empty limitations"
            )
            assert all(str(l).strip() for l in lims), (
                f"{faction}/{slug}: limitations entries must be non-empty"
            )

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_strength_notes_traceable(self, faction):
        for slug, entry in _heuristic_detachments(faction).items():
            notes = entry.get("strength_notes") or ""
            if not notes:
                continue
            assert _traces_to_source(notes), (
                f"{faction}/{slug}: strength_notes must reference an L0 source "
                f"(URL or one of {L2_SOURCE_TOKENS}) — opinion without source "
                f"is fabrication"
            )

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_rule_is_paraphrase_not_verbatim(self, faction):
        for slug, entry in _heuristic_detachments(faction).items():
            rule = entry.get("rule")
            if not rule:
                continue
            text = (rule.get("text") or "").strip()
            assert text, f"{faction}/{slug}: rule.text is empty"
            assert rule.get("_paraphrase") is True, (
                f"{faction}/{slug}: rule.text must be flagged _paraphrase: true "
                f"(no verbatim GW rule text — AGENTS.md IP)"
            )
            assert rule.get("_lang") == "en", (
                f"{faction}/{slug}: rule.text must be English (_lang: en) "
                f"— paraphrases are written in English, never GW's phrasing or lore"
            )
            assert len(text) <= L2_RULE_TEXT_MAX, (
                f"{faction}/{slug}: rule.text {len(text)} chars > {L2_RULE_TEXT_MAX} "
                f"— looks like verbatim rule text, needs paraphrase"
            )
            affects = rule.get("affects")
            assert isinstance(affects, list) and affects, (
                f"{faction}/{slug}: rule.affects must list keywords/units"
            )
            src = rule.get("_source")
            assert isinstance(src, list) and src and all(s.strip() for s in src), (
                f"{faction}/{slug}: rule._source must list L0 source URLs"
            )

    @pytest.mark.parametrize("faction", FACTIONS)
    def test_reviewed_file_is_complete(self, faction):
        if not _meta(faction).get("human_reviewed"):
            pytest.skip(f"{faction}: not yet human-reviewed")
        for slug, entry in _heuristic_detachments(faction).items():
            assert entry.get("strength"), f"{faction}/{slug}: reviewed entry unrated"
            assert (entry.get("strength_notes") or "").strip(), (
                f"{faction}/{slug}: reviewed entry missing strength_notes"
            )
            assert entry.get("limitations"), (
                f"{faction}/{slug}: reviewed entry missing limitations"
            )
            assert entry.get("rule"), (
                f"{faction}/{slug}: reviewed entry missing rule"
            )

# ═══════════════════════════════════════════════════════════════════════
# TIER 6: HTML REVIEW WORKBOOK (browser-readable view of the review state)
# ═══════════════════════════════════════════════════════════════════════

class TestL2ReviewHtml:
    """docs/detachment-atlas/ is generated, deterministic, complete.

    Per-army pages (docs/detachment-atlas/<faction>.html) separate the
    L0-L4 layers; the JSON files remain the source of truth; the HTML is
    the browser view the human reviewer reads. Regenerate with
    `python3 scripts/gen_detach_review_html.py`.
    """

    def test_atlas_is_current(self):
        """Committed HTML must equal render output — no hand edits.

        Index page plus one page per faction, all byte-identical to the
        pure render functions (no drift between generator + committed HTML).
        """
        assert (ATLAS_DIR / "index.html").read_text() == render_index() + "\n"
        assert ATLAS_FACTIONS, "no factions found"
        for faction in ATLAS_FACTIONS:
            p = ATLAS_DIR / f"{faction}.html"
            assert p.exists(), f"{p}: per-army page missing — run gen script"
            assert p.read_text() == render_faction(faction) + "\n", (
                f"{p}: stale — run python3 scripts/gen_detach_review_html.py"
            )

    def test_atlas_is_deterministic(self):
        """Two renders are byte-identical (per faction + index)."""
        assert render_index() == render_index()
        for faction in ATLAS_FACTIONS:
            assert render_faction(faction) == render_faction(faction)

    def test_atlas_covers_all_detachments(self):
        """Every faction page lists every detachment card from the config."""
        for faction in ATLAS_FACTIONS:
            doc = render_faction(faction)
            dets = _heuristic_detachments(faction)
            assert dets, f"{faction}: no detachments in scaffold"
            for slug in dets:
                assert f"id='l2-{slug}'" in doc, (
                    f"{faction}/{slug}: card missing from atlas page"
                )

    def test_drafts_overlay_existing_slugs_only(self):
        """LLM drafts (workspace/, gitignored) may only overlay scaffold slugs.

        A draft that invents a detachment slug would corrupt the review state.
        Gracefully passes when no drafts exist yet.
        """
        for faction in FACTIONS:
            p = REPO_ROOT / "workspace" / "detachment-drafts" / f"{faction}.draft.json"
            if not p.exists():
                continue
            scaffold = _heuristic_detachments(faction)
            draft = json.loads(p.read_text()).get("detachments", {})
            unknown = set(draft) - set(scaffold)
            assert not unknown, (
                f"{faction}: draft invents slugs not in scaffold: {sorted(unknown)}"
            )

    def test_draft_l2_fields_match_scaffold(self):
        """Draft entries carry only L2 expert fields on top of scaffold keys
        (plus `rule` with `_paraphrase`/`_lang`), and rule.text <= 600 chars."""
        from scripts.gen_detach_review_html import L2_EXPERT_FIELDS, DRAFT_DIR

        for p in sorted(DRAFT_DIR.glob("*.draft.json")) if DRAFT_DIR.exists() else []:
            faction = p.name.removesuffix(".draft.json")
            scaffold = _heuristic_detachments(faction)
            if not scaffold:
                continue
            data = json.loads(p.read_text())
            allowed = {"_slug", "name", "dp_cost", "disposition", "objective", "source"} | L2_EXPERT_FIELDS
            for slug, entry in data.get("detachments", {}).items():
                assert slug in scaffold, f"{faction}/{slug}: not in scaffold"
                unknown = set(entry) - allowed
                assert not unknown, (
                    f"{faction}/{slug}: draft field outside scaffold+L2: {sorted(unknown)}"
                )
                rule = entry.get("rule", {})
                if rule:
                    assert rule.get("_paraphrase") is True, (
                        f"{faction}/{slug}: draft rule must flag _paraphrase"
                    )
                    assert rule.get("_lang") == "en", (
                        f"{faction}/{slug}: draft rule must be _lang 'en'"
                    )
                    assert len(rule.get("text", "")) <= 600, (
                        f"{faction}/{slug}: draft rule.text > 600 chars"
                    )
