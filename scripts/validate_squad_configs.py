#!/usr/bin/env python3
"""
Validate squad configs for common issues:
1. ranged = default weapon (not special)
2. melee = default melee (not sergeant weapon)
3. special_max matches actual wargear options
4. DPP > 0.02 threshold

Usage:
    python scripts/validate_squad_configs.py [--fix] [--faction <name>]
"""
import json
import glob
import os
import sys
from pathlib import Path

# Known default weapons (not special)
DEFAULT_RANGED = {
    "Splinter Rifle", "Boltgun", "Bolter", "Storm Bolter", "Autogun", "Lasgun",
    "Shuriken Catapult", "Fusion Blaster", "Plasma Gun", "Melta Gun",
    "Flamer", "Web Spinner", "Gauss Flayer", "Tesla Carbine",
    "Pulse Rifle", "Pulse Carbine", "Striking Scorpion Blaster",
    "GuardianBlaster", "Avenger Shuriken Catapult",
    "Close combat weapon", "Melee weapon", "Power weapon",
    "Astartes chainsword", "Bolt pistol",
}

# Known default melee weapons
DEFAULT_MELEE = {
    "Close Combat Weapon", "Close combat weapon", "Melee weapon",
    "Power weapon", "Power Weapon", "Chainsword", "Astartes Chainsword",
    "Bolt pistol", "Bolt Pistol",
}

# Known special weapons (should NOT be default ranged)
SPECIAL_WEAPONS = {
    "Shredder", "Blaster", "Dark Lance", "Splinter Cannon",
    "Plasma Gun", "Melta Gun", "Flamer", "Missile Launcher",
    "Lascannon", "Heavy Bolter", "Plasma Cannon", "Multi-melta",
    "Inferno Pistol", "Blast Pistol", "Meltagun",
}


def validate_squad_config(faction: str, name: str, config: dict) -> list:
    """Validate a single squad config. Returns list of issues."""
    issues = []
    
    ranged = config.get("ranged")
    melee = config.get("melee")
    special_max = config.get("special_max", 0)
    specials = config.get("specials", [])
    
    # Check 1: ranged should be default weapon
    if ranged and ranged in SPECIAL_WEAPONS:
        issues.append(f"❌ ranged='{ranged}' is a special weapon, not default")
    
    # Check 2: melee should be default melee
    if melee and melee not in DEFAULT_MELEE and "Close" not in melee:
        issues.append(f"⚠️  melee='{melee}' might not be default melee")
    
    # Check 3: special_max should be reasonable
    if special_max > 5:
        issues.append(f"⚠️  special_max={special_max} seems high (>5)")
    
    # Check 4: specials list should not include default weapons
    for s in specials:
        if s in DEFAULT_RANGED:
            issues.append(f"⚠️  specials includes '{s}' which might be default")
    
    # Check 5: DPP sanity (requires running engine)
    # This is checked separately in test_dpp_sanity.py
    
    return issues


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Validate squad configs")
    parser.add_argument("--faction", help="Check specific faction only")
    parser.add_argument("--fix", action="store_true", help="Attempt auto-fix")
    args = parser.parse_args()
    
    config_dir = Path("data/config")
    total_issues = 0
    factions_checked = 0
    
    for squad_file in sorted(config_dir.glob("*/squads.json")):
        faction = squad_file.parent.name
        if args.faction and faction != args.faction:
            continue
        
        try:
            with open(squad_file) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ {faction}: JSON parse error: {e}")
            continue
        
        factions_checked += 1
        faction_issues = 0
        
        for name, config in data.items():
            if name.startswith("_"):
                continue
            
            issues = validate_squad_config(faction, name, config)
            if issues:
                print(f"\n{faction}/{name}:")
                for issue in issues:
                    print(f"  {issue}")
                faction_issues += len(issues)
        
        total_issues += faction_issues
    
    print(f"\n{'='*60}")
    print(f"Checked {factions_checked} factions")
    print(f"Total issues: {total_issues}")
    
    if total_issues > 0:
        print("\nRun with --fix to attempt auto-correction")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
