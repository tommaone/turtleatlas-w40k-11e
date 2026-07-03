"""
GK Unit Ranking — DPS + SURV + MOB three-vector system.
Loads merged GK data, computes per-unit DPP vs MEQ, survivability, and mobility.
Weapon profiles loaded from BSData merged JSON via weapon_loader.py.
"""

import json
import re
import sys
from pathlib import Path
import itertools

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.dpp import (
    WeaponProfile, TargetProfile,
    compute_weapon_dpp, HitMode,
    UnitDefense, compute_surv, compute_mob,
)
from engine.weapon_loader import WeaponCatalog

# ── Catalog ─────────────────────────────────────────────────────────
_CATALOG = WeaponCatalog(
    str(Path(__file__).resolve().parent.parent / "data" / "merged" / "grey-knights.json")
)

# ── Target profiles ──────────────────────────────────────────────
# Keys: (toughness, save, invuln, wounds_per_model, description)
TARGET_PROFILES = {
    "GEQ":     TargetProfile(toughness=3, save=5,  invuln=None),
    "MEQ":     TargetProfile(toughness=4, save=3,  invuln=None),
    "TEQ":     TargetProfile(toughness=5, save=2,  invuln=4),
    "Light V": TargetProfile(toughness=7, save=3,  invuln=None),
    "Heavy V": TargetProfile(toughness=10, save=2, invuln=4),
    "C'tan":   TargetProfile(toughness=11, save=4, invuln=4),
    "Knight":  TargetProfile(toughness=13, save=2, invuln=5),
}
MEQ = TARGET_PROFILES["MEQ"]  # backward compat

# ── Mission profiles ─────────────────────────────────────────────
# Weights for (DPS, SURV, MOB) — sum to 1.0
MISSION_PROFILES = {
    "Purge the Foe":    {"dps": 0.70, "surv": 0.20, "mob": 0.10},
    "Take and Hold":    {"dps": 0.20, "surv": 0.50, "mob": 0.30},
    "Reconnaissance":   {"dps": 0.15, "surv": 0.25, "mob": 0.60},
    "Priority Assets":  {"dps": 0.50, "surv": 0.30, "mob": 0.20},
    "Disruption":       {"dps": 0.35, "surv": 0.35, "mob": 0.30},
    "Purge (general)": {"dps": 0.60, "surv": 0.25, "mob": 0.15},
}

# Shorthand: load a weapon from the catalog
def W(name, **kw):
    return _CATALOG.load(name, **kw)


# ---------------------------------------------------------------------------
# DPP helpers (target-aware)
# ---------------------------------------------------------------------------

def _wp_dmg(wp, target=MEQ):
    return compute_weapon_dpp(wp, target, hit_mode=HitMode.NORMAL)["total_damage"]

def _ld_dmg(ranged, melee, innate, target=MEQ):
    d = 0
    for wp in ranged: d += _wp_dmg(wp, target)
    for wp in melee: d += _wp_dmg(wp, target)
    for wp in innate: d += _wp_dmg(wp, target)
    return d


# ---------------------------------------------------------------------------
# Squad wargear configs — weapon names loaded from BSData catalog
# ---------------------------------------------------------------------------

SQUAD_CONFIG = {
    "Strike Squad": {
        "unit": "Strike Squad",
        "n": 5,
        "ranged": "Storm bolter",
        "ranged_a": 4.0,             # ≤12" RF2 doubles A=2→4
        "melee": "Nemesis force weapon",
        "special_max": 1,
        "specials": ["Incinerator", "Psilencer", "Psycannon"],
        "sp_loses_r": True,
        "sp_loses_m": True,            # PA: special model swaps NFW→CCW
        "apoth_loses_r": False,
        "innate": [],
    },
    "Interceptor Squad": {
        "unit": "Interceptor Squad",
        "n": 5,
        "ranged": "Storm bolter",
        "ranged_a": 4.0,
        "melee": "Nemesis force weapon",
        "special_max": 1,
        "specials": ["Incinerator", "Psilencer", "Psycannon"],
        "sp_loses_r": True,
        "sp_loses_m": True,
        "apoth_loses_r": False,
        "innate": [],
    },
    "Purifier Squad": {
        "unit": "Purifier Squad",
        "n": 5,
        "ranged": "Storm bolter",
        "ranged_a": 4.0,
        "melee": "Nemesis force weapon",
        "special_max": 2,
        "specials": ["Incinerator", "Psilencer", "Psycannon"],
        "sp_loses_r": True,
        "sp_loses_m": True,
        "apoth_loses_r": False,
        "innate": ["Purifying Flame"],
    },
    "Purgation Squad": {
        "unit": "Purgation Squad",
        "n": 4,
        "ranged": "Storm bolter",
        "ranged_a": 4.0,
        "melee": "Nemesis force weapon",
        "special_max": 3,
        "specials": ["Incinerator", "Psilencer", "Psycannon"],
        "sp_loses_r": True,
        "sp_loses_m": True,
        "apoth_loses_r": False,
        "innate": [],
    },
    "Brotherhood Terminator Squad": {
        "unit": "Brotherhood Terminator Squad",
        "n": 5,
        "ranged": "Storm bolter",
        "ranged_a": 4.0,
        "melee": "Nemesis force weapon",
        "special_max": 2,
        "specials": ["Incinerator", "Psilencer", "Psycannon"],
        "sp_loses_r": True,
        "sp_loses_m": False,           # Terminators keep NFW
        "apoth_loses_r": True,
        "innate": [],
    },
    "Paladin Squad": {
        "unit": "Paladin Squad",
        "n": 5,
        "ranged": "Storm bolter",
        "ranged_a": 4.0,
        "melee": "Nemesis force weapon",
        "special_max": 2,
        "specials": ["Incinerator", "Psilencer", "Psycannon"],
        "sp_loses_r": True,
        "sp_loses_m": False,
        "apoth_loses_r": False,
        "innate": [],
    },
}


