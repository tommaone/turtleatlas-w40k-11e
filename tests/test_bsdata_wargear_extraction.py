"""Golden test for BSData wargear slot extraction.

Verifies:
1. Parser extracts correct wargear slots from BSData selectionEntryGroups
2. Engine BSData fallback produces identical results to hand-curated config
3. Entry links (shared weapon references) are resolved

Golden truth: Defiler (Chaos Space Marines) has 4 independent weapon slots
with 64 combos, verified against Wahapedia 2026-08-21.

Run: python3 -m pytest tests/test_bsdata_wargear_extraction.py -v
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from adapter.bsdata_parser_11e import BSDataParser11e
from engine.ranking import RankingEngine

# ── Golden values ────────────────────────────────────────────────────────

FACTION_SLUG = "chaos-space-marines"
FACTION_BSNAME = "Chaos - Chaos Space Marines"
UNIT_NAME = "Defiler"

# Expected wargear structure
EXPECTED_FIXED = [{"name": "Shearing claws", "type": "melee"}]
EXPECTED_SLOTS = [
    {
        "name": "Replace heavy missile launcher",
        "choices": [
            {"name": "Heavy missile launcher", "type": "ranged"},
            {"name": "Electroscourge", "type": "melee"},
            {"name": "Hades lascannon", "type": "ranged"},
            {"name": "Heavy reaper autocannon", "type": "ranged"},
        ],
    },
    {
        "name": "Main cannon",
        "choices": [
            {"name": "Hades battle cannon", "type": "ranged"},
            {"name": "Ectoplasma destructor", "type": "ranged"},
        ],
    },
    {
        "name": "Replace heavy baleflamer",
        "choices": [
            {"name": "Heavy baleflamer", "type": "ranged"},
            {"name": "Electroscourge", "type": "melee"},
            {"name": "Hades lascannon", "type": "ranged"},
            {"name": "Heavy reaper autocannon", "type": "ranged"},
        ],
    },
    {
        "name": "Replace excruciator cannons",
        "choices": [
            {"name": "Two excruciator cannons", "type": "ranged"},
            {"name": "Two magma cutters", "type": "ranged"},
        ],
    },
]

EXPECTED_COMBOS = 4 * 2 * 4 * 2  # 64
EXPECTED_DPP_CURATED = 0.0760  # hand-curated baseline

# ── Khorne Lord of Skulls ───────────────────────────────────────────────

KLOS_BSNAME = "Khorne Lord of Skulls"  # BSData uses lowercase 'o'
KLOS_MERGED_NAME = "Khorne Lord Of Skulls"  # merged JSON capitalizes
KLOS_FIXED = [{"name": "Great cleaver of Khorne", "type": "melee"}]
KLOS_SLOTS = [
    {
        "name": "Hades gatling cannon",
        "choices": [
            {"name": "Hades gatling cannon", "type": "ranged"},
            {"name": "Skullhurler", "type": "ranged"},
        ],
    },
    {
        "name": "Gorestorm cannon",
        "choices": [
            {"name": "Gorestorm cannon", "type": "ranged"},
            {"name": "Daemongore cannon", "type": "ranged"},
            {"name": "Ichor cannon", "type": "ranged"},
        ],
    },
]
KLOS_DPP_CURATED = 0.0599

# ── Lord Discordant on Helstalker ────────────────────────────────────────

LD_BSNAME = "Lord Discordant on Helstalker"
LD_MERGED_NAME = "Lord Discordant On Helstalker"
LD_FIXED = [
    {"name": "Bladed limbs", "type": "melee"},
    {"name": "Impaler chainglaive", "type": "melee"},
    {"name": "Bolt pistol", "type": "ranged"},
]
LD_SLOTS = [
    {
        "name": "Autocannon or baleflamer",
        "choices": [
            {"name": "Helstalker autocannon", "type": "ranged"},
            {"name": "Baleflamer", "type": "ranged"},
        ],
    },
    {
        "name": "Injector or magma cutter",
        "choices": [
            {"name": "Techno-virus injector", "type": "melee"},
            {"name": "Magma cutter", "type": "ranged"},
        ],
    },
]
LD_DPP_CURATED = 0.0891

# ── Helbrute ─────────────────────────────────────────────────────────────
# Golden truth: verified against New Recruit wiki (11e) 2026-08-22.
# Two independent replace-groups: Missile launcher (5) x Multi-melta (7) = 35 combos.

HB_BSNAME = "Helbrute"
HB_MERGED_NAME = "Helbrute"
HB_FIXED = [{"name": "Close combat weapon", "type": "melee"}]
HB_SLOTS = [
    {
        "name": "Missile launcher",
        "choices": [
            {"name": "Helbrute fist with combi-bolter", "type": "ranged"},
            {"name": "Helbrute fist with heavy flamer", "type": "ranged"},
            {"name": "Missile launcher", "type": "ranged"},
            {"name": "Helbrute hammer", "type": "melee"},
            {"name": "Power scourge", "type": "melee"},
        ],
    },
    {
        "name": "Multi-melta",
        "choices": [
            {"name": "Multi-melta", "type": "ranged"},
            {"name": "Twin autocannon", "type": "ranged"},
            {"name": "Helbrute fist with heavy flamer", "type": "ranged"},
            {"name": "Helbrute fist with combi-bolter", "type": "ranged"},
            {"name": "Helbrute plasma cannon", "type": "ranged"},
            {"name": "Twin heavy bolter", "type": "ranged"},
            {"name": "Twin lascannon", "type": "ranged"},
        ],
    },
]
HB_DPP_CURATED = 0.0488

# ── Maulerfiend ──────────────────────────────────────────────────────────
# Golden truth: verified against New Recruit wiki (11e) + Goonhammer 2026-08-22.
# Fixed fists; 1 slot (Head weapons): 2 magma cutters or Lasher tendrils.

MF_BSNAME = "Maulerfiend"
MF_MERGED_NAME = "Maulerfiend"
MF_FIXED = [{"name": "Maulerfiend fists", "type": "melee"}]
MF_SLOTS = [
    {
        "name": "Head weapons",
        "choices": [
            {"name": "2 magma cutters", "type": "ranged"},
            {"name": "Lasher tendrils", "type": "melee"},
        ],
    },
]
MF_DPP_CURATED = 0.0444


@pytest.fixture(scope="module")
def parser():
    return BSDataParser11e()


@pytest.fixture(scope="module")
def extracted_slots(parser):
    """Extract wargear slots from BSData for Defiler."""
    data = parser.query_faction(FACTION_BSNAME)
    for u in data["units"]:
        if u["name"] == UNIT_NAME:
            return u.get("wargear_slots")
    pytest.fail(f"{UNIT_NAME} not found in BSData extraction")


@pytest.fixture(scope="module")
def csm_engine():
    return RankingEngine(FACTION_SLUG)


# ── Parser tests ─────────────────────────────────────────────────────────

class TestBSDataExtraction:
    """Parser-level: wargear slots extracted correctly from BSData."""

    def test_wargear_slots_present(self, extracted_slots):
        assert extracted_slots is not None, "wargear_slots should be extracted"

    def test_fixed_weapons(self, extracted_slots):
        assert extracted_slots["fixed"] == EXPECTED_FIXED

    def test_slot_count(self, extracted_slots):
        assert len(extracted_slots["slots"]) == len(EXPECTED_SLOTS)

    def test_slot_names(self, extracted_slots):
        got = [s["name"] for s in extracted_slots["slots"]]
        exp = [s["name"] for s in EXPECTED_SLOTS]
        assert got == exp

    def test_slot_choices(self, extracted_slots):
        """Each slot has the correct choices with names and types."""
        for exp_slot in EXPECTED_SLOTS:
            got_slot = next(
                s for s in extracted_slots["slots"] if s["name"] == exp_slot["name"]
            )
            got_choices = [(c["name"], c["type"]) for c in got_slot["choices"]]
            exp_choices = [(c["name"], c["type"]) for c in exp_slot["choices"]]
            assert got_choices == exp_choices, (
                f"Slot '{exp_slot['name']}': expected {exp_choices}, got {got_choices}"
            )

    def test_entry_links_resolved(self, extracted_slots):
        """Electroscourge, Hades lascannon, Heavy reaper autocannon are
        entryLinks in BSData — verify they appear as choices."""
        all_names = set()
        for slot in extracted_slots["slots"]:
            for c in slot["choices"]:
                all_names.add(c["name"])
        # These are shared entries referenced via entryLinks
        assert "Electroscourge" in all_names
        assert "Hades lascannon" in all_names
        assert "Heavy reaper autocannon" in all_names


# ── Engine tests ─────────────────────────────────────────────────────────

class TestEngineBSDataFallback:
    """Engine-level: BSData fallback matches hand-curated config."""

    def test_curated_dpp(self, csm_engine):
        """Hand-curated config produces expected DPP."""
        result = csm_engine.compute_ranking()
        defiler = next(u for u in result if u["name"] == UNIT_NAME)
        assert defiler["dpp"] == pytest.approx(EXPECTED_DPP_CURATED, abs=0.0001)
        assert defiler.get("n_combos") == EXPECTED_COMBOS

    def test_bsdata_fallback_matches_curated(self, csm_engine):
        """Removing curated config, BSData fallback produces identical DPP."""
        import copy

        orig_wo = copy.deepcopy(csm_engine.config.weapon_options)
        orig_vh = copy.deepcopy(csm_engine.config.vehicles)
        orig_sq = copy.deepcopy(csm_engine.config.squads)
        orig_ch = copy.deepcopy(csm_engine.config.characters)

        try:
            csm_engine.config.weapon_options.pop(UNIT_NAME, None)
            csm_engine.config.vehicles.pop(UNIT_NAME, None)
            csm_engine.config.squads.pop(UNIT_NAME, None)
            csm_engine.config.characters.pop(UNIT_NAME, None)

            result = csm_engine.compute_ranking()
            defiler = next(u for u in result if u["name"] == UNIT_NAME)

            assert defiler["dpp"] == pytest.approx(EXPECTED_DPP_CURATED, abs=0.0001)
            assert defiler.get("n_combos") == EXPECTED_COMBOS
        finally:
            csm_engine.config.weapon_options = orig_wo
            csm_engine.config.vehicles = orig_vh
            csm_engine.config.squads = orig_sq
            csm_engine.config.characters = orig_ch


# ── Khorne Lord of Skulls ───────────────────────────────────────────────

@pytest.fixture(scope="module")
def klos_extracted_slots(parser):
    """Extract wargear slots from BSData for Khorne Lord of Skulls."""
    data = parser.query_faction(FACTION_BSNAME)
    for u in data["units"]:
        if u["name"] == KLOS_BSNAME:
            return u.get("wargear_slots")
    pytest.fail(f"{KLOS_BSNAME} not found in BSData extraction")


class TestBSDataExtractionKLOS:
    """Parser-level: Khorne Lord of Skulls wargear extraction."""

    def test_wargear_slots_present(self, klos_extracted_slots):
        assert klos_extracted_slots is not None

    def test_fixed_weapons(self, klos_extracted_slots):
        assert klos_extracted_slots["fixed"] == KLOS_FIXED

    def test_slot_count(self, klos_extracted_slots):
        assert len(klos_extracted_slots["slots"]) == 2

    def test_slot_choices(self, klos_extracted_slots):
        for exp_slot in KLOS_SLOTS:
            got_slot = next(
                s for s in klos_extracted_slots["slots"] if s["name"] == exp_slot["name"]
            )
            got_choices = [(c["name"], c["type"]) for c in got_slot["choices"]]
            exp_choices = [(c["name"], c["type"]) for c in exp_slot["choices"]]
            assert got_choices == exp_choices


class TestEngineBSDataFallbackKLOS:
    """Engine-level: Khorne Lord of Skulls BSData fallback."""

    def test_curated_dpp(self, csm_engine):
        result = csm_engine.compute_ranking()
        klos = next(u for u in result if u["name"] == KLOS_MERGED_NAME)
        assert klos["dpp"] == pytest.approx(KLOS_DPP_CURATED, abs=0.0001)

    def test_bsdata_fallback_matches_dpp(self, csm_engine):
        """BSData fallback produces same DPP as curated config."""
        import copy

        orig_wo = copy.deepcopy(csm_engine.config.weapon_options)
        orig_vh = copy.deepcopy(csm_engine.config.vehicles)
        orig_sq = copy.deepcopy(csm_engine.config.squads)
        orig_ch = copy.deepcopy(csm_engine.config.characters)

        try:
            csm_engine.config.weapon_options.pop(KLOS_MERGED_NAME, None)
            csm_engine.config.vehicles.pop(KLOS_MERGED_NAME, None)
            csm_engine.config.squads.pop(KLOS_MERGED_NAME, None)
            csm_engine.config.characters.pop(KLOS_MERGED_NAME, None)

            result = csm_engine.compute_ranking()
            klos = next(u for u in result if u["name"] == KLOS_MERGED_NAME)
            assert klos["dpp"] == pytest.approx(KLOS_DPP_CURATED, abs=0.0001)
        finally:
            csm_engine.config.weapon_options = orig_wo
            csm_engine.config.vehicles = orig_vh
            csm_engine.config.squads = orig_sq
            csm_engine.config.characters = orig_ch


# ── Lord Discordant on Helstalker ────────────────────────────────────────

@pytest.fixture(scope="module")
def ld_extracted_slots(parser):
    """Extract wargear slots from BSData for Lord Discordant."""
    data = parser.query_faction(FACTION_BSNAME)
    for u in data["units"]:
        if u["name"] == LD_BSNAME:
            return u.get("wargear_slots")
    pytest.fail(f"{LD_BSNAME} not found in BSData extraction")


class TestBSDataExtractionLD:
    """Parser-level: Lord Discordant wargear extraction."""

    def test_wargear_slots_present(self, ld_extracted_slots):
        assert ld_extracted_slots is not None

    def test_fixed_weapons(self, ld_extracted_slots):
        assert ld_extracted_slots["fixed"] == LD_FIXED

    def test_slot_count(self, ld_extracted_slots):
        assert len(ld_extracted_slots["slots"]) == 2

    def test_slot_choices(self, ld_extracted_slots):
        for exp_slot in LD_SLOTS:
            got_slot = next(
                s for s in ld_extracted_slots["slots"] if s["name"] == exp_slot["name"]
            )
            got_choices = [(c["name"], c["type"]) for c in got_slot["choices"]]
            exp_choices = [(c["name"], c["type"]) for c in exp_slot["choices"]]
            assert got_choices == exp_choices


class TestEngineBSDataFallbackLD:
    """Engine-level: Lord Discordant BSData fallback."""

    def test_curated_dpp(self, csm_engine):
        result = csm_engine.compute_ranking()
        ld = next(u for u in result if u["name"] == LD_MERGED_NAME)
        assert ld["dpp"] == pytest.approx(LD_DPP_CURATED, abs=0.0001)

    def test_bsdata_fallback_matches_dpp(self, csm_engine):
        """BSData fallback produces same DPP as curated config."""
        import copy

        orig_ch = copy.deepcopy(csm_engine.config.characters)

        try:
            csm_engine.config.characters.pop(LD_MERGED_NAME, None)

            result = csm_engine.compute_ranking()
            ld = next(u for u in result if u["name"] == LD_MERGED_NAME)
            assert ld["dpp"] == pytest.approx(LD_DPP_CURATED, abs=0.0001)
        finally:
            csm_engine.config.characters = orig_ch


# ── Helbrute ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def hb_extracted_slots(parser):
    """Extract wargear slots from BSData for Helbrute."""
    data = parser.query_faction(FACTION_BSNAME)
    for u in data["units"]:
        if u["name"] == HB_BSNAME:
            return u.get("wargear_slots")
    pytest.fail(f"{HB_BSNAME} not found in BSData extraction")


class TestBSDataExtractionHB:
    """Parser-level: Helbrute wargear extraction."""

    def test_wargear_slots_present(self, hb_extracted_slots):
        assert hb_extracted_slots is not None

    def test_fixed_weapons(self, hb_extracted_slots):
        assert hb_extracted_slots["fixed"] == HB_FIXED

    def test_slot_count(self, hb_extracted_slots):
        assert len(hb_extracted_slots["slots"]) == 2

    def test_slot_choices(self, hb_extracted_slots):
        for exp_slot in HB_SLOTS:
            got_slot = next(
                s for s in hb_extracted_slots["slots"] if s["name"] == exp_slot["name"]
            )
            got_choices = [(c["name"], c["type"]) for c in got_slot["choices"]]
            exp_choices = [(c["name"], c["type"]) for c in exp_slot["choices"]]
            assert got_choices == exp_choices

    def test_melee_types_correct(self, hb_extracted_slots):
        """Hammer and scourge are melee — curated config had them wrong."""
        ml_slot = next(
            s
            for s in hb_extracted_slots["slots"]
            if s["name"] == "Missile launcher"
        )
        by_name = {c["name"]: c["type"] for c in ml_slot["choices"]}
        assert by_name["Helbrute hammer"] == "melee"
        assert by_name["Power scourge"] == "melee"


class TestEngineBSDataFallbackHB:
    """Engine-level: Helbrute BSData fallback."""

    def test_curated_dpp(self, csm_engine):
        result = csm_engine.compute_ranking()
        hb = next(u for u in result if u["name"] == HB_MERGED_NAME)
        assert hb["dpp"] == pytest.approx(HB_DPP_CURATED, abs=0.0001)

    def test_bsdata_fallback_matches_dpp(self, csm_engine):
        """BSData fallback produces same DPP as curated config."""
        import copy

        orig_wo = copy.deepcopy(csm_engine.config.weapon_options)

        try:
            csm_engine.config.weapon_options.pop(HB_MERGED_NAME, None)

            result = csm_engine.compute_ranking()
            hb = next(u for u in result if u["name"] == HB_MERGED_NAME)
            assert hb["dpp"] == pytest.approx(HB_DPP_CURATED, abs=0.0001)
        finally:
            csm_engine.config.weapon_options = orig_wo


# ── Maulerfiend ──────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def mf_extracted_slots(parser):
    """Extract wargear slots from BSData for Maulerfiend."""
    data = parser.query_faction(FACTION_BSNAME)
    for u in data["units"]:
        if u["name"] == MF_BSNAME:
            return u.get("wargear_slots")
    pytest.fail(f"{MF_BSNAME} not found in BSData extraction")


class TestBSDataExtractionMF:
    """Parser-level: Maulerfiend wargear extraction."""

    def test_wargear_slots_present(self, mf_extracted_slots):
        assert mf_extracted_slots is not None

    def test_fixed_weapons(self, mf_extracted_slots):
        assert mf_extracted_slots["fixed"] == MF_FIXED

    def test_slot_count(self, mf_extracted_slots):
        assert len(mf_extracted_slots["slots"]) == 1

    def test_slot_choices(self, mf_extracted_slots):
        got_slot = mf_extracted_slots["slots"][0]
        assert got_slot["name"] == MF_SLOTS[0]["name"]
        got_choices = [(c["name"], c["type"]) for c in got_slot["choices"]]
        exp_choices = [(c["name"], c["type"]) for c in MF_SLOTS[0]["choices"]]
        assert got_choices == exp_choices


class TestEngineBSDataFallbackMF:
    """Engine-level: Maulerfiend BSData fallback."""

    def test_curated_dpp(self, csm_engine):
        result = csm_engine.compute_ranking()
        mf = next(u for u in result if u["name"] == MF_MERGED_NAME)
        assert mf["dpp"] == pytest.approx(MF_DPP_CURATED, abs=0.0001)

    def test_bsdata_fallback_matches_dpp(self, csm_engine):
        """BSData fallback produces same DPP as curated config."""
        import copy

        orig_wo = copy.deepcopy(csm_engine.config.weapon_options)

        try:
            csm_engine.config.weapon_options.pop(MF_MERGED_NAME, None)

            result = csm_engine.compute_ranking()
            mf = next(u for u in result if u["name"] == MF_MERGED_NAME)
            assert mf["dpp"] == pytest.approx(MF_DPP_CURATED, abs=0.0001)
        finally:
            csm_engine.config.weapon_options = orig_wo
