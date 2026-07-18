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
    model_count: int = 1    # unit size — affects Blast bonus (per 5 models)


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


@dataclass
class DetachmentModifier:
    """Modifiers applied by a detachment rule to DPP/SURV/MOB computation.

    Loaded from faction pack JSON `modifiers` field. A detachment may have
    multiple modifier options (e.g. Infernal Lance chooses one of three).
    """
    name: str                          # human-readable name
    affects: str = "dpp"               # "dpp", "surv", or "mob"
    unit_filter: list[str] | None = None  # if set, only applies to units whose name matches (case-insensitive substring)
    condition: str | None = None       # human-readable condition (e.g. "only vs battle-shocked")

    # DPP modifiers — applied via WeaponModifier or toggle
    hit_modifier: int = 0              # net BS modifier (e.g. -1 for +1 to hit)
    reroll_hits: str | None = None     # "all", "1s"
    reroll_wounds: str | None = None
    plus1_to_wound: bool = False
    sustained_hits_extra: int = 0
    lethal_hits: bool = False
    extra_ap: int = 0
    ignore_cover: bool = False
    assault: bool = False              # Assault — advance & shoot
    heavy_ignore: bool = False         # ignore Heavy movement penalty

    # SURV modifiers
    invulnerable_save: int | None = None   # e.g. 5 for 5++
    feel_no_pain: int | None = None        # e.g. 6 for FNP6+
    stealth: bool = False                  # -1 to hit the unit
    cover_save: bool = False               # improved cover save

    # MOB modifiers
    movement_bonus: int = 0
    advance_and_charge: bool = False
    fallback_and_shoot: bool = False
    fallback_and_charge: bool = False

    @staticmethod
    def from_dict(d: dict) -> "DetachmentModifier":
        """Create from JSON dict (from faction pack modifiers)."""
        return DetachmentModifier(
            name=d.get("name", "Unnamed"),
            affects=d.get("affects", "dpp"),
            unit_filter=d.get("unit_filter"),
            condition=d.get("condition"),
            hit_modifier=d.get("hit_modifier", 0),
            reroll_hits=d.get("reroll_hits"),
            reroll_wounds=d.get("reroll_wounds"),
            plus1_to_wound=d.get("plus1_to_wound", False),
            sustained_hits_extra=d.get("sustained_hits_extra", 0),
            lethal_hits=d.get("lethal_hits", False),
            extra_ap=d.get("extra_ap", 0),
            ignore_cover=d.get("ignore_cover", False),
            assault=d.get("assault", False),
            heavy_ignore=d.get("heavy_ignore", False),
            invulnerable_save=d.get("invulnerable_save"),
            feel_no_pain=d.get("feel_no_pain"),
            stealth=d.get("stealth", False),
            cover_save=d.get("cover_save", False),
            movement_bonus=d.get("movement_bonus", 0),
            advance_and_charge=d.get("advance_and_charge", False),
            fallback_and_shoot=d.get("fallback_and_shoot", False),
            fallback_and_charge=d.get("fallback_and_charge", False),
        )

    def to_weapon_modifier(self) -> WeaponModifier:
        """Convert DPP-affecting fields to a WeaponModifier."""
        return WeaponModifier(
            hit_modifier=self.hit_modifier,
            sustained_hits_extra=self.sustained_hits_extra,
            lethal_hits=self.lethal_hits,
            reroll_hits=self.reroll_hits,
            reroll_wounds=self.reroll_wounds,
            plus1_to_wound=self.plus1_to_wound,
            extra_ap=self.extra_ap,
            ignore_cover=self.ignore_cover,
        )


# ---------------------------------------------------------------------------
# Merge helpers — combine multiple modifiers (multi-detachment)
# ---------------------------------------------------------------------------