def _eval_variant(cfg, spec_indices):
    """Evaluate one loadout variant given which specials (by index) are taken."""
    n = cfg["n"]
    n_sp = len(spec_indices)
    if n_sp > cfg["special_max"]:
        return None
    unit_name = cfg["unit"]
    opts = cfg["specials"]
    sp_loses_r = cfg.get("sp_loses_r", True)
    sp_loses_m = cfg.get("sp_loses_m", False)
    apoth = cfg.get("apoth_loses_r", False)
    ranged_a_override = cfg.get("ranged_a")

    ranged, melee, innate = [], [], []
    si = 0
    for i in range(n):
        # Innate weapons (e.g. Purifying Flame on every Purifier)
        for iname in cfg.get("innate", []):
            innate.append(W(iname, unit_name=unit_name))

        if si < n_sp:  # special weapon model
            sname = opts[spec_indices[si]]
            si += 1
            ranged.append(W(sname, unit_name=unit_name))
            if sp_loses_m:
                melee.append(W("Close combat weapon", unit_name=unit_name))
            else:
                melee.append(W(cfg["melee"], unit_name=unit_name))
        else:  # regular model
            is_apoth = apoth and i == n - 1
            if not is_apoth:
                kw = {}
                if ranged_a_override is not None:
                    kw["a"] = ranged_a_override
                ranged.append(W(cfg["ranged"], unit_name=unit_name, **kw))
            melee.append(W(cfg["melee"], unit_name=unit_name))

    return {"ranged": ranged, "melee": melee, "innate": innate}


def best_squad_variant(name, target=MEQ):
    cfg = SQUAD_CONFIG.get(name)
    if not cfg:
        return None
    opts = cfg["specials"]
    best, best_d = None, -1
    for n_sp in range(0, cfg["special_max"] + 1):
        for indices in itertools.product(range(len(opts)), repeat=n_sp):
            ld = _eval_variant(cfg, list(indices))
            if ld is None:
                continue
            d = _ld_dmg(ld["ranged"], ld["melee"], ld["innate"], target)
            if d > best_d:
                best_d = d
                best = ld

    if best:
        r_counts = {}
        for wp in best["ranged"]:
            r_counts[wp.name] = r_counts.get(wp.name, 0) + 1
        m_counts = {}
        for wp in best["melee"]:
            m_counts[wp.name] = m_counts.get(wp.name, 0) + 1
        i_counts = {}
        for wp in best["innate"]:
            i_counts[wp.name] = i_counts.get(wp.name, 0) + 1
        target_tag = None
        for tname, tp in TARGET_PROFILES.items():
            if target == tp:
                target_tag = tname
                break
        tag = target_tag or "custom"
        parts = []
        if r_counts:
            parts.append("Ranged: " + ", ".join(f"{c}×{n}" for n, c in sorted(r_counts.items())))
        if m_counts:
            parts.append("Melee: " + ", ".join(f"{c}×{n}" for n, c in sorted(m_counts.items())))
        if i_counts:
            parts.append("Innate: " + ", ".join(f"{c}×{n}" for n, c in sorted(i_counts.items())))
        parts.append(f"[optimised for {tag}]")
        best["_desc"] = "; ".join(parts)
    return best


