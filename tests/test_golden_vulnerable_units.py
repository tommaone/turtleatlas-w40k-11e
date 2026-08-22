"""Golden data tests — most vulnerable units (2026-08-22 audit grind).

Pins engine output for the 18 NO_CURATED configs generated from BSData,
plus structural guards for the bug classes fixed in the audit grind:

- missing "slots" key -> silent zero damage in _resolve_slots_build
- stale dual-entry configs (characters.json vs weapon_options.json)
- name normalization drift (plasma pistol variants, Two plaguespitters)

Single source of computation: tests call compute_ranking and never
re-implement math. Golden values live in test_golden_vulnerable_units.json
(captured 2026-08-22). If the engine legitimately improves, regenerate.

Run: python3 -m pytest tests/test_golden_vulnerable_units.py -v
"""

import json
from pathlib import Path

import pytest

CONFIG = Path(__file__).resolve().parent.parent / "data" / "config"
GOLDEN_FILE = Path(__file__).resolve().parent / "test_golden_vulnerable_units.json"
DATA = json.loads(GOLDEN_FILE.read_text())
MISSION = DATA["mission"]

_engines = {}


def _engine(slug):
    from engine.ranking import RankingEngine
    if slug not in _engines:
        _engines[slug] = RankingEngine(slug)
    return _engines[slug]


def _row(slug, name):
    res = _engine(slug).compute_ranking(mission=MISSION)
    hits = [r for r in res if str(r.get("name", "")).lower() == name.lower()]
    assert hits, f"{slug}: {name} not ranked"
    return hits[0]


def _parse_key(key):
    slug, name = key.split("|", 1)
    return slug, name


class TestGoldenUnblockedUnits:
    """The 18 formerly-NO_CURATED units keep their engine output."""

    @pytest.mark.parametrize("key", sorted(DATA["golden"]))
    def test_golden_dpp_and_points(self, key):
        slug, name = _parse_key(key)
        exp = DATA["golden"][key]
        row = _row(slug, name)
        assert float(row["dpp"]) == pytest.approx(exp["dpp"], abs=1e-4)
        assert int(row["points"]) == exp["pts"]


class TestCrossFactionParity:
    """Shared datasheets must resolve identically across factions."""

    def test_land_raider_crusader_parity(self):
        parity = DATA["parity_lrc"]
        rows = {slug: float(_row(slug, "Land Raider Crusader")["dpp"])
                for slug in parity}
        vals = list(rows.values())
        assert max(vals) - min(vals) < 1e-6, f"LRC parity drift: {rows}"


class TestStructuralGuards:
    """Kill the zero-damage bug class at the schema level."""

    @pytest.mark.parametrize("fname", ["weapon_options.json", "vehicles.json"])
    def test_every_build_has_explicit_slots_key(self, fname):
        offenders = []
        for cfg_dir in sorted(CONFIG.iterdir()):
            fpath = cfg_dir / fname
            if not fpath.exists():
                continue
            data = json.loads(fpath.read_text())
            for key, val in data.items():
                if key.startswith("_") or not isinstance(val, dict):
                    continue
                builds = (val.get("builds")
                          or val.get("weapon_options", {}).get("builds", []))
                for b in builds:
                    if isinstance(b, dict) and "models" not in b and "slots" not in b:
                        offenders.append(f"{cfg_dir.name}/{key}")
        assert not offenders, (
            f"builds without explicit slots key (zero-damage risk): {offenders}"
        )

    def test_generated_configs_have_info_block(self):
        """The 18 unblocked units need info (T/SV/W) for get_unit_info."""
        for key in DATA["golden"]:
            slug, name = _parse_key(key)
            data = json.loads((CONFIG / slug / "weapon_options.json").read_text())
            assert name in data, f"{slug}/{name} missing from weapon_options.json"
            info = data[name].get("info", {})
            assert info.get("T"), f"{slug}/{name}: info block missing T"
            assert info.get("SV"), f"{slug}/{name}: info block missing SV"
            assert info.get("W"), f"{slug}/{name}: info block missing W"


def _norm(s):
    return (s.lower().replace("'", "").replace("\u2019", "")
            .replace("-", " ").replace("  ", " ").strip())


class TestDualEntrySync:
    """characters.json must never hold a stale copy of a weapon_options unit.

    The engine reads weapon_options first, so a stale characters entry is
    invisible at rank time but rots audit comparisons and confuses tooling.
    """

    def test_characters_mirror_weapon_options_builds(self):
        stale = []
        for cfg_dir in sorted(CONFIG.iterdir()):
            wo_p = cfg_dir / "weapon_options.json"
            ch_p = cfg_dir / "characters.json"
            if not (wo_p.exists() and ch_p.exists()):
                continue
            wo = json.loads(wo_p.read_text())
            ch = json.loads(ch_p.read_text())
            wo_norm = {_norm(k): k for k in wo
                       if not k.startswith("_") and isinstance(wo[k], dict)}
            for ck, cv in ch.items():
                if ck.startswith("_") or not isinstance(cv, dict):
                    continue
                wk = wo_norm.get(_norm(ck))
                if wk is None:
                    continue

                def _names(entry):
                    builds = (entry.get("builds")
                              or entry.get("weapon_options", {}).get("builds", []))
                    out = set()
                    for b in builds:
                        for f in b.get("fixed", []):
                            out.add(_norm(f["name"]))
                        for s in b.get("slots", []):
                            for c in s.get("choices", []):
                                out.add(_norm(c["name"]))
                    return out

                if _names(cv) != _names(wo[wk]):
                    stale.append(f"{cfg_dir.name}/{ck}")
        assert not stale, f"stale dual-entry configs: {stale}"


class TestNameNormalizationGoldens:
    """Choices renamed during the grind keep their BSData names."""

    def test_klos_cannon_choices(self):
        data = json.loads((CONFIG / "world-eaters" / "weapon_options.json").read_text())
        names = set()
        for b in data["Khorne Lord Of Skulls"]["builds"]:
            for s in b.get("slots", []):
                names |= {c["name"] for c in s["choices"]}
        assert {"Hades gatling cannon", "Daemongore cannon", "Skullhurler"} <= names

    def test_bloat_drone_two_plaguespitters(self):
        data = json.loads((CONFIG / "death-guard" / "weapon_options.json").read_text())
        ch = data["Foetid Bloat Drone"]
        names = {c["name"].lower() for b in ch["builds"]
                 for s in b.get("slots", []) for c in s["choices"]}
        assert "two plaguespitters" in names
        assert not any(n.startswith("2 ") for n in names), names

    def test_warboss_has_attack_squig_slot(self):
        data = json.loads((CONFIG / "orks" / "characters.json").read_text())
        wb = data["Warboss"]["weapon_options"]["builds"][0]
        slot_names = {s["name"] for s in wb["slots"]}
        assert any("squig" in n.lower() for n in slot_names), slot_names

    def test_dc_dread_blood_talons_in_melee_slot(self):
        data = json.loads((CONFIG / "blood-angels" / "weapon_options.json").read_text())
        ch = data["Death Company Dreadnought"]
        melee_choices = set()
        fixed = set()
        for b in ch["builds"]:
            fixed |= {f["name"].lower() for f in b.get("fixed", [])}
            for s in b.get("slots", []):
                if "melee" in s["name"].lower():
                    melee_choices |= {c["name"].lower() for c in s["choices"]}
        assert "blood talons" in melee_choices, melee_choices
        row = _row("blood-angels", "Death Company Dreadnought")
        assert float(row["dpp"]) > 0