def merge_weapon_modifiers(modifiers: list[WeaponModifier]) -> WeaponModifier:
    """Merge multiple WeaponModifiers into one (additive where applicable).

    Rules:
      - Numeric fields (hit_modifier, sustained_hits, extra_ap): sum
      - Boolean fields: True if any
      - Reroll fields: "all" > "1s" > None
    """
    if not modifiers:
        return WeaponModifier()
    if len(modifiers) == 1:
        return modifiers[0]

    base = WeaponModifier()
    base.hit_modifier = sum(m.hit_modifier for m in modifiers)
    base.sustained_hits_extra = sum(m.sustained_hits_extra for m in modifiers)
    base.extra_ap = sum(m.extra_ap for m in modifiers)
    base.lethal_hits = any(m.lethal_hits for m in modifiers)
    base.plus1_to_wound = any(m.plus1_to_wound for m in modifiers)
    base.ignore_cover = any(m.ignore_cover for m in modifiers)
    base.devastating_wounds = any(m.devastating_wounds for m in modifiers)
    base.twin_linked = any(m.twin_linked for m in modifiers)

    # Reroll priority: "all" > "1s" > None
    for field in ("reroll_hits", "reroll_wounds"):
        vals = [getattr(m, field) for m in modifiers if getattr(m, field)]
        if "all" in vals:
            setattr(base, field, "all")
        elif "1s" in vals:
            setattr(base, field, "1s")
    return base


def merge_detachment_modifiers(modifiers: list[DetachmentModifier]) -> DetachmentModifier:
    """Merge multiple DetachmentModifiers for SURV/MOB fields.

    Rules:
      - DPP-affecting fields: best/first (use merge_weapon_modifiers instead)
      - SURV fields: best value (lowest invuln/FNP), True if any stealth
      - MOB numeric fields: sum
      - MOB boolean fields: True if any
      - unit_filter: None if any has no filter (universal), else union
      - name: concatenated
    """
    if not modifiers:
        return DetachmentModifier(name="none")
    if len(modifiers) == 1:
        return modifiers[0]

    # Determine combined unit_filter: if any mod has no filter, combined has no filter
    has_universal = any(m.unit_filter is None for m in modifiers)
    combined_filter = None
    if not has_universal:
        combined_filter = list(set(f for m in modifiers for f in (m.unit_filter or [])))

    combined_name = " + ".join(m.name for m in modifiers if m.name and m.name != "Unnamed")
    if not combined_name:
        combined_name = "Combined"

    return DetachmentModifier(
        name=combined_name,
        affects="dpp",  # arbitrary; per-field checking used downstream
        unit_filter=combined_filter,
        condition=None,
        # DPP fields — use short-circuit: first non-zero/non-None/True wins
        hit_modifier=sum(m.hit_modifier for m in modifiers),
        sustained_hits_extra=sum(m.sustained_hits_extra for m in modifiers),
        lethal_hits=any(m.lethal_hits for m in modifiers),
        plus1_to_wound=any(m.plus1_to_wound for m in modifiers),
        extra_ap=sum(m.extra_ap for m in modifiers),
        ignore_cover=any(m.ignore_cover for m in modifiers),
        assault=any(m.assault for m in modifiers),
        heavy_ignore=any(m.heavy_ignore for m in modifiers),
        # SURV fields — best value
        invulnerable_save=min((m.invulnerable_save for m in modifiers if m.invulnerable_save), default=None),
        feel_no_pain=min((m.feel_no_pain for m in modifiers if m.feel_no_pain), default=None),
        stealth=any(m.stealth for m in modifiers),
        cover_save=any(m.cover_save for m in modifiers),
        # MOB fields — additive for numeric, any for boolean
        movement_bonus=sum(m.movement_bonus for m in modifiers),
        advance_and_charge=any(m.advance_and_charge for m in modifiers),
        fallback_and_shoot=any(m.fallback_and_shoot for m in modifiers),
        fallback_and_charge=any(m.fallback_and_charge for m in modifiers),
    )


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


# Toughness-based heuristic for Anti-Keyword matching.
# Maps an Anti keyword (e.g. "INFANTRY", "VEHICLE") to a toughness range.
# This avoids requiring TargetProfile to carry keywords, at the cost of
# edge cases (e.g. T6 Wraithlord is INFANTRY, not VEHICLE).
ANTI_KEYWORD_TOUGHNESS: dict[str, tuple[int, int]] = {
    "INFANTRY": (3, 5),
    "VEHICLE": (6, 13),
    "MONSTER": (6, 12),
    "DAEMON": (3, 5),
    "MOUNTED": (4, 5),
    "SWARM": (2, 3),
    "PSYKER": (3, 5),
    "TITANIC": (13, 14),
    "WALKER": (7, 10),
    "CHARACTER": (3, 10),   # wide range: from T3 to T10+
    "FLY": (3, 12),          # everything from T3 infantry to T12 monsters
    "BEHIND COVER": (0, 0),  # situational, never auto-matches
}