# ---------------------------------------------------------------------------
# Vehicle weapon configs
# ---------------------------------------------------------------------------

NDK_RANGED = ["Gatling psilencer", "Heavy psycannon", "Heavy incinerator"]
NDK_MELEE = ["Nemesis greatsword - strike", "Nemesis daemon greathammer", "Dreadfists"]

GMNDK_RANGED = ["Sublimator", "Gatling psilencer", "Heavy psycannon", "Heavy incinerator"]
GMNDK_MELEE = [
    "Nemesis greatsword - strike", "Nemesis mace", "Nemesis flail",
    "Nemesis daemon greathammer", "Dreadfists",
]


def best_vehicle_variant(ranged_names, melee_names, unit_name, target=MEQ):
    """Try all ranged+melee combos, return highest-DPP loadout."""
    best, best_d = None, -1
    for (rf1_name,), (rf2_name,) in itertools.combinations_with_replacement(
        [(n,) for n in ranged_names], 2
    ):
        for mm_name in melee_names:
            ranged = [W(rf1_name, unit_name=unit_name), W(rf2_name, unit_name=unit_name)]
            melee = [W(mm_name, unit_name=unit_name)]
            d = _ld_dmg(ranged, melee, [], target)
            if d > best_d:
                best_d = d
                best = {
                    "ranged": ranged,
                    "melee": melee,
                    "innate": [],
                    "_desc": f"Ranged: {rf1_name}+{rf2_name}; Melee: {mm_name} [optimised]",
                }
    return best


# ── Unit info (stats, not loadouts) ──────────────────────────────

SQUAD_INFO = {
    "Strike Squad": {"pts": 120, "n": 5, "info": {"M": "6\"", "T": 4, "SV": 3, "W": 2, "OC": 2, "INV": 4}},
    "Interceptor Squad": {"pts": 125, "n": 5, "info": {"M": "6\"", "T": 4, "SV": 3, "W": 2, "OC": 2, "INV": 4, "FLY": True}},
    "Purifier Squad": {"pts": 130, "n": 5, "info": {"M": "6\"", "T": 4, "SV": 3, "W": 2, "OC": 1, "INV": 4}},
    "Purgation Squad": {"pts": 110, "n": 4, "info": {"M": "6\"", "T": 4, "SV": 3, "W": 2, "OC": 1, "INV": 4}},
    "Brotherhood Terminator Squad": {"pts": 140, "n": 5, "info": {"M": "5\"", "T": 5, "SV": 2, "W": 3, "OC": 2, "INV": 4}},
    "Paladin Squad": {"pts": 170, "n": 5, "info": {"M": "5\"", "T": 5, "SV": 2, "W": 3, "OC": 1, "INV": 4}},
}

# Fixed loadout units (vehicles, characters — their loadout doesn't depend on target)
STATIC_LOADOUTS = {
    "Venerable Dreadnought": (
        130,
        [W("Storm bolter", unit_name="Grey Knights Dreadnought")],
        [W("Dreadnought combat weapon", unit_name="Grey Knights Dreadnought")],
        [],
        {"M": "8\"", "T": 9, "SV": 2, "W": 8, "OC": 3, "INV": 4},
    ),
    "Grey Knights Thunderhawk Gunship": (
        805, [W("Storm bolter")], [], [],
        {"M": "20+\"", "T": 12, "SV": 2, "W": 30, "OC": 0},
    ),
    "Dreadknight Champion [Crucible]": (
        210, [], [W("Dreadfists", unit_name="Nemesis Dreadknight")], [],
        {"M": "8\"", "T": 8, "SV": 2, "W": 13, "OC": 4, "INV": 4},
    ),
    "Venerable Daemon Slayer [Crucible]": (
        175, [],
        [W("Dreadnought combat weapon", unit_name="Grey Knights Dreadnought")],
        [],
        {"M": "8\"", "T": 9, "SV": 2, "W": 8, "OC": 3, "INV": 4},
    ),
    "Land Raider": (220, [W("Storm bolter")], [], [], {"M": "10\"", "T": 12, "SV": 2, "W": 16, "OC": 5}),
    "Land Raider Crusader": (220, [W("Storm bolter")], [], [], {"M": "12\"", "T": 12, "SV": 2, "W": 16, "OC": 5}),
    "Land Raider Redeemer": (250, [W("Storm bolter")], [], [], {"M": "12\"", "T": 12, "SV": 2, "W": 16, "OC": 5}),
    "Razorback": (85, [W("Storm bolter")], [], [], {"M": "12\"", "T": 9, "SV": 3, "W": 10, "OC": 2}),
    "Rhino": (80, [W("Storm bolter")], [], [], {"M": "12\"", "T": 9, "SV": 3, "W": 10, "OC": 2}),
    "Stormraven Gunship": (280, [W("Storm bolter")], [], [], {"M": "20+\"", "T": 10, "SV": 3, "W": 14, "OC": 0}),
    "Stormhawk Interceptor": (160, [W("Storm bolter")], [], [], {"M": "20+\"", "T": 9, "SV": 3, "W": 10, "OC": 0}),
    "Stormtalon Gunship": (170, [W("Storm bolter")], [], [], {"M": "20+\"", "T": 9, "SV": 3, "W": 10, "OC": 0}),
}

