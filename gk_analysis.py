"""
GK mission analysis — detachment DPP impact per disposition.
Mirrors ck_analysis.py structure for Grey Knights.
"""
from engine.ranking import RankingEngine
from engine.dpp import compute_weapon_dpp, WeaponProfile, WeaponModifier, TargetProfile, HitMode, UnitDefense, compute_surv
import json, sys

engine = RankingEngine("grey-knights")

targets = {
    "GEQ": engine.config.target_profiles["GEQ"],
    "MEQ": engine.config.target_profiles["MEQ"],
    "TEQ": engine.config.target_profiles["TEQ"],
    "Light V": engine.config.target_profiles["Light V"],
    "Heavy V": engine.config.target_profiles["Heavy V"],
    "C'tan": engine.config.target_profiles["C'tan"],
    "Knight": engine.config.target_profiles["Knight"],
}

# GK detachment → disposition mapping (from expert file)
GK_DETACHMENTS = {
    "WARPBANE TASK FORCE": {"dp": 3, "disp": "Purge the Foe"},
    "BROTHERHOOD STRIKE": {"dp": 2, "disp": "Purge the Foe"},
    "ARGENT ASSAULT": {"dp": 1, "disp": "Purge the Foe"},
    "HALLOWED CONCLAVE": {"dp": 2, "disp": "Take and Hold"},
    "IMMATERIAL INTERDICTION": {"dp": 1, "disp": "Priority Assets"},
    "SANCTIC SPEARHEAD": {"dp": 2, "disp": "Priority Assets"},
    "FIRES OF PURGATION": {"dp": 1, "disp": "Disruption"},
    "BANISHERS": {"dp": 2, "disp": "Disruption"},
    "AUGURIUM TASK FORCE": {"dp": 2, "disp": "Reconnaissance"},
}

# ── 1) Disposition constraints table ──────────────────────────────
print("=" * 120)
print("TABLE 1: FORCE DISPOSITION CONSTRAINTS (11e)")
print("=" * 120)
print(f"{'Disposition':<20s} {'Valid GK Detachments':<55s} {'DP'}")
print("-" * 80)

disp_groups = {}
for det, info in GK_DETACHMENTS.items():
    disp = info["disp"]
    if disp not in disp_groups:
        disp_groups[disp] = []
    disp_groups[disp].append(f"{det} ({info['dp']})")

for disp, dets in disp_groups.items():
    det_str = ", ".join(dets)
    print(f"{disp:<20s} {det_str:<55s}")

print()

# ── 2) Key unit DPP per target ────────────────────────────────────
print("=" * 140)
print("TABLE 2: KEY GK UNITS — RAW DPP PER TARGET (no detachment)")
print("=" * 140)
print(f"{'Unit':<42s} {'Pts':>5s} {'GEQ':>8s} {'MEQ':>8s} {'TEQ':>8s} {'LightV':>8s} {'HeavyV':>8s} {'Ctan':>8s} {'Knight':>8s} {'AC_wt':>8s}")
print("-" * 130)

ac_meta = engine.config._resolve_meta("all-comers")

key_units = [
    "Strike Squad", "Interceptor Squad", "Purifier Squad", "Purgation Squad",
    "Brotherhood Terminator Squad", "Paladin Squad",
    "Nemesis Dreadknight", "Grand Master in Nemesis Dreadknight",
    "Castellan Crowe", "Grand Master Voldus",
]

all_results = []
for unit_name in key_units:
    # Find unit in data
    unit_data = None
    for u in engine.data["units"]:
        if u["name"] == unit_name:
            unit_data = u
            break
    if not unit_data:
        continue

    profile = unit_data.get("profile") or {}
    pricing = unit_data.get("pricing", [])
    resolved = engine.resolve_loadout(unit_name, list(targets.values())[0], pricing)
    if resolved is None:
        continue
    pts, ranged_profiles, melee_profiles, innate_profiles, info = resolved

    row = {"name": unit_name, "pts": pts}
    dpp_vals = {}
    for tname, tp in targets.items():
        dmg = 0
        for wp in ranged_profiles:
            dmg += compute_weapon_dpp(wp, tp, unit_points=1)["total_damage"]
        for wp in melee_profiles:
            dmg += compute_weapon_dpp(wp, tp, unit_points=1)["total_damage"]
        for wp in innate_profiles:
            dmg += compute_weapon_dpp(wp, tp, unit_points=1)["total_damage"]
        dpp = dmg / pts if pts > 0 else 0
        row[tname] = round(dpp, 4)
        dpp_vals[tname] = dpp

    ac_dpp = sum(w * dpp_vals[tn] for tn, tp, w in ac_meta)
    row["AC"] = round(ac_dpp, 4)
    all_results.append(row)

all_results.sort(key=lambda r: r["AC"], reverse=True)

for r in all_results:
    ctan = "C'tan"
    print(f"{r['name']:<42s} {r['pts']:>5d} {r['GEQ']:>8.4f} {r['MEQ']:>8.4f} {r['TEQ']:>8.4f} {r['Light V']:>8.4f} {r['Heavy V']:>8.4f} {r[ctan]:>8.4f} {r['Knight']:>8.4f} {r['AC']:>8.4f}")

