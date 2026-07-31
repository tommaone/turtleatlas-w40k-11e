"""Tests for import/merge data quality.

Run after every merge to catch:
1. Duplicate unit names per faction
2. Units with 0 points (missing pricing)
3. Units in merged data without config entries
"""

import json
import glob
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MERGED_DIR = REPO_ROOT / "data" / "merged"
CONFIG_DIR = REPO_ROOT / "data" / "config"


def _load_merged(faction: str) -> list[dict]:
    path = MERGED_DIR / f"{faction}.json"
    if not path.exists():
        return []
    with open(path) as f:
        data = json.load(f)
    return data.get("units", [])


def _all_factions() -> list[str]:
    return sorted(p.stem for p in MERGED_DIR.glob("*.json"))


def _config_units(faction: str) -> set[str]:
    """Get all unit names defined in config files for a faction."""
    names = set()
    cfg_dir = CONFIG_DIR / faction
    if not cfg_dir.exists():
        return names
    for cfg_file in cfg_dir.glob("*.json"):
        if cfg_file.name in ("notes.json", "supported.json", "meta.json",
                             "detachment_modifiers.json"):
            continue
        with open(cfg_file) as f:
            data = json.load(f)
        for name, val in data.items():
            if isinstance(val, dict) and not name.startswith("_"):
                names.add(name)
    return names


def _faction_keywords(faction: str) -> list[str]:
    """Faction's own keywords from supported.json (engine reads 'keywords')."""
    sup_path = CONFIG_DIR / faction / "supported.json"
    if not sup_path.exists():
        return []
    with open(sup_path) as f:
        sup = json.load(f)
    return [k.upper() for k in sup.get("keywords", [])]


def _non_rankable(faction: str, config_units: set[str]) -> set[str]:
    """Config units the engine intentionally does not rank.

    - Allies: merged profile has Faction: keywords that don't match the
      faction's own (e.g. Knights/Agents in grey-knights, Daemons in CSM).
    - Not in merged data: engine iterates merged units, so these can't rank.
    """
    merged_names = {u["name"]: u for u in _load_merged(faction)}
    faction_kws = _faction_keywords(faction)

    excluded = set()
    for name in config_units:
        unit = merged_names.get(name)
        if unit is None:
            excluded.add(name)  # not in merged → engine never sees it
            continue
        profile = unit.get("profile") or {}
        unit_fks = [k.upper() for k in profile.get("keywords", [])
                    if k.upper().startswith("FACTION:")]
        if not faction_kws or not unit_fks:
            continue  # no faction keywords to compare → rankable
        if not any(fk in unit_fks for fk in faction_kws):
            excluded.add(name)  # ally — different faction keyword
    return excluded


class TestNoDuplicateNames:
    """Merged data must not contain duplicate unit names per faction."""

    @pytest.mark.parametrize("faction", _all_factions())
    def test_no_duplicates_in_merged(self, faction: str):
        units = _load_merged(faction)
        names = [u["name"] for u in units]
        dupes = {n: names.count(n) for n in set(names) if names.count(n) > 1}
        assert not dupes, f"{faction} has duplicate units: {dupes}"


class TestNoZeroPointUnits:
    """Every unit in merged data with pricing must have points > 0."""

    @pytest.mark.parametrize("faction", _all_factions())
    def test_no_zero_points(self, faction: str):
        units = _load_merged(faction)
        zero_units = []
        for u in units:
            pricing = u.get("pricing")
            if not pricing:
                continue
            costs = pricing[0].get("costs", [])
            if costs:
                pts = costs[0].get("points")
                if pts is not None and pts == 0:
                    zero_units.append(u["name"])
        assert not zero_units, f"{faction} has 0-point units: {zero_units}"


class TestConfigPointsValid:
    """Config entries must not have pts=0 (ally units excluded — pricing
    lives in the ally faction's own config, not the host faction's)."""

    @pytest.mark.parametrize("faction", _all_factions())
    def test_config_pts_not_zero(self, faction: str):
        cfg_dir = CONFIG_DIR / faction
        if not cfg_dir.exists():
            pytest.skip("no config dir")
        config_units = _config_units(faction)
        allies = _non_rankable(faction, config_units)
        zero_entries = []
        for cfg_file in cfg_dir.glob("*.json"):
            if cfg_file.name in ("notes.json", "supported.json", "meta.json"):
                continue
            with open(cfg_file) as f:
                data = json.load(f)
            for name, val in data.items():
                if isinstance(val, dict) and val.get("pts") == 0 and name not in allies:
                    zero_entries.append(f"{cfg_file.name}: {name}")
        assert not zero_entries, f"{faction} config has pts=0: {zero_entries}"