STATIC_LOADOUTS["Champion of Titan [Crucible]"] = (
    90, [], [W("Nemesis force weapon", unit_name="Strike Squad")], [],
    {"M": "6\"", "T": 4, "SV": 3, "W": 2, "OC": 1, "INV": 4},
)

# Characters — fixed loadout, not target-optimised
CHARACTER_LOADOUTS = {
    "Brother-Captain": (95, [W("Storm bolter", unit_name="Brother-Captain")],
                        [W("Nemesis force weapon", unit_name="Brother-Captain")], []),
    "Brotherhood Champion": (70, [W("Storm bolter", unit_name="Brotherhood Champion")],
                             [W("Nemesis force weapon", unit_name="Brotherhood Champion",
                                 abilities=["Precision", "Psychic"])], []),
    "Brotherhood Chaplain": (65, [W("Storm bolter", unit_name="Brotherhood Chaplain")],
                             [W("Crozius arcanum", unit_name="Brotherhood Chaplain")], []),
    "Brotherhood Librarian": (90, [W("Storm bolter", unit_name="Brotherhood Librarian")],
                              [W("Nemesis force weapon", unit_name="Brotherhood Librarian")], []),
    "Brotherhood Techmarine": (70, [W("Storm bolter", unit_name="Brotherhood Techmarine")],
                               [W("Omnissian power axe", unit_name="Brotherhood Techmarine")], []),
    "Castellan Crowe": (100, [W("Storm bolter", unit_name="Castellan Crowe")],
                        [W("Black Blade of Antwyr", unit_name="Castellan Crowe")],
                        [W("Purifying Flame", unit_name="Castellan Crowe")]),
    "Grand Master": (95, [W("Storm bolter", unit_name="Grand Master")],
                     [W("Nemesis force weapon", unit_name="Grand Master")], []),
    "Grand Master Voldus": (140, [W("Storm bolter", unit_name="Grand Master Voldus")],
                            [W("Malleus Argyrum", unit_name="Grand Master Voldus")], []),
}


def resolve_loadout(name, target=MEQ, pricing=None):
    """Resolve a unit's loadout for a given target.

    Returns (points, ranged_profiles, melee_profiles, innate_profiles, info_dict)
    or None if the unit isn't supported.
    """
    # Squad: optimised per target
    if name in SQUAD_CONFIG:
        sdetail = SQUAD_INFO[name]
        pts = sdetail["pts"]
        if pricing:
            for pr in pricing:
                for cost in pr.get("costs", []):
                    if cost.get("models") == sdetail["n"]:
                        pts = cost["points"]
                        break
                if pts:
                    break
        ld = best_squad_variant(name, target)
        return (pts, ld["ranged"], ld["melee"], ld["innate"], sdetail["info"])

    # Vehicle with weapon options: NDK / GMNDK
    if name == "Nemesis Dreadknight":
        pts = 195
        if pricing:
            for pr in pricing:
                for cost in pr.get("costs", []):
                    if cost.get("models") == 1:
                        pts = cost["points"]
        bv = best_vehicle_variant(NDK_RANGED, NDK_MELEE, name, target)
        info = {"M": "8\"", "T": 8, "SV": 2, "W": 13, "OC": 4, "INV": 4}
        return (pts, bv["ranged"], bv["melee"], bv["innate"], info)

    if name == "Grand Master In Nemesis Dreadknight":
        pts = 200
        if pricing:
            for pr in pricing:
                for cost in pr.get("costs", []):
                    if cost.get("models") == 1:
                        pts = cost["points"]
        bv = best_vehicle_variant(GMNDK_RANGED, GMNDK_MELEE, name, target)
        info = {"M": "8\"", "T": 8, "SV": 2, "W": 13, "OC": 4, "INV": 4}
        return (pts, bv["ranged"], bv["melee"], bv["innate"], info)

    # Character: fixed loadout
    if name in CHARACTER_LOADOUTS:
        pts, ranged, melee, innate = CHARACTER_LOADOUTS[name]
        return (pts, ranged, melee, innate, None)

    # Static: fixed loadout
    if name in STATIC_LOADOUTS:
        pts, ranged, melee, innate, info = STATIC_LOADOUTS[name]
        if pricing:
            for pr in pricing:
                for cost in pr.get("costs", []):
                    if cost.get("models") == 1:
                        pts = cost["points"]
        return (pts, ranged, melee, innate, info)

    return None


