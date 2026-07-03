"""
11e DPP (Damage Per Point) engine.

Computes expected damage output for 40k 11th Edition units.
Key 11e changes from 10e:
  - Cover modifies hit roll (worsen BS by 1), NOT save
  - Plunging Fire: +1 BS for TOWERING / elevated
  - Detachment Points (DP) budget: combine 2-3 detachments
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums & types
# ---------------------------------------------------------------------------

class Ability(Enum):
    """Core weapon abilities that affect damage computation."""
    ANTI = "ANTI"
    ASSAULT = "ASSAULT"
    BLAST = "BLAST"
    CLEAVE = "CLEAVE"
    DEVASTATING_WOUNDS = "DEVASTATING WOUNDS"
    EXTRA_ATTACKS = "EXTRA ATTACKS"
    HAZARDOUS = "HAZARDOUS"
    HEAVY = "HEAVY"
    IGNORES_COVER = "IGNORES COVER"
    INDIRECT_FIRE = "INDIRECT FIRE"
    LANCE = "LANCE"
    LETHAL_HITS = "LETHAL HITS"
    MELTA = "MELTA"
    ONE_SHOT = "ONE SHOT"
    PISTOL = "PISTOL"
    PRECISION = "PRECISION"
    PSYCHIC = "PSYCHIC"
    RAPID_FIRE = "RAPID FIRE"
    SUSTAINED_HITS = "SUSTAINED HITS"
    TORRENT = "TORRENT"
    TWIN_LINKED = "TWIN-LINKED"

    @classmethod
    def from_string(cls, s: str) -> Optional["Ability"]:
        """Parse ability name from string (case-insensitive)."""
        upper = s.upper().strip()
        for a in cls:
            if a.value == upper:
                return a
        return None


class HitMode(Enum):
    """How hit rolls work — covers BS modifiers."""
    NORMAL = "normal"
    COVER = "cover"                # -1 BS
    PLUNGING_FIRE = "plunging"     # +1 BS (TOWERING / elevated)
    COVER_PLUNGING = "cover_plunging"  # cancels out (net 0)


@dataclass
class WeaponProfile:
    """Simplified weapon profile for DPP computation."""
    name: str
    attacks: float           # average attacks (or fixed value)
    bs: int                  # base BS (before modifiers)
    strength: int
    ap: int
    damage: float            # average damage
    abilities: list[str] = field(default_factory=list)  # e.g. ["SUSTAINED HITS 1", "LETHAL HITS"]


@dataclass
class TargetProfile:
    """Target unit profile for DPP computation."""
    toughness: int
    save: int                # base save (3 = 3+)
    invuln: Optional[int] = None  # e.g. 4 for 4++
    wounds_per_model: int = 1
    model_count: int = 1


@dataclass
class WeaponModifier:
    """External modifiers to a weapon's performance."""
    hit_modifier: int = 0            # net BS modifier
    wound_modifier: int = 0          # net wound modifier
    sustained_hits_extra: int = 0    # extra hits from sustained
    lethal_hits: bool = False        # auto-wound on hit
    devastating_wounds: bool = False # mortal wounds on crit wound
    reroll_hits: str | None = None   # "all", "1s", None
    reroll_wounds: str | None = None
    plus1_to_wound: bool = False
    extra_ap: int = 0
    ignore_cover: bool = False
    twin_linked: bool = False


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def expected_hits(attacks: float, bs: int, hit_mod: int = 0,
                  sustained: int = 0, lethal: bool = False,
                  reroll: str | None = None) -> tuple[float, float]:
    """
    Compute expected number of hits and lethal hits from a weapon.

    Args:
        attacks: number of attacks
        bs: ballistic skill (e.g. 3 for 3+)
        hit_mod: modifier to BS (e.g. -1 for cover)
        sustained: number of extra hits on critical hit (6+)
        lethal: if True, critical hits auto-wound
        reroll: "all", "1s", or None

    Returns:
        (expected_hits, expected_lethal_wounds)
    """
    target = bs + hit_mod  # effective BS needed

    # Probability of a single die hitting
    if target >= 6:
        p_hit = 1.0 / 6  # only on 6
        crit_range = 1  # only 6
    elif target <= 2:
        p_hit = 5.0 / 6  # 2+
        crit_range = 1  # 6 (crit is always 6)
    else:
        p_hit = (7 - target) / 6.0
        crit_range = 1  # 6 (crit on unmodified 6)

    p_crit = 1.0 / 6  # unmodified 6 is always critical
    p_normal_hit = p_hit - p_crit

    # With rerolls
    if reroll == "all":
        p_miss = 1 - p_hit
        p_hit = p_hit + p_miss * p_hit
        p_crit = p_crit + p_miss * p_crit
        p_normal_hit = p_hit - p_crit
    elif reroll == "1s":
        p_one = 1.0 / 6
        p_hit = p_hit + p_one * p_hit
        p_crit = p_crit + p_one * p_crit
        p_normal_hit = p_hit - p_crit

    # Expected hits
    normal_hits = attacks * p_normal_hit
    crit_hits = attacks * p_crit

    # Sustained hits: extra hits from criticals
    sustained_total = crit_hits * (1 + sustained)

    # Lethal hits: criticals auto-wound
    lethal_wounds = crit_hits if lethal else 0

    total_hits = normal_hits + sustained_total
    return total_hits, lethal_wounds