print()
print("Assumptions: no cover, no detachment buffs, no stratagems, average dice, melee included")
print()

# ── 3) Detachment modifier impact ─────────────────────────────────
print("=" * 120)
print("TABLE 3: DETACHMENT MODIFIER IMPACT — top units vs MEQ")
print("=" * 120)

# Load detachment modifiers
with open("data/config/grey-knights/detachment_modifiers.json") as f:
    det_data = json.load(f)

det_mods = det_data.get("detachments", {})

# Test on a representative unit: Brotherhood Terminator Squad
test_unit = "Brotherhood Terminator Squad"
unit_data = next((u for u in engine.data["units"] if u["name"] == test_unit), None)
if unit_data:
    profile = unit_data.get("profile") or {}
    pricing = unit_data.get("pricing", [])
    resolved = engine.resolve_loadout(test_unit, targets["MEQ"], pricing)
    if resolved:
        pts, rp, mp, ip, info = resolved

        # Baseline
        base_dmg = 0
        for wp in rp:
            base_dmg += compute_weapon_dpp(wp, targets["MEQ"], unit_points=1)["total_damage"]
        for wp in mp:
            base_dmg += compute_weapon_dpp(wp, targets["MEQ"], unit_points=1)["total_damage"]
        for wp in ip:
            base_dmg += compute_weapon_dpp(wp, targets["MEQ"], unit_points=1)["total_damage"]
        base_dpp = base_dmg / pts if pts > 0 else 0

        print(f"Unit: {test_unit} ({pts}pts) vs MEQ")
        print(f"Baseline DPP: {base_dpp:.4f}")
        print()

        print(f"{'Detachment':<30s} {'Choice':<35s} {'DPP':>8s} {'vs Base':>10s} {'DP':>4s}")
        print("-" * 90)

        for det_name, det_info in det_mods.items():
            dp_cost = det_info.get("dp_cost", "?")
            choices = det_info.get("choices", [])
            for choice in choices:
                choice_name = choice.get("name", "?")
                affects = choice.get("affects", "?")

                # Create modifier from choice
                mod = WeaponModifier()
                if choice.get("reroll_hits"):
                    mod.reroll_hits = choice["reroll_hits"]
                if choice.get("sustained_hits"):
                    mod.sustained_hits = choice["sustained_hits"]
                if choice.get("lethal_hits"):
                    mod.lethal_hits = choice["lethal_hits"]
                if choice.get("extra_ap"):
                    mod.extra_ap = choice["extra_ap"]
                if choice.get("hit_modifier"):
                    mod.hit_modifier = choice["hit_modifier"]
                if choice.get("wound_modifier"):
                    mod.wound_modifier = choice["wound_modifier"]

                # Compute with modifier
                mod_dmg = 0
                for wp in rp:
                    mod_dmg += compute_weapon_dpp(wp, targets["MEQ"], unit_points=1, modifier=mod)["total_damage"]
                for wp in mp:
                    mod_dmg += compute_weapon_dpp(wp, targets["MEQ"], unit_points=1, modifier=mod)["total_damage"]
                for wp in ip:
                    mod_dmg += compute_weapon_dpp(wp, targets["MEQ"], unit_points=1, modifier=mod)["total_damage"]
                mod_dpp = mod_dmg / pts if pts > 0 else 0

                gain = ((mod_dpp - base_dpp) / base_dpp * 100) if base_dpp > 0 else 0
                gain_str = f"+{gain:.1f}%" if gain > 0 else f"{gain:.1f}%"

                print(f"{det_name:<30s} {choice_name:<35s} {mod_dpp:>8.4f} {gain_str:>10s} {str(dp_cost):>4s}")

print()

# ── 4) Purge the Foe comparison ───────────────────────────────────
print("=" * 120)
print("TABLE 4: PURGE THE FOE — Warpbane vs Brotherhood vs Argent Assault")
print("=" * 120)

# This would need manual analysis based on the modifier data
# For now, print the available choices per detachment
for det_name in ["WARPBANE TASK FORCE", "BROTHERHOOD STRIKE", "ARGENT ASSAULT"]:
    det_info = det_mods.get(det_name, {})
    dp = det_info.get("dp_cost", "?")
    choices = det_info.get("choices", [])
    print(f"\n{det_name} ({dp}DP):")
    for i, c in enumerate(choices):
        print(f"  [{i}] {c.get('name', '?')} — affects: {c.get('affects', '?')}")
        if c.get("reroll_hits"):
            print(f"      reroll_hits: {c['reroll_hits']}")
        if c.get("sustained_hits"):
            print(f"      sustained_hits: {c['sustained_hits']}")
        if c.get("lethal_hits"):
            print(f"      lethal_hits: {c['lethal_hits']}")
        if c.get("extra_ap"):
            print(f"      extra_ap: {c['extra_ap']}")
        if c.get("hit_modifier"):
            print(f"      hit_modifier: {c['hit_modifier']}")

print()
print("Analysis complete. Use this data to write findings/grey-knights/mission-analysis.md")