# ---------------------------------------------------------------------------
# Ranking computation
# ---------------------------------------------------------------------------

def compute_weapons_dpp(profiles, unit_points, target=MEQ):
    total_damage = 0.0
    for wp in profiles:
        r = compute_weapon_dpp(wp, target, unit_points=unit_points, hit_mode=HitMode.NORMAL)
        total_damage += r["total_damage"]
    return total_damage


def format_surv(defense_dict):
    ew = defense_dict["effective_wounds"]
    ppe = defense_dict["pts_per_eff_w_ap0"]
    return f'effW@AP0={ew["ap0"]} AP2={ew["ap2"]} AP4={ew["ap4"]}, pts/effW={ppe}'


def format_mob(mob_dict):
    m = mob_dict["movement"]
    fly = " Fly" if mob_dict["fly"] else ""
    ds = " DS" if mob_dict["deep_strike"] else ""
    oc = mob_dict["objective_control"]
    tier = mob_dict["mobility_tier"]
    return f'M={m}{fly}{ds} OC={oc} [{tier}]'


def get_unit_info(name, profile_data):
    """Return (keywords, toughness, save, wounds, oc, invuln) for a unit."""
    if name in SQUAD_INFO:
        info = SQUAD_INFO[name]["info"]
        kw = ["INFANTRY", "DEEP STRIKE", "FACTION: GREY KNIGHTS"]
        if info.get("FLY"):
            kw.append("FLY")
        if name == "Paladin Squad":
            kw.append("TERMINATOR")
        if "Terminator" in name:
            kw.append("TERMINATOR")
        return kw, info["T"], info["SV"], info["W"], info["OC"], info.get("INV")

    if name in STATIC_LOADOUTS:
        _, _, _, _, info = STATIC_LOADOUTS[name]
        kw = ["VEHICLE", "WALKER", "DEEP STRIKE", "FACTION: GREY KNIGHTS"]
        return kw, info["T"], info["SV"], info["W"], info["OC"], info.get("INV")

    # Characters — read from profile data
    if name in CHARACTER_LOADOUTS:
        ps = profile_data.get("stats", {})
        t = int(str(ps.get("T", "4")).replace('"', ""))
        sv = int(str(ps.get("SV", "3+")).replace("+", "").replace('"', ""))
        w = int(str(ps.get("W", "4")).replace('"', ""))
        oc_val = int(str(ps.get("OC", "1")).replace('"', ""))
        inv = None
        for rule in profile_data.get("rules", []):
            rl = rule.upper()
            if "INVULNERABLE" in rl:
                m = re.search(r'(\d+)\+', rl)
                if m:
                    inv = int(m.group(1))
        kw = ["INFANTRY", "CHARACTER", "DEEP STRIKE", "FACTION: GREY KNIGHTS"]
        if t >= 5:
            kw.append("TERMINATOR")
        return kw, t, sv, w, oc_val, inv

    return [], 4, 3, 2, 1, None


def _loadout_desc(name, ranged, melee, innate):
    parts = []
    r_counts = {}
    for wp in ranged:
        r_counts[wp.name] = r_counts.get(wp.name, 0) + 1
    if r_counts:
        parts.append("Ranged: " + ", ".join(f"{c}×{n}" for n, c in sorted(r_counts.items())))
    m_counts = {}
    for wp in melee:
        m_counts[wp.name] = m_counts.get(wp.name, 0) + 1
    if m_counts:
        parts.append("Melee: " + ", ".join(f"{c}×{n}" for n, c in sorted(m_counts.items())))
    if innate:
        i_counts = {}
        for wp in innate:
            i_counts[wp.name] = i_counts.get(wp.name, 0) + 1
        parts.append("Innate: " + ", ".join(f"{c}×{n}" for n, c in sorted(i_counts.items())))
    return "; ".join(parts)