def expected_wounds(hits: float, lethal_wounds: float,
                    strength: int, toughness: int,
                    wound_mod: int = 0, reroll: str | None = None,
                    twin_linked: bool = False,
                    devastating: bool = False,
                    anti_info: Optional[tuple[int, int]] = None,
                    lance: bool = False) -> tuple[float, float]:
    """
    Compute expected wounds after wound roll.

    Args:
        hits: number of hits (non-lethal)
        lethal_wounds: number of auto-wounds from lethal hits
        strength: weapon strength
        toughness: target toughness
        wound_mod: modifier to wound roll
        reroll: "all", "1s", or None
        twin_linked: reroll wounds
        devastating: crit wounds cause mortal wounds
        anti_info: (anti_value, anti_target_toughness) e.g. (4, 5) for ANTI-VEHICLE 4+
        lance: if S < T, +1 to wound

    Returns:
        (expected_wounds, expected_mortal_wounds)
    """
    effective_s = strength
    effective_t = toughness

    # Determine wound target
    if anti_info:
        anti_val, anti_t = anti_info
        if tough := anti_t == toughness:
            # Anti-X: critical wounds on Anti value
            wound_target = max(2, anti_val)  # wounds on anti_val+ basically
            # Actually ANTI means: unmodified wound roll of X+ is a critical wound
            # The wound roll still needs to meet the normal threshold OR be a crit
            pass

    # S vs T comparison for wound target
    ratio = effective_s / effective_t
    if ratio >= 2:
        base_wound_target = 2
    elif ratio > 1:
        base_wound_target = 3
    elif ratio == 1:
        base_wound_target = 4
    elif ratio >= 0.5:
        base_wound_target = 5
    else:
        base_wound_target = 6

    wound_target = base_wound_target + wound_mod

    # Lance: if S < T, +1 to wound
    if lance and effective_s < effective_t:
        wound_target -= 1

    if wound_target >= 7:
        p_wound = 0
    elif wound_target <= 1:
        p_wound = 1
    else:
        p_wound = (7 - wound_target) / 6.0

    p_crit_wound = 1.0 / 6  # unmodified 6
    p_normal_wound = p_wound - p_crit_wound

    # Rerolls
    if reroll == "all" or twin_linked:
        p_fail = 1 - p_wound
        p_wound = p_wound + p_fail * p_wound
        p_crit_wound = p_crit_wound + p_fail * p_crit_wound
        p_normal_wound = p_wound - p_crit_wound
    elif reroll == "1s":
        p_one = 1.0 / 6
        p_wound = p_wound + p_one * p_wound
        p_crit_wound = p_crit_wound + p_one * p_crit_wound
        p_normal_wound = p_wound - p_crit_wound

    # Devastating Wounds: crit wounds cause mortal wounds
    normal_wounds = hits * p_normal_wound
    crit_wounds = hits * p_crit_wound
    mortal_wounds = crit_wounds if devastating else 0
    regular_wounds = normal_wounds + (crit_wounds - mortal_wounds)

    # Add lethal hits
    regular_wounds += lethal_wounds * p_wound
    mortal_wounds += lethal_wounds * (1 - p_wound) if devastating else 0

    return regular_wounds, mortal_wounds