def _anti_keyword_matches(keyword: str, toughness: int) -> bool:
    """Check if an Anti-X keyword applies based on target toughness."""
    lo, hi = ANTI_KEYWORD_TOUGHNESS.get(keyword.upper(), (0, 999))
    return lo <= toughness <= hi


def expected_wounds(hits: float, lethal_wounds: float,
                    strength: int, toughness: int,
                    wound_mod: int = 0, reroll: str | None = None,
                    twin_linked: bool = False,
                    devastating: bool = False,
                    anti_info: Optional[tuple[int, str]] = None,
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
        anti_info: (anti_value, anti_keyword) e.g. (4, "VEHICLE") for ANTI-VEHICLE 4+
        lance: if S < T, +1 to wound

    Returns:
        (expected_wounds, expected_mortal_wounds)
    """
    effective_s = strength
    effective_t = toughness

    # S vs T comparison for wound target (11e Core Rules)
    ratio = effective_s / effective_t
    if ratio >= 2:
        base_wound_target = 2   # S >= 2x T
    elif ratio > 1:
        base_wound_target = 3   # S > T
    elif ratio == 1:
        base_wound_target = 4   # S == T
    elif ratio > 0.5:
        base_wound_target = 5   # S > 0.5x T (but < T)
    else:
        base_wound_target = 6   # S <= 0.5x T

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

    # Critical wound threshold:
    # - Without Anti: unmodified 6 is the only crit
    # - With Anti-X: unmodified X+ is also critical (if keyword matches)
    crit_roll = 6  # natural crit on unmodified 6
    if anti_info:
        anti_val, anti_kw = anti_info
        if anti_kw and _anti_keyword_matches(anti_kw, toughness):
            crit_roll = min(anti_val, 6)

    # A crit wound requires both wounding AND rolling at or above the crit threshold
    crit_wound_threshold = max(wound_target, crit_roll)
    if crit_wound_threshold <= 6:
        p_crit_wound = (7 - crit_wound_threshold) / 6.0
    else:
        p_crit_wound = 0.0
    p_normal_wound = max(0.0, p_wound - p_crit_wound)

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

    # Add lethal hits — auto-wounds bypass the wound roll entirely [11e core]
    regular_wounds += lethal_wounds
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
    damage_reduction: int = 0  # flat damage reduction (e.g. DWK -1)


def _wound_prob(strength: int, toughness: int) -> float:
    """11e wound table: probability to wound."""
    if strength >= 2 * toughness:
        return 5.0 / 6.0   # 2+
    if strength > toughness:
        return 4.0 / 6.0   # 3+
    if strength == toughness:
        return 3.0 / 6.0   # 4+
    if strength > toughness / 2:
        return 2.0 / 6.0   # 5+
    return 1.0 / 6.0       # 6+


def _shots_to_kill(
    total_wounds: int, toughness: int, save: int, invuln: Optional[int],
    fnp: Optional[int], bs: int, strength: int, ap: int, damage: float,
    damage_reduction: int = 0,
) -> float:
    """
    Expected number of shots (from a given weapon) to kill the unit.

    Factors in: ballistic skill, wound table, save/AP, invuln, FNP, damage reduction.

    damage_reduction: flat reduction to incoming damage (e.g. Deathwing Knights -1).
                      D1 weapons still deal D1 (can't go below 1).
    """
    p_hit = (7 - bs) / 6.0
    p_wound = _wound_prob(strength, toughness)

    # Apply damage reduction (minimum 1)
    actual_damage = max(1, damage - damage_reduction)

    # Save
    modified_save = save - ap
    if invuln and invuln < modified_save:
        save_target = invuln
    else:
        save_target = modified_save
    if save_target >= 7:
        p_unsaved = 1.0
    elif save_target <= 1:
        p_unsaved = 0.0
    else:
        p_unsaved = 1.0 - (7 - save_target) / 6.0

    # FNP
    if fnp:
        p_fnp_through = (fnp - 1) / 6.0  # FNP 5+ → 4/6 damage gets through
    else:
        p_fnp_through = 1.0

    expected_dmg = p_hit * p_wound * p_unsaved * actual_damage * p_fnp_through
    if expected_dmg <= 0:
        return float('inf')
    return round(total_wounds / expected_dmg, 1)


# Benchmark attacker profiles: (name, bs, strength, ap, avg_damage)
BENCHMARK_ATTACKERS = [
    ("bolter",     3,  4,  0, 1.0),   # BS3+ S4  AP0  D1  — volume fire
    ("plasma",     3,  7, -3, 2.0),   # BS3+ S7  AP-3 D2  — anti-MEQ
    ("lascannon",  3,  9, -3, 3.0),   # BS3+ S9  AP-3 D3  — anti-heavy
    ("melta",      3,  9, -4, 3.5),   # BS3+ S9  AP-4 D6 (~3.5 avg) — anti-vehicle
    ("heavy",      3, 14, -4, 4.5),   # BS3+ S14 AP-4 D6+1 (~4.5 avg) — dedicated anti-tank
]


def _primary_surv_metric(toughness: int) -> str:
    """Toughness-bracketed survivability metric.

    Returns the most relevant benchmark weapon for the unit's toughness
    based on what actually kills them in a balanced meta:

      T3-4  → plasma (S7 AP-3 D2) — bolters chip, plasma kills marines
      T5-6  → plasma (S7 AP-3 D2) — terminators eat plasma/autocannons
      T7-8  → melta (S9 AP-4 D6) — vehicles eat melta/lascannon
      T9-10 → lascannon (S9 AP-3 D3) — heavy vehicles eat lascannons
      T12+  → heavy (S14 AP-4 D6+1) — super-heavies eat dedicated AT

    This gives a realistic "how well does this unit survive its typical threat?"
    """
    if toughness <= 4:
        return "plasma"
    elif toughness <= 6:
        return "plasma"
    elif toughness <= 8:
        return "melta"
    elif toughness <= 10:
        return "lascannon"
    else:
        return "heavy"


def compute_surv(
    defense: UnitDefense,
    unit_points: float = 1.0,
) -> dict:
    """
    Compute survivability metrics for a unit at different AP levels.

    Returns effective wound pool (how much raw damage must be dealt to
    kill the unit before saves) and points-per-effective-wound efficiency,
    plus toughness-aware survival vs benchmark weapons.

    Args:
        defense: unit defense profile
        unit_points: unit points cost

    Returns:
        dict with effective wounds at AP0, AP-2, AP-4, and
        ``_shots_vs_<weapon>`` fields for benchmark profiles.
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

    # Toughness-aware survival: expected shots to kill by benchmark weapons
    shots_vs = {}
    pts_per_shot = {}
    for name, bs, st, ap, dmg in BENCHMARK_ATTACKERS:
        sk = _shots_to_kill(total_w, defense.toughness, defense.save, defense.invuln,
                            fnp, bs, st, ap, dmg, damage_reduction=defense.damage_reduction)
        shots_vs[f"shots_{name}"] = sk
        pts_per_shot[f"pts_per_shot_{name}"] = round(unit_points / sk, 2) if sk != float('inf') else None

    # Determine toughness-bracketed primary metric
    prim = _primary_surv_metric(defense.toughness)
    prim_key = f"shots_{prim}"
    prim_pps_key = f"pts_per_shot_{prim}"
    primary_shots = shots_vs.get(prim_key, float('inf'))
    primary_pps = pts_per_shot.get(prim_pps_key)

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
        "primary_metric": prim,
        "primary_shots": primary_shots,
        "primary_pps": primary_pps,
        **shots_vs,
        **pts_per_shot,
    }


def compute_mob(
    movement: int = 6,
    fly: bool = False,
    deep_strike: bool = False,
    oc: int = 1,
    keywords: Optional[list[str]] = None,
    transport_capacity: Optional[str] = None,
    abilities: Optional[list[str]] = None,
    gate_of_infinity: bool = False,
    no_t1_reinforcements: bool = True,
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
        gate_of_infinity: has Gate of Infinity army rule (GK redeploy per turn)
        no_t1_reinforcements: 11e rule — no reserves on T1 (reduces DS value)

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
    has_gate = gate_of_infinity or "GATE OF INFINITY" in ab

    # Mobility tier: heuristic based on movement + Fly + TRANSPORT keyword
    # FORTIFICATION (Hammerfall Bunker) = static, can't move
    # AIRCRAFT vehicles (Thunderhawk) get flyer/skyborne tier
    # FLY + TRANSPORT (Stormraven) get movement-based tier
    # TRANSPORT ground vehicles (Land Raider, Rhino) get transporter tier
    # FLY infantry (jump packs) get movement-based tier + fly bonus
    has_transport = "TRANSPORT" in kw
    has_aircraft = "AIRCRAFT" in kw
    has_fortification = "FORTIFICATION" in kw
    if has_fortification:
        mob_tier = "static"
    elif has_aircraft:
        # Fixed-wing aircraft get movement-based tier
        if movement >= 20:
            mob_tier = "skyborne"
        elif movement >= 14:
            mob_tier = "very_fast"
        else:
            mob_tier = "flyer"
    elif has_fly and has_transport:
        # Flying transport (Stormraven) — movement-based tier
        if movement >= 20:
            mob_tier = "skyborne"
        elif movement >= 14:
            mob_tier = "very_fast"
        elif movement >= 10:
            mob_tier = "fast"
        else:
            mob_tier = "standard"
    elif has_transport and is_vehicle:
        mob_tier = "transporter"
    elif movement >= 20:
        mob_tier = "skyborne"
    elif movement >= 14:
        mob_tier = "very_fast"
    elif movement >= 10:
        mob_tier = "fast"
    elif movement >= 8:
        mob_tier = "cavalry"
    elif movement >= 6:
        mob_tier = "standard"
    else:
        mob_tier = "slow"

    # Effective tier: DS upgrades slow/static significantly
    # For objective-holding, DS is king — deploy anywhere beats slow movement
    # no_t1_reinforcements limits value slightly (can't deploy T1)
    effective_tier = mob_tier
    if has_deep_strike:
        if no_t1_reinforcements:
            # Can't DS T1 — smaller tier upgrade
            if mob_tier in ("slow", "static"):
                effective_tier = "standard"
            elif mob_tier == "standard":
                effective_tier = "fast"
        else:
            # Full DS value — can deploy T1
            if mob_tier in ("slow", "static"):
                effective_tier = "fast"       # DS slow unit ≈ fast (can reach any objective)
            elif mob_tier == "standard":
                effective_tier = "very_fast"  # DS standard unit ≈ very fast

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
        "effective_tier": effective_tier,
        "no_t1_reinforcements": no_t1_reinforcements,
    }


# ---------------------------------------------------------------------------
# Full computation pipeline
# ---------------------------------------------------------------------------

def compute_weapon_dpp(weapon: WeaponProfile,
                       target: TargetProfile,
                       modifier: Optional[WeaponModifier] = None,
                       hit_mode: HitMode = HitMode.NORMAL,
                       unit_points: float = 1.0,
                       melta_active: bool = False,
                       heavy_stationary: bool = False) -> dict:
    """
    Compute expected damage per point for a single weapon against a target.

    Args:
        weapon: weapon profile
        target: target profile
        modifier: external modifiers
        hit_mode: cover / plunging fire mode
        unit_points: total unit points cost
        melta_active: assume ≤ half range for Melta bonus
        heavy_stationary: assume the unit remained stationary for Heavy bonus

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
    rapid_fire_extra = 0  # from Rapid Fire X: extra attacks at ≤12"
    blast_x = 0           # from Blast / Blast X: bonus attacks per 5 models
    melta_x = 0           # from Melta X: bonus damage at half range
    has_heavy = False     # Heavy: +1 to hit if stationary

    ab_set = [a.upper() for a in weapon.abilities]
    for ab in ab_set:
        if ab.startswith("SUSTAINED HITS"):
            parts = ab.split()
            if len(parts) >= 3:
                raw = parts[2]
                if raw == "D3":
                    sustained = 2  # average of D3 = 2
                elif raw == "D6":
                    sustained = 3  # average of D6 = 3.5, floor = 3
                else:
                    try:
                        sustained = int(raw)
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
                anti_info = (int(m.group(2)), m.group(1).upper())
        elif ab.startswith("RAPID FIRE"):
            parts = ab.split()
            if len(parts) >= 3:
                raw = parts[2]
                if raw == "D3":
                    rapid_fire_extra = 2  # average of D3 = 2
                elif raw == "D6":
                    rapid_fire_extra = 3  # average of D6 = 3.5, floor = 3
                else:
                    try:
                        rapid_fire_extra = int(raw)
                    except ValueError:
                        rapid_fire_extra = 1
        elif ab.upper().startswith("BLAST"):
            parts = ab.split()
            try:
                blast_x = int(parts[1])
            except (ValueError, IndexError):
                blast_x = 1  # plain "Blast" = Blast 1
        elif ab.upper().startswith("MELTA"):
            parts = ab.split()
            try:
                melta_x = int(parts[1])
            except (ValueError, IndexError):
                melta_x = 0
        elif ab == "HEAVY":
            has_heavy = True

    # Apply external sustained hits (from detachment modifiers, etc.)
    sustained += mod.sustained_hits_extra

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

    # Heavy: +1 to hit if the unit remained stationary
    if has_heavy and heavy_stationary:
        hit_mod -= 1  # improve BS by 1

    has_torrent = any("TORRENT" in a for a in ab_set)
    has_ignore_cover = any("IGNORES COVER" in a or "IGNORES_COVER" in a for a in ab_set)
    is_psychic = any(a == "PSYCHIC" for a in ab_set)

    # Psychic [24.29]: ignore ALL BS/WS and hit roll modifiers
    # This includes Cover, Plunging Fire, Heavy, and external mods
    if is_psychic:
        hit_mod = 0
    elif has_ignore_cover and hit_mode == HitMode.COVER:
        hit_mod = 0  # Ignore Cover negates the cover penalty

    # Blast bonus (11e [24.05]): add X attacks per 5 models in target unit
    blast_bonus = blast_x * (target.model_count // 5)

    # Apply Rapid Fire (assume ≤12" range — the "melee reach" equivalent)
    # and Blast bonus (scales with target unit size)
    effective_attacks = weapon.attacks + blast_bonus + rapid_fire_extra

    # Torrent: auto-hit, skip hit roll
    if has_torrent:
        total_hits = effective_attacks
        lethal_wounds = 0
    else:
        total_hits, lethal_wounds = expected_hits(
            attacks=effective_attacks,
            bs=weapon.bs,
            hit_mod=hit_mod,
            sustained=sustained,
            lethal=lethal,
            reroll=mod.reroll_hits,
        )

    # Wound roll (plus1_to_wound maps to wound_mod -1)
    effective_wound_mod = mod.wound_modifier
    if mod.plus1_to_wound:
        effective_wound_mod -= 1
    regular_wounds, mortal_wounds = expected_wounds(
        hits=total_hits - lethal_wounds,
        lethal_wounds=lethal_wounds,
        strength=weapon.strength,
        toughness=target.toughness,
        wound_mod=effective_wound_mod,
        reroll=mod.reroll_wounds,
        twin_linked=twin_linked,
        devastating=devastating,
        anti_info=anti_info,
        lance=lance,
    )

    # Melta: add X to damage at half range
    effective_damage = weapon.damage + (melta_x if melta_active else 0)

    # Damage after save
    total_damage = expected_damage(
        wounds=regular_wounds,
        mortal_wounds=mortal_wounds,
        ap=weapon.ap + mod.extra_ap,
        save=target.save,
        invuln=target.invuln,
        damage=effective_damage,
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
            "blast_bonus": blast_bonus,
            "melta_x": melta_x if melta_active else 0,
            "heavy_stationary": heavy_stationary and has_heavy,
        },
    }


def compute_unit_dpp(weapons: list[WeaponProfile],
                     target: TargetProfile,
                     points: float,
                     hit_mode: HitMode = HitMode.NORMAL,
                     modifiers: Optional[list[WeaponModifier]] = None,
                     melta_active: bool = False,
                     heavy_stationary: bool = False) -> dict:
    """
    Compute total DPP for a unit (all weapons combined).

    Args:
        weapons: list of weapon profiles
        target: target profile
        points: unit points cost
        hit_mode: cover / plunging fire
        modifiers: per-weapon modifiers (or same for all)
        melta_active: assume ≤ half range for Melta bonus
        heavy_stationary: assume the unit remained stationary for Heavy bonus

    Returns:
        dict with per-weapon breakdown + total
    """
    if modifiers is None:
        modifiers = [WeaponModifier()] * len(weapons)

    results = []
    total_damage = 0
    for i, wp in enumerate(weapons):
        mod = modifiers[i] if i < len(modifiers) else WeaponModifier()
        r = compute_weapon_dpp(wp, target, mod, hit_mode, points,
                               melta_active=melta_active,
                               heavy_stationary=heavy_stationary)
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