def _get_notes(name):
    notes_map = {
        "Strike Squad": "max 1 special; 4×SB + 4×NFW + 1×CCW default",
        "Interceptor Squad": "max 1 special; Personal Teleporters (no charge after shoot)",
        "Purifier Squad": "max 2 specials; 5×PF innate; NFW→CCW on special models",
        "Purgation Squad": "fixed: 1×Inc+1×Psil+1×Psyc; 4 models, shooty squad",
        "Brotherhood Terminator Squad": "max 2 specials; 5×NFW keep regardless; Apothecary revive",
        "Paladin Squad": "max 2 specials; BS2+ on ranged; Terminator keyword; 5×NFW A=4",
        "Nemesis Dreadknight": "Deep Strike on walker; greatsword + heavy psycannon + gatling psilencer",
        "Grand Master In Nemesis Dreadknight": "Deep Strike; Surge of Wrath (reroll vs M/V); 4++",
        "Castellan Crowe": "Leads Purifiers; +1A to Purifying Flame; A=3 on his own PF",
        "Brother-Captain": "Leads Terminators/Paladins; Hammerhand (Lethal Hits); reroll wounds",
        "Brotherhood Champion": "Leads Strike/Purgation; Clarion of Haste (Adv+Charge)",
        "Brotherhood Librarian": "Leads Terminators/Paladins; Haloed in Soulfire (18\" shoot range); FNP4+ vs Psychic",
        "Brotherhood Chaplain": "Leads Terminators/Paladins; reroll charges",
        "Grand Master": "Leads Terminators/Paladins; Might of Titan (+3A/+3S once)",
        "Grand Master Voldus": "Leads Terminators/Paladins; Sanctuary (-1 to hit); Hammer Aflame (mortals)",
        "Brotherhood Techmarine": "Leads Strike/Purgation/Purifier; heals vehicles D3",
        "Champion of Titan [Crucible]": "Leads Strike/Purgation; Might of Titan (+3A/+3S once)",
        "Land Raider": "Transport 12 (incl Terminators); 4++",
        "Land Raider Crusader": "Transport 12; 4++",
        "Land Raider Redeemer": "Transport 12; 4++",
        "Razorback": "Transport 6 (no Terminator); Twin X loadout",
        "Rhino": "Transport 6 (no Terminator); cheap taxi",
        "Venerable Dreadnought": "Deep Strike on dread; 4++",
        "Stormraven Gunship": "Transport 12 + 1 Dread; Hover; 4++",
        "Stormhawk Interceptor": "Flyer; anti-fly focused",
        "Stormtalon Gunship": "Flyer",
        "Grey Knights Thunderhawk Gunship": "Titanic Flyer; Transport; 805pts",
        "Dreadknight Champion [Crucible]": "Crucible variant; Surge of Wrath; 4++",
        "Venerable Daemon Slayer [Crucible]": "Crucible variant; Dreadnought chassis",
    }
    return notes_map.get(name, "")


