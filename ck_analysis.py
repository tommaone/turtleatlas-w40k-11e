"""
CK helicopter analysis — extract DPP per target profile for all units.
No commentary, no bias. Just the data.
"""
from engine.ranking import RankingEngine
from engine.dpp import compute_weapon_dpp, WeaponProfile, WeaponModifier, TargetProfile, HitMode
import json, sys

engine = RankingEngine("chaos-knights")

targets = {
    "GEQ": engine.config.target_profiles["GEQ"],
    "MEQ": engine.config.target_profiles["MEQ"],
    "TEQ": engine.config.target_profiles["TEQ"],
    "Light V": engine.config.target_profiles["Light V"],
    "Heavy V": engine.config.target_profiles["Heavy V"],
    "C'tan": engine.config.target_profiles["C'tan"],
    "Knight": engine.config.target_profiles["Knight"],
}

# ── 1) Per-target raw DPP for each unit ──────────────────────────────
print("=" * 140)
print("TABLE 1: RAW DPP PER TARGET PROFILE — all CK units (no mission weighting)")
print("=" * 140)
print(f"{'Unit':<42s} {'Pts':>5s} {'GEQ':>8s} {'MEQ':>8s} {'TEQ':>8s} {'LightV':>8s} {'HeavyV':>8s} {'Ctan':>8s} {'Knight':>8s} {'AC_wt':>8s} {'Comp_wt':>8s}")
print("-" * 175)

# all-comers and competitive weights
ac_meta = engine.config._resolve_meta("all-comers")
comp_meta = engine.config._resolve_meta("competitive")
# (name, tp, weight) for each

all_results = []
for unit in engine.data["units"]:
    name = unit["name"]
    if name not in engine.config.known_units:
        continue
    profile = unit.get("profile") or {}
    kws = [k.upper() for k in profile.get("keywords", [])]
    if profile and not any(fk in kws for fk in engine.config.faction_keywords):
        continue
    pricing = unit.get("pricing", [])
    resolved = engine.resolve_loadout(name, list(targets.values())[0], pricing)
    if resolved is None:
        continue
    pts, ranged_profiles, melee_profiles, innate_profiles, info = resolved

    # Compute DPP for each target profile
    row = {"name": name, "pts": pts}
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

    # All-comers weighted DPP
    ac_dpp = sum(w * dpp_vals[tn] for tn, tp, w in ac_meta)
    comp_dpp = sum(w * dpp_vals[tn] for tn, tp, w in comp_meta)
    row["AC"] = round(ac_dpp, 4)
    row["Comp"] = round(comp_dpp, 4)

    all_results.append(row)

# Sort by all-comers weighted DPP descending
all_results.sort(key=lambda r: r["AC"], reverse=True)

for r in all_results:
    ctan_key = "C'tan"
    print(f"{r['name']:<42s} {r['pts']:>5d} {r['GEQ']:>8.4f} {r['MEQ']:>8.4f} {r['TEQ']:>8.4f} {r['Light V']:>8.4f} {r['Heavy V']:>8.4f} {r[ctan_key]:>8.4f} {r['Knight']:>8.4f} {r['AC']:>8.4f} {r['Comp']:>8.4f}")

print()
print("Assumptions: no cover, no detachment buffs, no stratagems, average dice, melee included")
print("All-comers weights: GEQ×15%, MEQ×25%, TEQ×15%, Light V×20%, Heavy V×15%, C'tan×5%, Knight×5%")
print("Competitive weights: MEQ×35%, TEQ×15%, Light V×25%, Heavy V×15%, Knight×10%")
print()

# ── 2) Non-DPP value table ─────────────────────────────────────────
print("=" * 140)
print("TABLE 2: NON-DPP VALUE — OC, durability, mobility per unit")
print("=" * 140)
print(f"{'Unit':<42s} {'Pts':>5s} {'OC':>3s} {'T':>3s} {'SV':>3s} {'W':>3s} {'INV':>4s} {'EffW@AP0':>9s} {'EffW@AP2':>9s} {'EffW@AP4':>9s} {'M':>4s} {'Fly':>4s} {'DS':>4s} {'Tier':<13s}")
print("-" * 140)

