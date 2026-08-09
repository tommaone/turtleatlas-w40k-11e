"""Tests for the squad composition generator (scripts/gen_squad_composition.py).

Verifies count allocation from squad size n:
- leaders (min == 1) get fixed count 1
- a single pool type becomes a flat model entry (count = budget)
- multiple pool types become ONE alloc model (parallel variants)
- units whose pool cannot reach the squad size are skipped (capacity guard)

Run: python3 -m pytest tests/test_gen_squad_composition.py -v
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _load_gen_module():
    path = Path(__file__).resolve().parent.parent / "scripts" / "gen_squad_composition.py"
    spec = importlib.util.spec_from_file_location("gen_squad_composition", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def gen():
    return _load_gen_module()


@pytest.fixture(scope="module")
def composition():
    from adapter.bsdata_parser_11e import BSDataParser11e
    return BSDataParser11e().extract_squad_composition("Aeldari")


@pytest.fixture(scope="module")
def sm_composition():
    """Space Marines composition — used by the case-insensitive exact-match
    regression (Eradicator Squad With Heavy Bolters must NOT resolve to the
    base Eradicator Squad's melta payload)."""
    from adapter.bsdata_parser_11e import BSDataParser11e
    return BSDataParser11e().extract_squad_composition("space-marines")


def _comp_for(composition, name):
    for bs_name, data in composition.items():
        if name.lower() in bs_name.lower() or bs_name.lower() in name.lower():
            return data
    return None


def test_troupe_emits_alloc(gen, composition):
    """Troupe n=5: Lead Player (min=1) + Player alloc model with budget 4."""
    build = gen.make_build({"n": 5}, _comp_for(composition, "Troupe"))
    assert build is not None
    alloc_m = [m for m in build["models"] if m.get("alloc")]
    assert len(alloc_m) == 1
    am = alloc_m[0]
    assert am["name"] == "Player"
    assert am["count"] == 4
    variants = {v["name"] for v in am["alloc"]}
    assert variants == {
        "Player with Harlequin's Blade",
        "Player with Harlequin's Special Weapon",
        "Player with Fusion Pistol",
        "Player with Neuro Disruptor",
    }
    blade = [v for v in am["alloc"] if v["name"] == "Player with Harlequin's Blade"][0]
    assert blade["min"] == 0 and blade["max"] == 11
    lead = [m for m in build["models"] if m["name"] == "Lead Player"][0]
    assert lead["count"] == 1


def test_windriders_emits_alloc(gen, composition):
    """Windriders n=3: no leader, alloc over 3 weapon variants, budget 3."""
    build = gen.make_build({"n": 3}, _comp_for(composition, "Windriders"))
    assert build is not None
    am = build["models"][0]
    assert am["name"] == "Windrider"
    assert am["count"] == 3
    assert len(am["alloc"]) == 3
    assert all(v.get("max") == 6 for v in am["alloc"])


def test_storm_guardians_keeps_mins(gen, composition):
    """Storm Guardians n=11: Serpent's Scale leader + alloc budget 10, base
    variant keeps min=4, specials keep max=2."""
    build = gen.make_build({"n": 11}, _comp_for(composition, "Storm Guardians"))
    assert build is not None
    am = [m for m in build["models"] if m.get("alloc")][0]
    assert am["count"] == 10
    base = [v for v in am["alloc"] if v["name"] == "Storm Guardian"][0]
    assert base["min"] == 4 and base["max"] == 10
    specials = [v for v in am["alloc"] if v["name"] != "Storm Guardian"]
    assert len(specials) == 5
    assert all(v["max"] == 2 for v in specials)
    assert [m["name"] for m in build["models"] if m.get("count") == 1] == [
        "Serpent's Scale Platform",
    ]


def test_ynnari_reavers_leader_and_pool(gen, composition):
    """Ynnari Reavers n=3: Arena Champion leader + alloc budget 2 over
    [Reaver min=2, Blaster max=1, Heat Lance max=1]."""
    build = gen.make_build({"n": 3}, _comp_for(composition, "Ynnari Reavers"))
    assert build is not None
    am = [m for m in build["models"] if m.get("alloc")][0]
    assert am["count"] == 2
    reaver = [v for v in am["alloc"] if v["name"] == "Reaver"][0]
    assert reaver["min"] == 2
    assert [m["name"] for m in build["models"] if m.get("count") == 1] == [
        "Arena Champion",
    ]


def test_voidscarred_nested_pool_alloc(gen, composition):
    """Corsair Voidscarred n=5: Felarch leader + alloc budget 4 over the
    nested base pool. Base variants carry pool_min=4 (the nested 'Voidscarred'
    SEG min), so the engine forces all 4 models into the base pool and the
    capped specials get none."""
    build = gen.make_build({"n": 5}, _comp_for(composition, "Corsair Voidscarred"))
    assert build is not None
    am = [m for m in build["models"] if m.get("alloc")][0]
    assert am["name"] == "Voidscarred"
    assert am["count"] == 4
    base = [v for v in am["alloc"] if v.get("pool_min")]
    assert len(base) == 7
    assert all(v["pool_min"] == 4 for v in base)
    specials = [v for v in am["alloc"] if not v.get("pool_min")]
    assert len(specials) == 3  # Shade Runner, Soul Weaver, Way Seeker
    assert all(v["max"] == 1 for v in specials)
    assert [m["name"] for m in build["models"] if m.get("count") == 1] == [
        "Voidscarred Felarch",
    ]


def test_warlock_conclave_multi_weapon_lists(gen, composition):
    """Warlock Conclave n=2: per-variant fixed weapons emit as LISTS when a
    model carries 2+ fixed weapons (regression: parser used to collapse to
    `[0]`). Singing Spear is dual-profile — the spear lands in ranged AND
    melee, so the Singing Spear variant always has a melee profile."""
    build = gen.make_build({"n": 2}, _comp_for(composition, "Warlock Conclave"))
    assert build is not None
    am = [m for m in build["models"] if m.get("alloc")][0]
    variants = {v["name"]: v for v in am["alloc"]}
    assert set(variants) == {
        "Warlock with Witchblade",
        "Warlock with Singing Spear",
    }
    witchblade = variants["Warlock with Witchblade"]
    assert witchblade["ranged"] == ["Shuriken Pistol", "Destructor"]
    assert witchblade["melee"] == "Witchblade"
    singing = variants["Warlock with Singing Spear"]
    assert singing["ranged"] == ["Singing Spear", "Shuriken Pistol", "Destructor"]
    assert singing["melee"] == "Singing Spear"  # spear's melee half kept


def test_warlock_skyrunner_four_weapon_payload(gen, composition):
    """Warlock Skyrunners n=1: Singing Spear variant carries FOUR fixed ranged
    weapons (Twin Shuriken Catapult + Pistol + Destructor + Spear), all kept
    in emission order, PLUS the spear's melee half."""
    build = gen.make_build({"n": 1}, _comp_for(composition, "Warlock Skyrunners"))
    assert build is not None
    am = [m for m in build["models"] if m.get("alloc")][0]
    singing = [v for v in am["alloc"]
               if v["name"] == "Warlock Skyrunner with Singing Spear"][0]
    assert singing["ranged"] == [
        "Shuriken Pistol",
        "Twin Shuriken Catapult",
        "Destructor",
        "Singing Spear",
    ]
    assert singing["melee"] == "Singing Spear"


def test_single_pool_flat_dark_reapers(gen, composition):
    """Dark Reapers n=5: single pool type → flat model, not alloc."""
    build = gen.make_build({"n": 5}, _comp_for(composition, "Dark Reapers"))
    assert build is not None
    assert not any(m.get("alloc") for m in build["models"])
    dr = [m for m in build["models"] if m.get("count") == 4][0]
    assert dr["name"] == "Dark Reaper"
    ex = [m for m in build["models"] if m.get("count") == 1][0]
    assert ex["name"] == "Dark Reaper Exarch"


def test_case_insensitive_exact_match_heavy_bolters(gen, sm_composition):
    """Regression: 'Eradicator Squad With Heavy Bolters' must resolve to the
    heavy-bolter composition, NOT the base 'Eradicator Squad' melta payload.

    The old code fell through to substring matching (bs_name in unit_name)
    and would have written melta rifles into the heavy-bolter squad.
    """
    heavy = gen.fuzzy_find_composition(
        sm_composition, "Eradicator Squad With Heavy Bolters"
    )
    assert heavy is not None
    assert "Eradicator Squad with Heavy Bolters" in sm_composition
    models = {m["name"]: m for m in heavy["builds"][0]["models"]}
    flat = json.dumps(heavy)
    assert "Multi-melta" not in flat
    assert "Melta rifle" not in flat
    assert models["Eradicator"]["ranged"] == ["Heavy Bolter", "Bolt pistol"]
    assert models["Eradicator Sergeant"]["ranged"] == ["Heavy Bolter", "Bolt pistol"]


def test_case_insensitive_exact_match_keeps_base(gen, sm_composition):
    """The base 'Eradicator Squad' still resolves to its own melta entry."""
    base = gen.fuzzy_find_composition(sm_composition, "Eradicator Squad")
    assert base is not None
    assert "Heavy Bolter" not in json.dumps(base)


def test_alloc_model_name_deterministic_tiebreak(gen):
    """Tie-break: 'Outrider' vs 'Invader ATV' both count 1 — the base name
    (shortest) must win deterministically, NOT hash-order."""
    assert gen._alloc_model_name(["Outrider", "Invader ATV"]) == "Outrider"
    assert gen._alloc_model_name(["Invader ATV", "Outrider"]) == "Outrider"
    # most-frequent still wins when no tie
    mixed = [
        "Assault Intercessors with Jump Pack",
        "Assault Intercessors with Jump Pack w/ Plasma Pistol",
        "Assault Intercessors with Jump Pack",
    ]
    assert gen._alloc_model_name(mixed) == "Assault Intercessors"


def test_alloc_model_name_player_unchanged(gen):
    """Troupe-style parallel variants keep 'Player' as the base name."""
    assert gen._alloc_model_name(
        [
            "Player with Harlequin's Blade",
            "Player with Harlequin's Special Weapon",
            "Player with Fusion Pistol",
            "Player with Neuro Disruptor",
        ]
    ) == "Player"
