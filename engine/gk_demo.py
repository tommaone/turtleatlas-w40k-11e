"""
GK DPP Demo — runs the 11e engine against real Grey Knights data.

Shows how Cover and Plunging Fire change DPP calculations.
"""

import json
import sys
from pathlib import Path

# Add parent for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.dpp import (
    WeaponProfile, TargetProfile, WeaponModifier,
    compute_weapon_dpp, compute_unit_dpp, HitMode,
)


def find_gk_unit(data: dict, name_fragment: str) -> dict | None:
    """Find a Grey Knights unit by name fragment."""
    for u in data["units"]:
        if name_fragment.lower() in u["name"].lower():
            return u
    return None


def weapon_to_profile(w: dict) -> WeaponProfile | None:
    """Convert a merged-data weapon dict to WeaponProfile."""
    # Stats might be in nested profiles
    stats = w
    if "profiles" in w:
        for prof in w["profiles"]:
            if "stats" in prof:
                stats = prof["stats"]
                break
    if "stats" in w:
        stats = w["stats"]

    # Parse attacks (might be 'D3+3', '2', '4', etc.)
    a_str = str(stats.get("A", stats.get("attacks", "1")))
    # Crude: grab first number
    import re
    a_match = re.search(r'(\d+)', a_str)
    attacks = float(a_match.group(1)) if a_match else 1.0
    # Handle D6, D3 etc.
    if "D" in a_str.upper() and "+" not in a_str:
        a_match = re.search(r'D(\d+)', a_str.upper())
        if a_match:
            attacks = (int(a_match.group(1)) + 1) / 2.0  # average of D6 = 3.5, D3 = 2

    # BS/WS
    bs_str = str(stats.get("BS", stats.get("bs", stats.get("WS", "4+"))))
    bs_str = bs_str.replace("+", "").replace('"', "").replace("N/A", "6")
    try:
        bs = int(bs_str)
    except ValueError:
        bs = 4

    # Strength
    s_str = str(stats.get("S", stats.get("strength", "4")))
    s_match = re.search(r'(\d+)', s_str)
    strength = int(s_match.group(1)) if s_match else 4

    # AP
    ap_str = str(stats.get("AP", stats.get("ap", "0")))
    ap_match = re.search(r'(-?\d+)', ap_str)
    ap = int(ap_match.group(1)) if ap_match else 0

    # Damage
    d_str = str(stats.get("D", stats.get("damage", "1")))
    d_match = re.search(r'(\d+)', d_str)
    damage = float(d_match.group(1)) if d_match else 1.0
    if "D" in d_str.upper() and "+" not in d_str:
        d_match = re.search(r'D(\d+)', d_str.upper())
        if d_match:
            damage = (int(d_match.group(1)) + 1) / 2.0

    # Abilities from Keywords field or abilities list
    kw = str(stats.get("Keywords", stats.get("keywords", "")))
    abilities = [a.strip() for a in kw.split(",")] if kw else w.get("abilities", [])

    return WeaponProfile(
        name=stats.get("name", w.get("name", "?")),
        attacks=attacks,
        bs=bs,
        strength=strength,
        ap=ap,
        damage=damage,
        abilities=abilities,
    )


def main():
    merged_path = Path(__file__).resolve().parent.parent / "data" / "merged" / "grey-knights.json"
    if not merged_path.exists():
        print(f"No merged data at {merged_path}")
        print("Run: python3 adapter/merge.py --faction grey-knights")
        return

    data = json.loads(merged_path.read_text())

    # Pick a real GK unit: Brotherhood Terminator Squad
    unit = find_gk_unit(data, "Terminator Squad")
    if not unit:
        print("No Terminator Squad found")
        return

    prof = unit.get("profile", {})
    weapons = prof.get("weapons", [])
    if not weapons:
        print(f"No weapons found for {unit['name']}")
        return

    # Get points
    pricing = unit.get("pricing", [])
    points = 0
    if pricing:
        costs = pricing[0].get("costs", [])
        if costs:
            points = costs[0].get("points", 0)

    # Find interesting ranged weapons (storm bolter, psilencer, psycannon, incinerator)
    interesting = []
    for w in weapons:
        name = w.get("name", "").lower()
        if any(x in name for x in ["storm bolter", "psilencer", "psycannon", "incinerator", "psyk"]):
            interesting.append(w)
    if not interesting:
        interesting = weapons[:5]

    print(f"=== {unit['name']} ({points} pts) ===")
    print()

    # Convert weapons to profiles
    profiles = [p for w in interesting if (p := weapon_to_profile(w))]

    # Target: MEQ (T4, 3+)
    meq = TargetProfile(toughness=4, save=3, invuln=None)
    # Target: TEQ (T5, 2+, 4++)
    teq = TargetProfile(toughness=5, save=2, invuln=4)

    for wp in profiles:
        print(f"Weapon: {wp.name}")
        print(f"  Stats: A{wp.attacks:.1f} BS{wp.bs}+ S{wp.strength} AP{wp.ap} D{wp.damage:.1f}")
        print(f"  Abilities: {wp.abilities}")
        print()

        for target_label, target in [("vs MEQ", meq), ("vs TEQ", teq)]:
            print(f"  {target_label}:")
            for mode_label, mode in [("Normal", HitMode.NORMAL),
                                     ("Cover (worsen BS)", HitMode.COVER),
                                     ("Plunging Fire", HitMode.PLUNGING_FIRE)]:
                r = compute_weapon_dpp(wp, target, unit_points=points, hit_mode=mode)
                print(f"    {mode_label:22s} D={r['total_damage']:<8.3f} DPP={r['dpp']:<8.5f} "
                      f"H={r['expected_hits']:<5.2f} W={r['regular_wounds']:<5.2f} MW={r['mortal_wounds']:<5.2f}")
            print()


if __name__ == "__main__":
    main()