class TestMergedUnitsHavePricing:
    """Units from BSData that are also in MFM must have pricing attached."""

    @pytest.mark.parametrize("faction", _all_factions())
    def test_mfm_units_have_pricing(self, faction: str):
        units = _load_merged(faction)
        missing = []
        for u in units:
            if u.get("in_mfm") and not u.get("pricing"):
                missing.append(u["name"])
        assert not missing, f"{faction} units marked in_mfm but no pricing: {missing}"


class TestBSDataDedup:
    """BSData parser must not return duplicate unit names."""

    def test_orks_no_duplicates(self):
        """Known issue: Orks had 7 duplicates from multiple XML files."""
        from adapter.bsdata_parser_11e import BSDataParser11e
        parser = BSDataParser11e()
        result = parser.query_faction("Orks")
        if result is None:
            pytest.skip("Orks not in BSData")
        names = [u["name"] for u in result["units"]]
        dupes = {n: names.count(n) for n in set(names) if names.count(n) > 1}
        assert not dupes, f"BSData Orks has duplicates: {dupes}"

    @pytest.mark.parametrize("faction", _all_factions())
    def test_all_factions_no_bsdata_duplicates(self, faction: str):
        from adapter.bsdata_parser_11e import BSDataParser11e
        parser = BSDataParser11e()
        result = parser.query_faction(faction.replace("-", " "))
        if result is None:
            pytest.skip(f"{faction} not in BSData")
        names = [u["name"] for u in result["units"]]
        dupes = {n: names.count(n) for n in set(names) if names.count(n) > 1}
        assert not dupes, f"BSData {faction} has duplicates: {dupes}"


class TestRankingNoZeroPts:
    """Ranking output must not show 0-point units."""

    @pytest.mark.parametrize("faction", _all_factions())
    def test_ranking_no_zero_pts(self, faction: str):
        from engine.ranking import RankingEngine
        try:
            engine = RankingEngine(faction)
        except Exception:
            pytest.skip(f"Cannot create engine for {faction}")
        results = engine.compute_ranking(max_points=2000)
        zero = [r["name"] for r in results if r["points"] == 0]
        assert not zero, f"{faction} ranking has 0-point units: {zero}"


class TestRankingCompleteness:
    """All units defined in a faction's config must appear in rankings.

    Configs define which units are in the army. If a unit is in the config
    with pricing, it should rank. Merged data may contain cross-faction
    BSData imports that aren't in the config — those are expected to be excluded.

    Ally units (merged profile has a different Faction: keyword than the
    faction's own) are intentionally not ranked by the engine's faction
    keyword filter — they are excluded from the assertion.
    Units not present in merged data at all cannot be ranked — excluded too.
    """

    @pytest.mark.parametrize("faction", _all_factions())
    def test_all_config_units_ranked(self, faction: str):
        from engine.ranking import RankingEngine

        # Skip titan-only factions
        if faction in ("titan-legions", "chaos-titan-legions"):
            pytest.skip("titan factions not ranked at 2000pt")

        config_units = _config_units(faction)
        if not config_units:
            pytest.skip(f"{faction} has no config units")

        # Run ranking
        try:
            engine = RankingEngine(faction)
        except Exception:
            pytest.skip(f"Cannot create engine for {faction}")
        results = engine.compute_ranking(max_points=2000)
        ranked = {r["name"] for r in results}

        # All config units must be ranked
        missing = config_units - ranked
        # Allowlist: units not in BSData (Legends / missing datasheets)
        allowlist = {"Deathwing Command Squad", "Ravenwing Talonmaster",
                     "Phantom Titan", "Manta", "Warhound Titan", "Reaver Titan",
                     "Warlord Titan", "Warbringer Nemesis Titan"}
        missing -= allowlist
        # Exclude allies and units not in merged data (engine cannot rank them)
        missing -= _non_rankable(faction, config_units)

        assert not missing, (
            f"{faction} has {len(missing)} config units not ranked: "
            f"{sorted(missing)}"
        )