def compute_ranking(target=MEQ, mission=None):
    """Compute unit ranking for a given target, optionally weighted by mission.

    Args:
        target: TargetProfile to evaluate DPP against.
        mission: Mission name from MISSION_PROFILES, or None for unweighted.

    Returns:
        list of dicts sorted by mission score (or DPP if no mission).
    """
    data_path = Path(__file__).resolve().parent.parent / "data" / "merged" / "grey-knights.json"
    data = json.loads(data_path.read_text())

    # Allow all known or static units
    known = set(SQUAD_INFO) | set(STATIC_LOADOUTS) | set(CHARACTER_LOADOUTS)

    results = []

    for unit in data["units"]:
        name = unit["name"]
        profile = unit.get("profile", {})
        kws_upper = [k.upper() for k in profile.get("keywords", [])]

        if "FACTION: GREY KNIGHTS" not in kws_upper:
            continue

        if name not in known:
            continue

        pricing = unit.get("pricing", [])
        stats = profile.get("stats", {})

        # Resolve loadout for this specific target
        resolved = resolve_loadout(name, target, pricing)
        if resolved is None:
            continue
        pts, ranged_profiles, melee_profiles, innate_profiles, info = resolved

        # DPP vs target
        dmg_ranged = compute_weapons_dpp(ranged_profiles, pts, target) if ranged_profiles else 0
        dmg_melee = compute_weapons_dpp(melee_profiles, pts, target) if melee_profiles else 0
        dmg_innate = compute_weapons_dpp(innate_profiles, pts, target) if innate_profiles else 0
        total_dmg = dmg_ranged + dmg_melee + dmg_innate
        dpp_val = total_dmg / pts if pts > 0 else 0

        # Unit info
        kw_list, t_val, sv_val, w_val, oc_val, inv_val = get_unit_info(name, profile)
        fnp_val = 6

        is_infantry = "INFANTRY" in kw_list

        n_models = 1
        if name in SQUAD_INFO:
            n_models = SQUAD_INFO[name]["n"]

        # SURV
        defense = UnitDefense(
            toughness=t_val,
            wounds_per_model=w_val,
            save=sv_val,
            invuln=inv_val,
            fnp=fnp_val if is_infantry else None,
            models=n_models,
        )
        surv = compute_surv(defense, pts)

        # MOB
        m_val = 6
        if info:
            m_val = int(re.search(r'(\d+)', str(info.get("M", "6\""))).group(1))
            if info.get("FLY"):
                kw_list.append("FLY")
        else:
            m_str = stats.get("M", "6\"")
            m_m = re.search(r'(\d+)', str(m_str))
            if m_m:
                m_val = int(m_m.group(1))

        has_fly = "FLY" in kw_list
        has_deep_strike = "DEEP STRIKE" in kw_list
        for rule in profile.get("rules", []):
            if "DEEP STRIKE" in rule.upper():
                has_deep_strike = True

        mob = compute_mob(
            movement=m_val,
            fly=has_fly,
            deep_strike=has_deep_strike,
            oc=oc_val,
            keywords=kw_list,
        )

        notes = _get_notes(name)

        results.append({
            "name": name,
            "points": pts,
            "dpp": round(dpp_val, 4),
            "total_damage": round(total_dmg, 2),
            "surv": surv,
            "mob": mob,
            "loadout_desc": _loadout_desc(name, ranged_profiles, melee_profiles, innate_profiles),
            "notes": notes,
        })

    # Sort by mission-weighted score or DPP
    if mission and mission in MISSION_PROFILES:
        w = MISSION_PROFILES[mission]
        # Compute percentiles for each vector
        dps_vals = [r["dpp"] for r in results]
        surv_vals = [r["surv"]["effective_wounds"]["ap0"] for r in results]
        mob_vals = [mob_score(r["mob"]) for r in results]
        n = len(results)

        def _pct(val, series):
            if n <= 1:
                return 100
            return round(sum(1 for x in series if x < val) / (n - 1) * 100)

        for r in results:
            r["_dps_pct"] = _pct(r["dpp"], dps_vals)
            r["_surv_pct"] = _pct(r["surv"]["effective_wounds"]["ap0"], surv_vals)
            r["_mob_pct"] = _pct(mob_score(r["mob"]), mob_vals)
            r["_mission_score"] = (
                w["dps"] * r["_dps_pct"] +
                w["surv"] * r["_surv_pct"] +
                w["mob"] * r["_mob_pct"]
            )
        results.sort(key=lambda r: r["_mission_score"], reverse=True)
    else:
        # Percentiles for standard display
        dps_vals = [r["dpp"] for r in results]
        surv_vals = [r["surv"]["effective_wounds"]["ap0"] for r in results]
        mob_vals = [mob_score(r["mob"]) for r in results]
        n = len(results)

        def _pct(val, series):
            if n <= 1:
                return 100
            return round(sum(1 for x in series if x < val) / (n - 1) * 100)

        for r in results:
            r["_dps_pct"] = _pct(r["dpp"], dps_vals)
            r["_surv_pct"] = _pct(r["surv"]["effective_wounds"]["ap0"], surv_vals)
            r["_mob_pct"] = _pct(mob_score(r["mob"]), mob_vals)
        results.sort(key=lambda r: r["dpp"], reverse=True)

    return results


def mob_score(mob):
    tier_map = {"static": 10, "slow": 25, "standard": 45, "fast": 65, "cavalry": 80, "flyer": 95, "transporter": 70}
    base = tier_map.get(mob["mobility_tier"], 30)
    bonuses = 0
    if mob.get("fly"): bonuses += 10
    if mob.get("deep_strike"): bonuses += 10
    oc_bonus = min(mob.get("objective_control", 0) * 3, 15)
    return min(base + bonuses + oc_bonus, 100)


def _bar(pct, width=10):
    filled = round(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)


