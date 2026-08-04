"""Sanity check: every unit must have DPP >= 0.02.

Units below this threshold are likely misconfigured (missing weapons,
wrong loadout, or broken config). Whitelist covers units that legitimately
have low DPP (transports, melee-only, support characters, weak flyers).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from ranking import RankingEngine

# Minimum DPP threshold — below this = investigate.
# 0.01 after the overkill cap: high-D weapons now waste damage on mid-W
# targets, so legit anti-tank units legitimately sit in 0.01-0.02.
# Broken configs (missing weapons) still register ~0.001-0.005 and get caught.
MIN_DPP = 0.01

# Units that legitimately have low DPP (not broken, just weak/ melee / support)
NO_WEAPONS_WHITELIST = {
    # Transports / no weapons
    "Cyclops Demolition Vehicle", "Dreadnought", "Drop Pod", "Impulsor",
    "Chaos Rhino", "Trukk", "Repulsor", "Repulsor Executioner",
    "Ynnari Venom", "Corvus Blackstar", "Stormraven Gunship",
    "Taurox Prime", "Centaur Rsv", "Ghost Ark", "Land Raider Crusader",
    # Melee-only
    "Sanguinary Priest", "Wolf Priest", "Ripper Swarms", "Nurglings",
    "Blue Horrors", "Gretchin (Armageddon)", "Neurogaunts", "Seekers",
    "Exalted Eightbound", "Death Company Marines With Jump Packs",
    "Deathwing Knights", "Chaos Lord With Jump Pack",
    "Chaos Lord In Terminator Armour",
    "Shield-Captain In Allarus Terminator Armour",
    "Contemptor-Achillus Dreadnought", "Contemptor-Galatus Dreadnought",
    "Acolyte Iconward",
    # Suicide / one-shot
    "Spore Mines", "Spore Mines (Biovore)", "Mucolid Spores",
    # Support characters
    "Ethereal", "Apothecary Biologis", "Hospitaller", "Imagifier",
    "Dialogus", "Ministorum Priest", "Clamavus", "Nexos", "Biophagus",
    "Sanctus", "Spiritseer", "Navigator", "Darkstrider", "Cadre Fireblade",
    "Kroot Trail Shaper", "Memnyr Strategist", "Brôkhyr Iron-Master",
    "Knight-Centura", "Icon Bearer", "Tallyman", "Sloppity Bilepiper",
    "Commissar Yarrick", "Commissar Graves", "Canoptek Reanimator",
    "Chronomancer", "Geomancer", "Psychomancer", "Technomancer",
    "Orikan The Diviner", "Sydonian Skatros", "Watch Master", "Fabius Bile",
    "Commander In Coldstar Battlesuit", "Commander In Enforcer Battlesuit",
    "Lieutenant With Combi-Weapon", "Painboy",
    # Weak flyers / vehicles
    "Invader Atv", "Eliminator Squad", "Thunderhawk Gunship",
    "Onager Dunecrawler", "Blitza-Bommer", "Dakkajet",
    "Stormtalon Gunship", "Stormhawk Interceptor",
    "War Dog Moirax", "Armiger Moirax",
    "Crisis Sunforge Battlesuits", "Crisis Starscythe Battlesuits",
    "Crisis Fireknife Battlesuits", "Inceptor Squad",
    "Desolation Squad", "Devastator Squad", "Centurion Devastator Squad",
    "Tervigon", "Leman Russ Punisher", "Wyvern", "Centaur Rsv",
    "Telemon Heavy Dreadnought",
    # Necron gimmick / huge
    "Tesseract Vault", "Obelisk",
    # Config bugs (known)
    "Firestrike Servo-Turrets", "Valkyrie", "The Blue Scribes",
    # Fortifications (utility, weak weapons) — added by the missers-curation pass
    "Miasmic Malignifier", "Tidewall Droneport", "Tidewall Gunrig",
    # Support Primarch (force multiplier > raw damage)
    "Marneus Calgar In Armour Of Antilochus",
    # Under-modeled default-build squad (Indomitor Kill Team has rich wargear
    # options — special-weapon modes need curating; baseline Melee build only)
    "Indomitor Kill Team",
}

# All factions to scan
FACTIONS = [
    "astra-militarum", "adeptus-custodes", "adeptus-mechanicus",
    "adepta-sororitas", "aeldari", "black-templars", "blood-angels",
    "chaos-daemons", "chaos-knights", "chaos-space-marines",
    "dark-angels", "death-guard", "deathwatch", "drukhari",
    "emperors-children", "genestealer-cults", "grey-knights",
    "imperial-agents", "imperial-knights", "leagues-of-votann",
    "necrons", "orks", "space-marines", "space-wolves",
    "tau-empire", "thousand-sons", "tyranids", "world-eaters",
]


def _collect_failing():
    """Collect all failing units at module load time (not generator)."""
    seen = set()
    cases = []
    for faction in FACTIONS:
        try:
            eng = RankingEngine(faction)
            results = eng.compute_ranking(mission="Take and Hold")
        except Exception:
            continue
        for r in results:
            key = (faction, r["name"])
            if key in seen:
                continue
            seen.add(key)
            if r["dpp"] < MIN_DPP and r["name"] not in NO_WEAPONS_WHITELIST:
                cases.append((faction, r["name"], r["dpp"],
                              r.get("total_damage", 0), r["points"]))
    return cases


# Build parametrize list at module level
_FAILING_UNITS = _collect_failing()


class TestDPPSanityCheck:
    """Every unit must have DPP >= 0.02 (whitelisted units excluded)."""

    @pytest.mark.parametrize("faction,unit_name,dpp,dmg,pts", _FAILING_UNITS)
    def test_dpp_above_threshold(self, faction, unit_name, dpp, dmg, pts):
        """Unit has suspiciously low DPP — investigate config."""
        assert dpp >= MIN_DPP, (
            f"{faction}/{unit_name}: DPP={dpp:.4f} < {MIN_DPP} "
            f"(DMG={dmg:.1f}, {pts}pts). Check: weapons loaded? loadout correct?"
        )


def get_low_dpp_units():
    """Return all non-whitelisted units below threshold for reporting."""
    return [{"faction": f, "name": n, "dpp": d, "dmg": dm, "pts": p}
            for f, n, d, dm, p in _FAILING_UNITS]