def expected_damage(wounds: float, mortal_wounds: float,
                    ap: int, save: int, invuln: Optional[int] = None,
                    damage: float = 1,
                    ignore_cover: bool = False,
                    extra_ap: int = 0,
                    fnp: Optional[int] = None) -> float:
    """
    Compute expected damage after saves and damage.

    Args:
        wounds: regular wounds to resolve
        mortal_wounds: mortal wounds (no save)
        ap: armor penetration
        save: target save characteristic (3 = 3+)
        invuln: invulnerable save (4 = 4++)
        damage: damage per wound
        ignore_cover: ignore cover modifiers
        extra_ap: additional AP modifier
        fnp: feel no pain (5 = 5+++)

    Returns:
        expected total damage
    """
    # Determine save target
    # In 40k: AP-x worsens save by x. SV3+ AP-2 → save on 5+.
    # ap is negative (e.g. -2 for AP-2), so save - ap gives the target.
    effective_ap = ap + extra_ap  # extra_ap is also negative
    modified_save = save - effective_ap  # SV3+ AP-2 → 3-(-2)=5, save on 5+

    # Invulnerable save
    if invuln:
        save_target = max(modified_save, invuln)
    else:
        save_target = modified_save

    if save_target >= 7:
        p_save = 0
    elif save_target <= 1:
        p_save = 1
    else:
        p_save = (7 - save_target) / 6.0

    # FNP
    if fnp:
        p_fnp_save = (fnp - 1) / 6.0  # 5+ FNP = 4/6 chance of failure
    else:
        p_fnp_save = 0

    # Regular damage
    p_pass_save = 1 - p_save
    regular_damage = wounds * damage * p_pass_save * (1 - p_fnp_save)

    # Mortal damage (no save, FNP applies)
    mortal_damage = mortal_wounds * damage * (1 - p_fnp_save)

    return regular_damage + mortal_damage


# ---------------------------------------------------------------------------
# Unit survivability (SURV) and mobility (MOB) metrics
# ---------------------------------------------------------------------------


@dataclass
class UnitDefense:
    """Unit profile for survivability computation."""
    toughness: int
    wounds_per_model: int
    save: int               # 3 = 3+
    invuln: Optional[int] = None  # 4 = 4++
    fnp: Optional[int] = None     # 5 = 5+++
    models: int = 1
    feel_no_pain: Optional[int] = None  # alias for fnp


def compute_surv(
    defense: UnitDefense,
    unit_points: float = 1.0,
) -> dict:
    """
    Compute survivability metrics for a unit at different AP levels.

    Returns effective wound pool (how much raw damage must be dealt to
    kill the unit before saves) and points-per-effective-wound efficiency.

    Args:
        defense: unit defense profile
        unit_points: unit points cost

    Returns:
        dict with effective wounds at AP0, AP-2, AP-4 and efficiency
    """
    fnp = defense.fnp or defense.feel_no_pain
    total_w = defense.wounds_per_model * defense.models

    ap_levels = [0, -2, -4]
    eff_wounds = {}

    for ap in ap_levels:
        # Modified save: SV3+ vs AP-2 → save on 5+
        # Our convention: ap is negative, sv - ap gives the roll needed
        modified_save = defense.save - ap

        # Invulnerable save (lower = better). Use the better of the two.
        if defense.invuln and defense.invuln < modified_save:
            save_target = defense.invuln
        else:
            save_target = modified_save

        # Probability of FAILING the save (taking damage)
        if save_target >= 7:
            p_save = 0.0       # no save possible
        elif save_target <= 1:
            p_save = 1.0        # always saves
        else:
            p_save = (7 - save_target) / 6.0

        p_unsaved = 1 - p_save

        if p_unsaved <= 0:
            eff = float('inf')
        else:
            eff = total_w / p_unsaved

        # FNP multiplies effective wounds (FNP 5+ → need 1.5x damage)
        if fnp:
            # FNP 5+: wound ignored on 5+, so 4/6 of damage gets through
            # multiplier = 6/(fnp-1), e.g. FNP 5+ → 6/4 = 1.5
            fnp_factor = 6.0 / (fnp - 1)
            eff *= fnp_factor

        eff_wounds[f"ap{abs(ap)}"] = round(eff, 1)

    pts_per_eff_w = round(unit_points / eff_wounds["ap0"], 2) if eff_wounds["ap0"] != float('inf') else None

    return {
        "toughness": defense.toughness,
        "wounds_per_model": defense.wounds_per_model,
        "models": defense.models,
        "total_wounds": total_w,
        "save": f"{defense.save}+",
        "invuln": f"{defense.invuln}+" if defense.invuln else None,
        "fnp": f"{fnp}+" if fnp else None,
        "effective_wounds": eff_wounds,
        "pts_per_eff_w_ap0": pts_per_eff_w,
    }