def print_ranking(results, target_name="MEQ", mission_name=None):
    n = len(results)
    if not n:
        print("No results.")
        return

    title = f"## Grey Knights — Ranking vs {target_name}"
    if mission_name:
        title += f" (mission: {mission_name})"
    print(f"{title}\n")

    has_mission = "_mission_score" in results[0] if results else False

    print("```")
    if has_mission:
        header = f'{"Unit":<42s} {"Pts":>5s} {"Scr":>4s} {"DPS%":>5s} {"SURV%":>6s} {"MOB%":>5s}  Profile'
    else:
        header = f'{"Unit":<42s} {"Pts":>5s} {"DPS%":>5s} {"SURV%":>6s} {"MOB%":>5s}  Profile'
    print(header)
    print("-" * len(header))
    for r in results:
        dpb = _bar(r["_dps_pct"])
        svb = _bar(r["_surv_pct"])
        mob = _bar(r["_mob_pct"])
        if has_mission:
            print(f'{r["name"]:<42s} {r["points"]:>5d} {r["_mission_score"]:>3d}  {r["_dps_pct"]:>3d}% {r["_surv_pct"]:>3d}%  {r["_mob_pct"]:>3d}%  {dpb} {svb} {mob}')
        else:
            print(f'{r["name"]:<42s} {r["points"]:>5d} {r["_dps_pct"]:>3d}% {r["_surv_pct"]:>3d}%  {r["_mob_pct"]:>3d}%  {dpb} {svb} {mob}')
    print("```")
    print(f"  DPS% = DPP vs {target_name} percentile | SURV% = effW@AP0 percentile | MOB% = mobility score percentile")
    if has_mission:
        print(f"  Scr  = mission-weighted score (higher = better fit for {mission_name})\n")
    else:
        print()

    # ── per-unit detail ──
    for r in results:
        surv = r["surv"]
        mob = r["mob"]
        ew = surv["effective_wounds"]
        ppe = surv["pts_per_eff_w_ap0"]
        m = mob["movement"]
        fly_str = " Fly" if mob["fly"] else ""
        ds_str = " DS" if mob["deep_strike"] else ""
        tier = mob["mobility_tier"]
        line = (
            f'### {r["name"]} ({r["points"]}pts)\n'
            f'**Profile:** DPS {_bar(r["_dps_pct"])} {r["_dps_pct"]:>2d}%  '
            f'SURV {_bar(r["_surv_pct"])} {r["_surv_pct"]:>2d}%  '
            f'MOB {_bar(r["_mob_pct"])} {r["_mob_pct"]:>2d}%\n'
            f'**DPS:** DPP vs {target_name} = {r["dpp"]:.4f} (total dmg={r["total_damage"]:.2f}) | '
            f'**SURV:** effW@AP0={ew["ap0"]} AP2={ew["ap2"]} AP4={ew["ap4"]}, pts/effW={ppe} | '
            f'**MOB:** M={m}{fly_str}{ds_str} OC={mob["objective_control"]} [{tier}]\n'
            f'**Loadout:** {r["loadout_desc"]}\n'
            f'**Notes:** {r["notes"]}\n'
        )
        print(line)

    # ── assumption registry ──
    print("---\n## Assumption Registry")
    print(f"""
**Assumptions:**
- Opponent: {target_name}
- Range context: ≤12" for Storm Bolters (Rapid Fire 2 active), standard range for others
- No detachment buffs, stratagems, or command rerolls
- No cover modifiers (Psychic weapons ignore Cover [24.29]; Storm Bolters evaluated without Cover)
- No Plunging Fire modelled
- Average dice (no variance band)
- Melee DPP included in total (assumes charge reaches target)
- No FNP on the target
- No Blast minimum attacks modelled
- No Melta half-range bonus modelled
- Character buffs to their squad NOT included (only solo model output)

**What DPP does NOT model:**
- Detachment buffs (Warpbane rerolls, Argent Assault bonuses, etc.)
- Stratagem support (Sanctified Kill Zone, Truesilver Aegis, etc.)
- Warpbane Task Force Hallowed Ground bonuses
- Gate of Infinity redeployment value
- Purifying Flame Anti-Infantry 2+ critical wounds bonus
- Brotherhood Champion's charge buff for squad
- Interceptor's Personal Teleporters mobility

**Data sources:**
- Unit profiles from merged BSData+MFM JSON
- Weapon profiles from BSData via weapon_loader.py (data-driven, no hardcoded factories)
- Squad loadout limits from resources/experts/grey-knights.md
- DPP engine v1.0 from engine/dpp.py
""")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="GK Unit Ranking — three-vector DPS/SURV/MOB")
    parser.add_argument("--target", "-t", default="MEQ",
                        choices=list(TARGET_PROFILES.keys()),
                        help="Target profile to evaluate DPP against")
    parser.add_argument("--mission", "-m", default=None,
                        choices=list(MISSION_PROFILES.keys()),
                        help="Mission profile for weighted ranking")
    args = parser.parse_args()

    target = TARGET_PROFILES[args.target]
    results = compute_ranking(target=target, mission=args.mission)
    print_ranking(results, target_name=args.target, mission_name=args.mission)


if __name__ == "__main__":
    main()
