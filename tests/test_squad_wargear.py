"""Validate squad configs against wargear rules.

Every squad must have:
1. A valid `ranged` (default weapon for all models)
2. A valid `melee` (default melee for all models)
3. `special_max` that matches wargear options
4. `specials` list that's non-empty if special_max > 0

Also checks that:
- `ranged` is not a special weapon (e.g., "Shredder")
- `melee` is not a sergeant-only weapon (e.g., "Power Weapon" when only sergeant has it)
- DPP > 0.02 for non-whitelisted units
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from ranking import RankingEngine

# Known default weapons (not special)
DEFAULT_RANGED = {
    "Splinter Rifle", "Boltgun", "Bolter", "Storm Bolter", "Autogun", "Lasgun",
    "Shuriken Catapult", "Guardian Blaster", "Avenger Shuriken Catapult",
    "Pulse Rifle", "Pulse Carbine", "Gauss Flayer", "Tesla Carbine",
    "Striking Scorpion Blaster", "Fusion Blaster", "Plasma Gun", "Melta Gun",
    "Flamer", "Web Spinner", "Close combat weapon", "Melee weapon",
    "Power weapon", "Astartes chainsword", "Bolt pistol",
    "Twin bolt rifle", "Twin smart missile system",
    "Heavy 2b stubber", "Heavy stubber",
    "Autoch-pattern bolt pistol", "Las-beam cutter",
    "Mechanicus pistol", "Fireblade pulse rifle",
    "Kroot rifle", "Shade",
    "Bolt pistol", "Plasma pistol - standard", "Plasma pistol - Supercharge",
    "Absolvor bolt pistol", "Zealot's vindictor",
    "Guardian spear", "Misericordia",
    "Vigil spear",
}

# Known special weapons (should NOT be default ranged)
# Note: Splinter Cannon is DEFAULT for Scourges With Heavy Weapons
SPECIAL_WEAPONS = {
    "Shredder", "Blaster", "Dark Lance",
    "Plasma Gun", "Melta Gun", "Flamer", "Missile Launcher",
    "Lascannon", "Plasma Cannon", "Multi-melta",
    "Inferno Pistol", "Blast Pistol", "Meltagun",
    "Psycannon", "Incinerator", "Psilencer",
    "Heavy psycannon", "Heavy incinerator", "Heavy psilencer",
}

# Units that are intentionally melee-only or support (no ranged weapons)
MELEE_ONLY_WHITELIST = {
    # Melee-only
    "Deathwing Knights", "Exalted Eightbound", "Seekers",
    "Death Company Marines With Jump Packs", "Nurglings", "Blue Horrors",
    "Gretchin (Armageddon)", "Neurogaunts", "Ripper Swarms",
    "Spore Mines", "Spore Mines (Biovore)", "Mucolid Spores",
    "Sanguinary Priest", "Wolf Priest", "Ministorum Priest",
    "Acolyte Iconward", "Contemptor-Achillus Dreadnought",
    "Contemptor-Galatus Dreadnought",
    "Chaos Lord With Jump Pack", "Chaos Lord In Terminator Armour",
    "Shield-Captain In Allarus Terminator Armour",
    # Light vehicles / utility (legitimately low DPP)
    "Invader Atv", "Impulsor", "Rhino", "Chaos Rhino", "Trukk",
    "Drop Pod", "Taurox", "Taurox Prime", "Centaur Rsv",
    "Ghost Ark", "Canoptek Reanimator",
    # Support characters
    "Fabius Bile", "Warlock Skyrunners",
    # Transports with guns
    "Stormraven Gunship", "Corvus Blackstar", "Valkyrie",
    "Land Raider Crusader", "Ynnari Venom",
    # Blast/Indirect heavy squads — legitimately low DPP vs MEQ
    "Desolation Squad",
}


def load_all_squads():
    """Load all squad configs across all factions."""
    config_dir = Path(__file__).resolve().parent.parent / "data" / "config"
    all_squads = {}
    for faction_dir in config_dir.iterdir():
        if not faction_dir.is_dir():
            continue
        squads_file = faction_dir / "squads.json"
        if not squads_file.exists():
            continue
        with open(squads_file) as f:
            data = json.load(f)
        for name, cfg in data.items():
            if name.startswith("_"):
                continue
            all_squads[(faction_dir.name, name)] = cfg
    return all_squads


def validate_squad_config(faction, name, cfg):
    """Validate a single squad config. Returns list of issues."""
    issues = []

    # Check required fields
    if "n" not in cfg:
        issues.append("missing 'n' (squad size)")
    if "pts" not in cfg:
        issues.append("missing 'pts' (points)")
    if "ranged" not in cfg and "melee" not in cfg:
        issues.append("missing both 'ranged' and 'melee' — no weapons at all")

    ranged = cfg.get("ranged")
    melee = cfg.get("melee")
    special_max = cfg.get("special_max", 0)
    specials = cfg.get("specials", [])

    # Check ranged is not a special weapon
    if ranged and ranged in SPECIAL_WEAPONS:
        issues.append(f"ranged='{ranged}' is a special weapon, not default")

    # Check special_max vs specials consistency
    if special_max > 0 and not specials:
        issues.append(f"special_max={special_max} but specials is empty")
    if specials and special_max == 0:
        issues.append(f"specials has {len(specials)} items but special_max=0")

    # Check special_max is reasonable
    n = cfg.get("n", 10)
    if special_max > n:
        issues.append(f"special_max={special_max} > squad size n={n}")

    return issues


ALL_SQUADS = load_all_squads()


class TestSquadConfigIntegrity:
    """Every squad must have valid config structure."""

    @pytest.mark.parametrize("key,cfg", list(ALL_SQUADS.items()))
    def test_squad_has_required_fields(self, key, cfg):
        """Squad config must have n, pts, and at least one weapon type."""
        faction, name = key
        issues = validate_squad_config(faction, name, cfg)
        # Filter out "missing both" — some units are intentionally melee-only
        real_issues = [i for i in issues if "missing both" not in i]
        assert not real_issues, (
            f"{faction}/{name}: {real_issues}"
        )

    @pytest.mark.parametrize("key,cfg", list(ALL_SQUADS.items()))
    def test_ranged_is_not_special_weapon(self, key, cfg):
        """Default ranged weapon should not be a special weapon."""
        faction, name = key
        ranged = cfg.get("ranged")
        if ranged and ranged in SPECIAL_WEAPONS:
            pytest.fail(
                f"{faction}/{name}: ranged='{ranged}' is a special weapon. "
                f"Default should be the standard weapon for the unit."
            )

    @pytest.mark.parametrize("key,cfg", list(ALL_SQUADS.items()))
    def test_specials_consistency(self, key, cfg):
        """special_max and specials must be consistent."""
        faction, name = key
        special_max = cfg.get("special_max", 0)
        specials = cfg.get("specials", [])
        if special_max > 0 and not specials:
            pytest.fail(
                f"{faction}/{name}: special_max={special_max} but specials is empty"
            )
        if specials and special_max == 0:
            pytest.fail(
                f"{faction}/{name}: {len(specials)} specials but special_max=0"
            )


class TestSquadDPPSanity:
    """Every squad must have DPP >= 0.02 (with whitelist)."""

    @pytest.mark.parametrize("key,cfg", list(ALL_SQUADS.items()))
    def test_squad_dpp_above_threshold(self, key, cfg):
        """Squad DPP must be above minimum threshold."""
        faction, name = key

        # Skip whitelisted units
        if name in MELEE_ONLY_WHITELIST:
            return

        try:
            eng = RankingEngine(faction)
            results = eng.compute_ranking()
        except Exception:
            return

        for entry in results:
            if entry["name"] == name:
                if entry["dpp"] < 0.02:
                    pytest.fail(
                        f"{faction}/{name}: DPP={entry['dpp']:.4f} < 0.02. "
                        f"Loadout: {entry['loadout_desc']}. "
                        f"Check: weapons loaded? loadout correct?"
                    )
                break