for r in all_results:
    name = r["name"]
    # Re-resolve to get info
    profile = next((u for u in engine.data["units"] if u["name"] == name), None)
    pdata = (profile or {}).get("profile") or {}
    pricing = (profile or {}).get("pricing", [])
    resolved = engine.resolve_loadout(name, list(targets.values())[0], pricing)
    if resolved is None:
        continue
    pts, rp, mp, ip, info = resolved
    kw_list, t_val, sv_val, w_val, oc_val, inv_val = engine.get_unit_info(name, pdata)

    # SURV
    from engine.dpp import UnitDefense, compute_surv
    is_infantry = "INFANTRY" in kw_list
    fnp_val = 6 if is_infantry else None
    n_models = 1
    if name in engine.config.squads:
        n_models = engine.config.squads[name]["n"]
    defense = UnitDefense(toughness=t_val, wounds_per_model=w_val, save=sv_val,
                          invuln=inv_val, fnp=fnp_val, models=n_models)
    surv = compute_surv(defense, pts)

    # MOB
    m_val = 6
    if info:
        import re
        m_m = re.search(r'(\d+)', str(info.get("M", '6"')))
        if m_m:
            m_val = int(m_m.group(1))
        if info.get("FLY"):
            kw_list.append("FLY")
    else:
        m_str = pdata.get("stats", {}).get("M", '6"')
        m_m = re.search(r'(\d+)', str(m_str))
        if m_m:
            m_val = int(m_m.group(1))

    has_fly = "FLY" in kw_list
    has_ds = "DEEP STRIKE" in kw_list

    mob_tier = "skyborne" if m_val >= 20 else ("very_fast" if m_val >= 14 else ("fast" if m_val >= 10 else ("cavalry" if m_val >= 8 else ("standard" if m_val >= 6 else "slow"))))

    inv_str = f"{inv_val}+" if inv_val else "none"
    fly_str = "Y" if has_fly else "N"
    ds_str = "Y" if has_ds else "N"
    print(f"{name:<42s} {pts:>5d} {oc_val:>3d} {t_val:>3d} {sv_val}+{'>2s' if False else '':>2s} {w_val*n_models:>3d} {inv_str:>4s} {surv['effective_wounds']['ap0']:>9.1f} {surv['effective_wounds']['ap2']:>9.1f} {surv['effective_wounds']['ap4']:>9.1f} {m_val:>3d}\" {fly_str:>4s} {ds_str:>4s} {mob_tier:<13s}")

print()

# ── 3) Detachment table ──────────────────────────────────────────────
print("=" * 120)
print("TABLE 3: DETACHMENT ANALYSIS — all 8 CK detachments")
print("=" * 120)

disp_names = {
    "PURGE THE FOE": "Kill-focused (DPS 70%, SURV 20%, MOB 10%)",
    "TAKE AND HOLD": "Objective-focused (DPS 20%, SURV 50%, MOB 30%)",
    "PRIORITY ASSETS": "Balanced/assassination (DPS 50%, SURV 30%, MOB 20%)",
    "RECONNAISSANCE": "Mobility-focused (DPS 15%, SURV 25%, MOB 60%)",
    "DISRUPTION": "Deny/control (DPS 35%, SURV 35%, MOB 30%)",
}

# Load modifier data from config (machine-readable, no GW IP)
mod_config_path = engine.merged_path.replace("merged/chaos-knights.json", "../config/chaos-knights/detachment_modifiers.json")
import os
mod_config_path = os.path.normpath(mod_config_path)
mod_data = {}
if os.path.exists(mod_config_path):
    with open(mod_config_path) as f:
        mod_data = json.load(f).get("detachments", {})