def compute_mob(
    movement: int = 6,
    fly: bool = False,
    deep_strike: bool = False,
    oc: int = 1,
    keywords: Optional[list[str]] = None,
    transport_capacity: Optional[str] = None,
    abilities: Optional[list[str]] = None,
) -> dict:
    """
    Compute a mobility/utility profile for a unit.

    Returns structured data about how the unit moves and controls the board.

    Args:
        movement: movement characteristic in inches
        fly: has Fly keyword
        deep_strike: has Deep Strike ability
        oc: Objective Control characteristic
        keywords: list of keywords
        transport_capacity: e.g. "6 INFANTRY"
        abilities: list of relevant mobility abilities

    Returns:
        dict with mobility profile
    """
    kw = [k.upper() for k in (keywords or [])]
    ab = [a.upper() for a in (abilities or [])]

    has_fly = fly or "FLY" in kw
    has_deep_strike = deep_strike or "DEEP STRIKE" in ab
    is_infantry = "INFANTRY" in kw
    is_vehicle = "VEHICLE" in kw
    is_walker = "WALKER" in kw
    is_terminator = "TERMINATOR" in kw or "TERMINATOR" in str(keywords)
    is_character = "CHARACTER" in kw
    has_gate = "GATE OF INFINITY" in ab

    # Mobility tier: simple heuristic based on movement + Fly
    if movement >= 20:
        mob_tier = "skyborne"
    elif movement >= 10:
        mob_tier = "fast"
    elif movement >= 8:
        mob_tier = "cavalry"
    elif movement >= 6:
        mob_tier = "standard"
    else:
        mob_tier = "slow"

    return {
        "movement": f'{movement}"',
        "fly": has_fly,
        "deep_strike": has_deep_strike,
        "gate_of_infinity": has_gate,
        "objective_control": oc,
        "keywords": keywords or [],
        "is_infantry": is_infantry,
        "is_vehicle": is_vehicle,
        "is_terminator": is_terminator,
        "is_character": is_character,
        "transport_capacity": transport_capacity,
        "mobility_tier": mob_tier,
    }


# ---------------------------------------------------------------------------
# Full computation pipeline
# ---------------------------------------------------------------------------

def compute_weapon_dpp(weapon: WeaponProfile,
                       target: TargetProfile,
                       modifier: Optional[WeaponModifier] = None,
                       hit_mode: HitMode = HitMode.NORMAL,
                       unit_points: float = 1.0) -> dict:
    """
    Compute expected damage per point for a single weapon against a target.

    Args:
        weapon: weapon profile
        target: target profile
        modifier: external modifiers
        hit_mode: cover / plunging fire mode
        unit_points: total unit points cost

    Returns:
        dict with breakdown
    """
    mod = modifier or WeaponModifier()

    # Parse abilities from weapon
    sustained = 0
    lethal = mod.lethal_hits
    devastating = mod.devastating_wounds
    twin_linked = mod.twin_linked
    anti_info = None
    ignore_cover = mod.ignore_cover
    lance = False

    ab_set = [a.upper() for a in weapon.abilities]
    for ab in ab_set:
        if ab.startswith("SUSTAINED HITS"):
            parts = ab.split()
            if len(parts) >= 3:
                try:
                    sustained = int(parts[2])
                except ValueError:
                    sustained = 1
        elif ab == "LETHAL HITS":
            lethal = True
        elif ab == "DEVASTATING WOUNDS":
            devastating = True
        elif ab == "TWIN-LINKED":
            twin_linked = True
        elif ab == "LANCE":
            lance = True
        elif ab.startswith("ANTI"):
            m = __import__('re').match(r'ANTI[-\s]?(\w+)\s+(\d+)\+?', ab)
            if m:
                anti_info = (int(m.group(2)), None)
        elif ab == "HEAVY" and hit_mode in (HitMode.COVER, HitMode.NORMAL):
            pass  # Heavy: +1 to hit if unit didn't move (simplified)

    # Hit modifier
    # 11e: Cover = worsen BS by 1 (higher target number, e.g. 3+ → 4+)
    #       Plunging Fire = improve BS by 1 (lower target number, e.g. 3+ → 2+)
    hit_mod = mod.hit_modifier
    if hit_mode == HitMode.COVER:
        hit_mod += 1  # BS gets worse: 3+ → 4+
    elif hit_mode == HitMode.PLUNGING_FIRE:
        hit_mod -= 1  # BS gets better: 3+ → 2+
    elif hit_mode == HitMode.COVER_PLUNGING:
        pass  # net 0

    has_torrent = any("TORRENT" in a for a in ab_set)
    has_ignore_cover = any("IGNORES COVER" in a or "IGNORES_COVER" in a for a in ab_set)

    # Ignore Cover negates the cover penalty
    if has_ignore_cover and hit_mode == HitMode.COVER:
        hit_mod = 0  # no cover penalty

    # Torrent: auto-hit, skip hit roll
    if has_torrent:
        total_hits = weapon.attacks
        lethal_wounds = 0
    else:
        total_hits, lethal_wounds = expected_hits(
            attacks=weapon.attacks,
            bs=weapon.bs,
            hit_mod=hit_mod,
            sustained=sustained,
            lethal=lethal,
            reroll=mod.reroll_hits,
        )

    # Wound roll
    regular_wounds, mortal_wounds = expected_wounds(
        hits=total_hits - lethal_wounds,
        lethal_wounds=lethal_wounds,
        strength=weapon.strength,
        toughness=target.toughness,
        wound_mod=mod.wound_modifier,
        reroll=mod.reroll_wounds,
        twin_linked=twin_linked,
        devastating=devastating,
        anti_info=anti_info,
        lance=lance,
    )

    # Damage after save
    total_damage = expected_damage(
        wounds=regular_wounds,
        mortal_wounds=mortal_wounds,
        ap=weapon.ap + mod.extra_ap,
        save=target.save,
        invuln=target.invuln,
        damage=weapon.damage,
        ignore_cover=ignore_cover,
    )

    dpp = total_damage / unit_points if unit_points > 0 else 0

    return {
        "weapon": weapon.name,
        "target_toughness": target.toughness,
        "target_save": target.save,
        "expected_hits": round(total_hits, 2),
        "lethal_wounds": round(lethal_wounds, 2),
        "regular_wounds": round(regular_wounds, 2),
        "mortal_wounds": round(mortal_wounds, 2),
        "total_damage": round(total_damage, 2),
        "dpp": round(dpp, 4),
        "conditions": {
            "hit_mode": hit_mode.value,
            "hit_mod": hit_mod,
        },
    }


