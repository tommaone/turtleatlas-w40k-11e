"""Golden structure locks — daemon big-character wargear.

Pins the regenerated daemon character entries (chaos-daemons, thousand-sons,
world-eaters, emperors-children, death-guard) against the failure modes
fixed in commits 2909092 + follow-up EC Keeper fix:

- bundle choices ('Axe and flail', 'Axe and lash') must stay WHOLE — never
  flattened to their first nested component ('Bloodflail', 'Lash of Khorne')
- 'Plague flail' (Great Unclean One) must survive intact and resolve to the
  Plague flail profile — never the stripped 'flail' (which silently resolves
  to 'Bloodflail' S16 or 'Flail of corruption' S5)
- Daemon Princes must carry exactly Infernal cannon + Hellforged weapons
  (no strike/sweep double-count)
- canonical build schema {name, fixed, slots} only

STRUCTURE + NAME + COUNT assertions only — no damage numbers. The engine
stays the single source of computation.

Source of truth: data/config/*/characters.json (regenerated from BSData,
verified against Wahapedia 11ed, 2026-08-28).
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from engine.ranking import RankingEngine

REPO = Path(__file__).resolve().parent.parent

# The 16 regenerated entries (unit -> expected build shape).
TARGETS = {
    "chaos-daemons": ["Lord Of Change", "Bloodthirster", "Keeper Of Secrets",
                      "Great Unclean One", "Daemon Prince Of Chaos",
                      "Daemon Prince Of Chaos With Wings"],
    "thousand-sons": ["Lord Of Change", "Daemon Prince Of Tzeentch",
                      "Daemon Prince Of Tzeentch With Wings"],
    "world-eaters": ["Daemon Prince Of Khorne", "Daemon Prince Of Khorne With Wings"],
    "emperors-children": ["Daemon Prince Of Slaanesh", "Daemon Prince Of Slaanesh With Wings", "Keeper Of Secrets"],
    "death-guard": ["Great Unclean One", "Daemon Prince Of Nurgle",
                    "Daemon Prince Of Nurgle With Wings"],
}

CANONICAL_KEYS = {"name", "fixed", "slots"}


def _characters(faction: str) -> dict:
    with open(REPO / "data" / "config" / faction / "characters.json") as f:
        return json.load(f)


def _builds(faction: str, unit: str) -> list[dict]:
    chars = _characters(faction)
    return chars[unit]["weapon_options"]["builds"]


def _resolve(engine, name, MEQ):
    res = engine.resolve_loadout(name, MEQ)
    assert res is not None, f"{name}: no resolve"
    return res


def _names(weapons) -> list[str]:
    return sorted(w.name for w in weapons)


@pytest.fixture(scope="module")
def engines():
    return {faction: RankingEngine(faction) for faction in TARGETS}


class TestCanonicalSchema:
    """Every regenerated build is {name, fixed, slots} — no legacy keys."""

    @pytest.mark.parametrize("faction,unit", [
        (f, u) for f, units in TARGETS.items() for u in units
    ])
    def test_build_keys_canonical(self, faction, unit):
        for build in _builds(faction, unit):
            assert set(build.keys()) == CANONICAL_KEYS, (
                f"{faction}/{unit}: legacy keys leaked back in: {set(build) - CANONICAL_KEYS}"
            )


class TestBundlesNeverFlatten:
    """Bloodthirster: axe/flail/lash bundles whole + melee, never components."""

    @pytest.mark.parametrize("faction", ["chaos-daemons"])
    def test_slot_holds_bundles_not_components(self, faction):
        b = _builds(faction, "Bloodthirster")[0]
        slot = b["slots"][0]
        names = [c["name"] for c in slot["choices"]]
        assert names == ["Great axe of Khorne", "Axe and flail", "Axe and lash"], names
        # The flattened components must never reappear as separate choices.
        assert "Bloodflail" not in names and "Lash of Khorne" not in names

    def test_bundles_typed_melee(self):
        b = _builds("chaos-daemons", "Bloodthirster")[0]
        types = {c["name"]: c["type"] for c in b["slots"][0]["choices"]}
        assert types == {"Great axe of Khorne": "melee",
                         "Axe and flail": "melee",
                         "Axe and lash": "melee"}

    def test_ranged_pool_hellfire_only(self, engines, MEQ):
        _pts, ranged, _melee, _i, info = _resolve(engines["chaos-daemons"], "Bloodthirster", MEQ)
        assert _names(ranged) == ["Hellfire breath"]
        assert info.get("_n_combos", 0) == 3, "all three axe kits must be combinable"

    def test_bundles_reachable_as_melee(self, engines):
        """All three kits resolve as melee — not just the damage-picked axe."""
        for bundle in ("Great axe of Khorne", "Axe and flail", "Axe and lash"):
            w = engines["chaos-daemons"].W(bundle, unit_name="Bloodthirster", category="melee")
            assert w is not None, bundle


class TestLordOfChange:
    """Both factions: fixed Bolt of Change + Staff; Wargear slot 1-of-two."""

    @pytest.mark.parametrize("faction", ["chaos-daemons", "thousand-sons"])
    def test_fixed_and_slot(self, faction):
        b = _builds(faction, "Lord Of Change")[0]
        fixed = {(f["name"], f["type"]) for f in b["fixed"]}
        assert fixed == {("Bolt of Change", "ranged"), ("Staff of Tzeentch", "melee")}
        assert len(b["slots"]) == 1
        choices = {(c["name"], c["type"]) for c in b["slots"][0]["choices"]}
        assert choices == {("Rod of sorcery", "ranged"), ("Baleful sword", "melee")}

    @pytest.mark.parametrize("faction", ["chaos-daemons", "thousand-sons"])
    def test_resolves_pools(self, engines, MEQ, faction):
        _pts, ranged, melee, _i, info = _resolve(engines[faction], "Lord Of Change", MEQ)
        assert any("Bolt of Change" in w.name for w in ranged)
        assert any(w.name == "Staff of Tzeentch" for w in melee)
        assert info.get("_n_combos", 0) >= 1


class TestKeeper:
    """Fixed witchfire + claws + sword; Wargear whip/knife slot.

    Both chaos-daemons and emperors-children. The EC entry was shadowed by a
    stale weapon_options.json duplicate (with a non-weapon 'Shining aegis'
    choice and mis-typed 'Living whip') — the duplicate is gone and the
    engine MUST resolve the characters.json entry.
    """

    @pytest.mark.parametrize("faction", ["chaos-daemons", "emperors-children"])
    def test_fixed_and_slot(self, faction):
        b = _builds(faction, "Keeper Of Secrets")[0]
        fixed = {(f["name"], f["type"]) for f in b["fixed"]}
        assert fixed == {("Phantasmagoria", "ranged"),
                         ("Snapping claws", "melee"),
                         ("Witstealer sword", "melee")}
        choices = {(c["name"], c["type"]) for c in b["slots"][0]["choices"]}
        # Living whip is Ranged Weapons in the catalog (11ed whip attack).
        assert choices == {("Living whip", "ranged"), ("Ritual knife", "melee")}

    @pytest.mark.parametrize("faction", ["chaos-daemons", "emperors-children"])
    def test_resolves_pools(self, engines, MEQ, faction):
        _pts, ranged, melee, _i, info = _resolve(engines[faction], "Keeper Of Secrets", MEQ)
        assert any("Phantasmagoria" in w.name for w in ranged)
        for melee_name in ("Snapping claws", "Witstealer sword"):
            assert any(w.name == melee_name for w in melee), melee_name
        assert info.get("_n_combos", 0) >= 1

    def test_no_stale_weapon_options_shadow(self):
        """Engine dispatches weapon_options BEFORE characters — a stale Keeper
        entry there would shadow the regenerated characters.json build."""
        with open(REPO / "data" / "config" / "emperors-children" / "weapon_options.json") as f:
            wo = json.load(f)
        assert "Keeper Of Secrets" not in wo


class TestGreatUncleanOne:
    """Putrid vomit fixed; Bilesword/Bell + Plague flail/Bileblade slots.

    The Plague flail lock guards the normalize_for_catalog regression: the
    stripped 'flail' silently resolved to 'Bloodflail' (S16, chaos-daemons
    catalog) or 'Flail of corruption' (S5, death-guard catalog).
    """

    @pytest.mark.parametrize("faction", ["chaos-daemons", "death-guard"])
    def test_fixed_and_slots(self, faction):
        b = _builds(faction, "Great Unclean One")[0]
        assert [(f["name"], f["type"]) for f in b["fixed"]] == [("Putrid vomit", "ranged")]
        slot_names = [(s["name"], sorted((c["name"], c["type"]) for c in s["choices"]))
                      for s in b["slots"]]
        assert slot_names == [
            ("Bilesword / Bell", [("Bilesword", "melee"), ("Doomsday bell", "melee")]),
            ("Flail / Bileblade", [("Bileblade", "melee"), ("Plague flail", "ranged")]),
        ]

    @pytest.mark.parametrize("faction", ["chaos-daemons", "death-guard"])
    def test_plague_flail_never_stripped(self, faction):
        blob = json.dumps(_builds(faction, "Great Unclean One"))
        assert '"Plague flail"' in blob, "'Plague flail' must survive intact"
        assert '"flail"' not in blob.replace('"Plague flail"', ""), \
            "stripped 'flail' would fuzzy-resolve to the wrong catalog weapon"

    @pytest.mark.parametrize("faction", ["chaos-daemons", "death-guard"])
    def test_plague_flail_resolves_to_itself(self, engines, faction):
        w = engines[faction].W("Plague flail", unit_name="Great Unclean One",
                               category="ranged")
        assert w is not None and "plague flail" in w.name.lower(), w


class TestDaemonPrinces:
    """8 variants: exactly Infernal cannon + Hellforged weapons, no double-count."""

    @pytest.mark.parametrize("faction,unit", [
        (f, u) for f, units in TARGETS.items() for u in units
        if u.startswith("Daemon Prince")
    ])
    def test_fixed_exact_no_double_count(self, faction, unit):
        b = _builds(faction, unit)[0]
        fixed = [(f["name"], f["type"]) for f in b["fixed"]]
        if faction == "thousand-sons":
            # Tzeentch Princes add fixed Dark Blessing (ranged).
            assert fixed == [("Dark Blessing", "ranged"),
                             ("Infernal cannon", "ranged"),
                             ("Hellforged weapons", "melee")], fixed
        else:
            assert fixed == [("Infernal cannon", "ranged"),
                             ("Hellforged weapons", "melee")], fixed
        assert b["slots"] == [], f"{faction}/{unit}: unexpected slots"

    @pytest.mark.parametrize("faction,unit", [
        (f, u) for f, units in TARGETS.items() for u in units
        if u.startswith("Daemon Prince")
    ])
    def test_resolves_single_each(self, engines, MEQ, faction, unit):
        _pts, ranged, melee, _i, _info = _resolve(engines[faction], unit, MEQ)
        n_ranged = 1 if faction != "thousand-sons" else 2
        assert len(ranged) == n_ranged and "Infernal cannon" in ranged[-1].name, \
            [w.name for w in ranged]
        assert len(melee) == 1 and "Hellforged weapons" in melee[0].name

    def test_ts_princes_keep_dark_blessing(self, engines, MEQ):
        for unit in ("Daemon Prince Of Tzeentch", "Daemon Prince Of Tzeentch With Wings"):
            _pts, ranged, melee, _i, _info = _resolve(engines["thousand-sons"], unit, MEQ)
            assert any(w.name == "Dark Blessing" for w in ranged), unit
            assert len(melee) == 1 and "Hellforged weapons" in melee[0].name