for det in engine.data["detachments"]:
    name = det["name"]
    dp = det.get("dp", "?")
    objective = det.get("objective", "NONE")
    disp_desc = disp_names.get(objective, objective)

    print(f"\n### {name}  (DP={dp}, Disposition: {disp_desc})")

    # Modifiers from config
    det_mods = mod_data.get(name.upper(), {})
    choices = det_mods.get("choices", [])
    if choices:
        for c in choices:
            filter_str = f" (filter: {', '.join(c.get('unit_filter', ['all']))})" if c.get('unit_filter') else " (all units)"
            cond = f" [{c.get('condition', 'always-on')}]" if c.get('condition') else ""

            buff_parts = []
            if c.get('hit_modifier'): buff_parts.append("hit_mod")
            if c.get('sustained_hits_extra'): buff_parts.append(f"Sustained Hits +{c['sustained_hits_extra']}")
            if c.get('lethal_hits'): buff_parts.append("Lethal Hits")
            if c.get('plus1_to_wound'): buff_parts.append("+1 to wound")
            if c.get('extra_ap'): buff_parts.append(f"AP{c['extra_ap']}")
            if c.get('ignore_cover'): buff_parts.append("Ignores Cover")
            if c.get('reroll_hits'): buff_parts.append(f"Reroll hits ({c['reroll_hits']})")
            if c.get('movement_bonus'): buff_parts.append(f"+{c['movement_bonus']}\" M")
            if c.get('invulnerable_save'): buff_parts.append(f"INV {c['invulnerable_save']}+")
            if c.get('feel_no_pain'): buff_parts.append(f"FNP {c['feel_no_pain']}+")

            buff_str = ", ".join(buff_parts) if buff_parts else c.get('description', 'see above')
            print(f"    {c['name']}: {c.get('description', '')}{filter_str}{cond}")
            if buff_parts:
                print(f"      → {buff_str}")
    else:
        print(f"  No DPP modifiers defined (detachment's effects are stratagem/enhancement-based)")

    # Enhancements from merged data
    enhs = det.get("enhancements", [])
    if enhs:
        print(f"  Enhancements ({len(enhs)}):")
        for e in enhs:
            print(f"    • {e['name']} ({e.get('points', '?')}pts)")
    else:
        print(f"  Enhancements: none listed")

print()
print("=" * 140)
print("TABLE 4: NON-DPP VALUE NOTES — OC, screening, action efficiency")
print("=" * 140)
print()
print("OC per point (higher = better action monkey / objective holder):")
print(f"{'Unit':<42s} {'Pts':>5s} {'OC':>3s} {'OC/pts':>8s} {'Screening':<30s} {'Role notes'}")
print("-" * 140)

# All units — OC/pts, screening potential, role notes
screening_notes = {
    "War Dog Brigand": "Large base, can block lanes",
    "War Dog Executioner": "Large base, cheap War Dog",
    "War Dog Huntsman": "Large base",
    "War Dog Karnivore": "Large base, fast — can screen forward",
    "War Dog Moirax": "Large base",
    "War Dog Stalker": "Large base, scout move",
    "Knight Abominant": "Massive base, can block half a board",
    "Knight Desecrator": "Massive base",
    "Knight Despoiler": "Massive base",
    "Knight Rampager": "Massive base, 12\" M",
    "Knight Ruinator": "Massive base",
    "Knight Tyrant": "Massive base, 8\" M — castle piece",
    "Chaos Acastus Knight Asterius": "Titanic base",
    "Chaos Acastus Knight Porphyrion": "Titanic base",
    "Chaos Cerastus Knight Acheron": "Cerastus base",
    "Chaos Cerastus Knight Atrapos": "Cerastus base",
    "Chaos Cerastus Knight Castigator": "Cerastus base",
    "Chaos Cerastus Knight Lancer": "Cerastus base, fastest",
    "Chaos Questoris Knight Styrix": "Massive base",
}