def compute_unit_dpp(weapons: list[WeaponProfile],
                     target: TargetProfile,
                     points: float,
                     hit_mode: HitMode = HitMode.NORMAL,
                     modifiers: Optional[list[WeaponModifier]] = None) -> dict:
    """
    Compute total DPP for a unit (all weapons combined).

    Args:
        weapons: list of weapon profiles
        target: target profile
        points: unit points cost
        hit_mode: cover / plunging fire
        modifiers: per-weapon modifiers (or same for all)

    Returns:
        dict with per-weapon breakdown + total
    """
    if modifiers is None:
        modifiers = [WeaponModifier()] * len(weapons)

    results = []
    total_damage = 0
    for i, wp in enumerate(weapons):
        mod = modifiers[i] if i < len(modifiers) else WeaponModifier()
        r = compute_weapon_dpp(wp, target, mod, hit_mode, points)
        results.append(r)
        total_damage += r["total_damage"]

    return {
        "target": {
            "toughness": target.toughness,
            "save": f"{target.save}+",
            "invuln": f"{target.invuln}+" if target.invuln else None,
        },
        "hit_mode": hit_mode.value,
        "unit_points": points,
        "total_damage": round(total_damage, 2),
        "total_dpp": round(total_damage / points if points > 0 else 0, 4),
        "weapons": results,
    }


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

def demo():
    """Run a quick comparison to demonstrate 11e rules effects."""

    # Example: Grey Knights PsyCannon vs MEQ
    psycannon = WeaponProfile(
        name="Psycannon",
        attacks=4,
        bs=3,
        strength=8,
        ap=-1,
        damage=2,
        abilities=["SUSTAINED HITS 1"],
    )

    meq = TargetProfile(toughness=4, save=3, invuln=None)

    # No cover
    result_normal = compute_weapon_dpp(psycannon, meq, unit_points=100)
    # Cover (-1 BS)
    result_cover = compute_weapon_dpp(psycannon, meq, hit_mode=HitMode.COVER, unit_points=100)
    # Plunging Fire (+1 BS)
    result_plunging = compute_weapon_dpp(psycannon, meq, hit_mode=HitMode.PLUNGING_FIRE, unit_points=100)

    print(f"{'Condition':<20} {'Hits':<8} {'Wounds':<8} {'Damage':<8} {'DPP':<8}")
    print("-" * 55)
    for label, r in [("Normal", result_normal), ("Cover (-1 BS)", result_cover),
                      ("Plunging (+1 BS)", result_plunging)]:
        print(f"{label:<20} {r['expected_hits']:<8} {r['regular_wounds']:<8} "
              f"{r['total_damage']:<8} {r['dpp']:<8}")


if __name__ == "__main__":
    demo()