role_notes = {
    "War Dog Brigand": "Ranged support, anti-horde/MEQ",
    "War Dog Executioner": "Cheapest War Dog, light vehicle hunter",
    "War Dog Huntsman": "Anti-tank spear + melee",
    "War Dog Karnivore": "Pure melee beatstick",
    "War Dog Moirax": "Flexible loadout",
    "War Dog Stalker": "Flexible, scout option",
    "Knight Abominant": "Elite infantry hunter, psychic",
    "Knight Desecrator": "Anti-tank laser + melee",
    "Knight Despoiler": "Flexible arms, MEQ spam build",
    "Knight Rampager": "Pure melee, 12\" M",
    "Knight Ruinator": "Ranged focus, torrent",
    "Knight Tyrant": "Castle gun platform",
    "Chaos Acastus Knight Asterius": "Titanic ranged platform",
    "Chaos Acastus Knight Porphyrion": "Titanic ranged platform",
    "Chaos Cerastus Knight Acheron": "Flame cannon, anti-horde",
    "Chaos Cerastus Knight Atrapos": "Anti-vehicle specialist",
    "Chaos Cerastus Knight Castigator": "TEQ hunter, bolt cannon",
    "Chaos Cerastus Knight Lancer": "Fastest knight, shock lance",
    "Chaos Questoris Knight Styrix": "Mixed ranged + melee",
}

for r in all_results:
    name = r["name"]
    pts = r["pts"]
    profile = next((u for u in engine.data["units"] if u["name"] == name), None)
    pdata = (profile or {}).get("profile") or {}
    
    # Get OC
    config_name = name
    oc_val = 0
    if config_name in engine.config.vehicles:
        oc_val = engine.config.vehicles[config_name]["info"].get("OC", 0)
    elif config_name in engine.config.weapon_options:
        oc_val = engine.config.weapon_options[config_name].get("info", {}).get("OC", 0)
    else:
        # fallback
        _, _, _, _, oc_v, _ = engine.get_unit_info(name, pdata)
        oc_val = oc_v
    
    oc_pts = oc_val / pts if pts > 0 else 0
    screen = screening_notes.get(name, "N/A")
    role = role_notes.get(name, "")
    print(f"{name:<42s} {pts:>5d} {oc_val:>3d} {oc_pts:>8.4f} {screen:<30s} {role}")

print()
print("=" * 140)
print("NOTES ON WHAT THIS DATA DOES AND DOES NOT CAPTURE")
print("=" * 140)
print()
print("DPP captures: expected damage per point spent, averaged over hit/wound/save/damage rolls.")
print("DPP does NOT capture:")
print("  - Detachment buffs (see Table 3 for what exists)")
print("  - Stratagem support (CP cost + 1/game or per phase)")
print("  - Command rerolls")
print("  - Melta half-range bonus")
print("  - Blast minimum attacks")
print("  - Heavy movement penalty")
print("  - Feel No Pain on the target")
print("  - Cover modifiers")
print("  - Target keywords (Anti-Keyword match is heuristic)")
print("  - Knight Despoiler: config includes all possible arm+carapace weapons simultaneously")
print("    (2x gatling + hellstorm + missile pod + stubber), overcounting DPP vs a real loadout")
print()
print("Non-DPP value (Table 2+4) captures: OC, durability, mobility, screening potential.")
print("Non-DPP does NOT capture: action monkey efficiency (qualitative only), CP generation,")
print("  psychic shenanigans, aura effects, battleshock synergy, ally interactions.")
print()
print("Army rules also NOT modelled:")
print("  - Harbingers of Dread (Darkness: Stealth) — -1 to hit the unit")
print("  - Super-heavy Walker — ignore terrain for movement, stomp attacks")
print("  - Daemonic Pact allies (up to 500pt Daemons)")
print("  - Iconoclast Fiefdom DAMNED allies (up to 500pt CSM cultists)")
print()
print("INVULNERABLE SAVE DATA GAP: Zero out of 19 CK units have INV in the config data.")
print("  notes.json confirms Desecrator, Rampager, and Lancer should have 4++ invuln.")
print("  This means SURV effective wounds are OVERSTATED for all units vs their true values.")
print("  The config needs INV fields added — until then, treat SURV as best-case (no invuln).")
print()
print("All numbers rounded to 4 decimal places. All-comers meta: GEQ×15%, MEQ×25%, TEQ×15%,")
print("  Light V×20%, Heavy V×15%, C'tan×5%, Knight×5%.")
print("Competitive meta: MEQ×35%, TEQ×15%, Light V×25%, Heavy V×15%, Knight×10%.")
