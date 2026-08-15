#!/usr/bin/env python3
"""BSData-derived alloc cap scaling — single source of truth.

BSData encodes squad-composition caps at its REFERENCE squad size (base pool
max + leaders). Configs carry squad size n from MFM pricing (first cost tier).
When n < ref the per-variant maxes must be scaled down (per-5 datasheet caps),
but FLAT caps ("up to 4 at any squad size") must be preserved verbatim.

This module is the ONE place that:
  1. derives the reference squad size from a composition,
  2. scales per-variant maxes from ref to config n,
  3. knows which variants are flat-cap exceptions.

The generator (gen_squad_composition.py) and the validator
(validate_configs_vs_bsdata.py) import from here so there is exactly one
source of computation — no duplicated formulas.

Scaling rule:
  ref = pool_capacity + len(leaders)                 # BSData squad size
  scaled_max = max(1, round(bsdata_max * n / ref))   # per-5 proportional
  base variants (max == pool capacity) -> min(n - leaders, pool capacity)
                                                      # "any number", capped by pool
  flat-cap variants -> kept verbatim (registry below)

group_max: the nested SEG's shared budget ("at most N combined"). ENCODING IS
INCONSISTENT in BSData:
  - SEGs whose name/modifiers carry a "per N models" marker store the
    REF-SCALED cap (Raptors '2 selections per 5 models' max=4 at ref 10 =
    2 per 5; Pioneers 'Heavy weapons' max=2 at ref 6 = 1 per 3) — these scale
    by n/ref (group_per5 flag).
  - SEGs without the marker store the datasheet rate verbatim (Purifier
    'Heavy weapons' max=2 IS the per-5 rate; Purgation max=4 is flat) — kept
    verbatim.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Flat-cap registry — variants whose BSData max is a FLAT datasheet cap, NOT a
# per-5 proportional cap. Verified against wahapedia 11e (see comments).
# Key: (faction_slug, unit_name, variant_name) -> the flat max to keep.
# ---------------------------------------------------------------------------
FLAT_CAPS: dict[tuple[str, str, str], int] = {
    # "Up to 4 Purgators can each have their storm bolter and Nemesis force
    # weapon replaced with one of the following: 1 incinerator / psilencer /
    # psycannon..." — flat 4 at ANY squad size (5-10 models).
    ("grey-knights", "Purgation Squad", "Purgator w/ incinerator"): 4,
    ("grey-knights", "Purgation Squad", "Purgator w/ psilencer"): 4,
    ("grey-knights", "Purgation Squad", "Purgator w/ psycannon"): 4,
    # "Up to 4 Devastator Marines can each have their boltgun replaced with
    # one of the following: 1 grav-cannon / heavy bolter / lascannon / missile
    # launcher / multi-melta / plasma cannon..." — flat 4 at ANY squad size.
    ("space-marines", "Devastator Squad", "Devastator Marine w/ Heavy Weapon"): 4,
    ("black-templars", "Devastator Squad", "Devastator Marine w/ Heavy Weapon"): 4,
    ("blood-angels", "Devastator Squad", "Devastator Marine w/ Heavy Weapon"): 4,
    ("dark-angels", "Devastator Squad", "Devastator Marine w/ Heavy Weapon"): 4,
    # Unit composition "3-6 Torments, 5-10 Mutants" — both are FLAT ranges at
    # ANY squad size (8-16 models), not per-5 caps. The two pools are coupled
    # (Torment + Mutant = squad size), so neither variant scales with n/ref.
    ("chaos-space-marines", "Accursed Cultists", "Torment"): 6,
    ("chaos-space-marines", "Accursed Cultists", "Mutant"): 10,
    # "For every 5 models in this unit, up to 2 Paladins can each have their
    # storm bolter replaced with one of the following: 1 incinerator /
    # psilencer / psycannon" — the BSData max=2 IS the per-5 rate, stored
    # verbatim without a per-5 marker (same encoding as Purifier below). The
    # generic proportional scaling wrongly halves it (2@ref10 -> 1@n5).
    ("grey-knights", "Paladin Squad", "Paladin with Heavy Weapon"): 2,
    # "Up to 2 Players can each have their shuriken pistol replaced with
    # 1 fusion pistol ..." and the same for neuro disruptor — SEPARATE flat
    # budgets of 2 at n<=9 (4 at n>=10). BSData stores max=None (no cap),
    # so without the registry the engine could take 4 fusion pistols in a
    # 5-model Troupe. Config n=5 -> cap 2.
    ("aeldari", "Troupe", "Player with Fusion Pistol"): 2,
    ("aeldari", "Troupe", "Player with Neuro Disruptor"): 2,
    # "For every 3 models in this unit, 1 Thunderwolf Cavalry model's bolt
    # pistol can be replaced with 1 plasma pistol" — per-3 rate, NOT
    # any-number. BSData stores max=6 (same as the any-number boltgun/storm
    # shield variants), so the mechanism treats it as base/any-number and
    # emits the whole budget (3 at n=3). Config n=3 -> cap 1.
    ("space-wolves", "Thunderwolf Cavalry", "Thunderwolf w/ plasma pistol"): 1,
    # Death Company: "1 model's heavy bolt pistol can be replaced with 1 hand
    # flamer / inferno pistol / plasma pistol" AND "1 model's chainsword can
    # be replaced with 1 power fist / power weapon / thunder hammer" — two
    # FLAT one-model allowances. BSData splits the non-JP unit into
    # alternate weapons (max=2 = the two flat swaps) + separate Eviscerator
    # model (per-5); the JP unit merges everything into one variant whose
    # BSData max=7 is garbage. Config n=5: non-JP 2, JP adds the per-5
    # eviscerator (1) -> 3.
    ("blood-angels", "Death Company Marines", "Death Company Marine w/ alternate weapons"): 2,
    ("blood-angels", "Death Company Marines With Bolt Rifles", "Death Company Marine w/ alternate weapons"): 2,
    ("blood-angels", "Death Company Marines With Jump Packs", "Death Company Marine w/ alternate weapons"): 3,
}

# Shared melee-weapon budgets, keyed (faction, unit, melee weapon) -> shared
# cap AT REF SQUAD SIZE. The datasheet caps the SUM of variants carrying the
# same melee weapon ("up to 3 power fists per 5 models"), but BSData splits
# them across ranged variants (combi-bolter / combi-weapon) with no group
# marker — e.g. Chaos Terminators. Without this registry the generator would
# emit 'Power fist and combi-bolter' max=3 AND 'Power fist and combi-weapon'
# max=3 at n=5, letting the engine pick 6 power fists in a 5-model squad.
#
# Values verified against 11e datasheets (wahapedia):
#   CSM/WE Terminators (ref 10): 3 per 5 power fists -> 6, 1 per 5 chainfist
#     -> 2. EC Terminators (ref 5, fixed squad): 3, 1.
SHARED_GROUPS: dict[tuple[str, str, str], int] = {
    ("chaos-space-marines", "Chaos Terminator Squad", "Power fist"): 6,
    ("chaos-space-marines", "Chaos Terminator Squad", "Chainfist"): 2,
    ("world-eaters", "Chaos Terminators", "Power fist"): 6,
    ("world-eaters", "Chaos Terminators", "Chainfist"): 2,
    ("emperors-children", "Chaos Terminators", "Power fist"): 3,
    ("emperors-children", "Chaos Terminators", "Chainfist"): 1,
}


def derive_ref(models: list[dict]) -> int | None:
    """BSData reference squad size for a composition model list.

    ref = pool capacity + number of leaders (min == max == 1). Pool capacity
    comes from the pool_capacity marker (survives the dup-strip that removes
    the base model's own max, e.g. Purgation/Purifier) or, when absent, the
    largest pool variant max (base variant, e.g. CSM 'Accursed weapon and
    combi-bolter' max=9). Returns None when no capacity is derivable — callers
    then keep BSData maxes verbatim (no scaling).
    """
    leaders = [m for m in models if m.get("min") == 1 and m.get("max", 1) == 1]
    pool = [m for m in models if not (m.get("min") == 1 and m.get("max", 1) == 1)]
    caps = [m.get("pool_capacity") for m in pool if m.get("pool_capacity") is not None]
    if not caps:
        caps = [m.get("max") for m in pool if m.get("max") is not None]
    if not caps:
        return None
    return max(caps) + len(leaders)


def scaled_max(bsdata_max: int | None, n: int, ref: int | None) -> int | None:
    """Scale a per-variant max from BSData ref squad size to config n.

    None bsdata_max -> None (no cap). None ref -> verbatim (can't derive).
    Per-5 proportional: round(max * n / ref), floor 1.
    """
    if bsdata_max is None or ref is None or ref <= 0:
        return bsdata_max
    if n >= ref:
        return bsdata_max
    return max(1, round(bsdata_max * n / ref))


def pool_capacity_of(models: list[dict]) -> int | None:
    """The pool's capacity (max models in the non-leader pool) for a
    composition model list. None when not derivable."""
    leaders = [m for m in models if m.get("min") == 1 and m.get("max", 1) == 1]
    pool = [m for m in models if not (m.get("min") == 1 and m.get("max", 1) == 1)]
    caps = [m.get("pool_capacity") for m in pool if m.get("pool_capacity") is not None]
    if not caps:
        caps = [m.get("max") for m in pool if m.get("max") is not None]
    return max(caps) if caps else None


def expected_alloc_max(
    faction: str | None,
    unit_name: str | None,
    variant_name: str,
    bsdata_max: int | None,
    n: int,
    ref: int | None,
    pool_capacity: int | None,
    budget: int,
) -> int | None:
    """Expected alloc max for one variant at config squad size n.

    Resolution order:
      1. Flat-cap registry -> verbatim value (datasheet flat cap).
      2. Base / any-number variants (max == pool capacity) -> budget
         (n - leaders): "any number of models can take this".
      3. Otherwise -> per-5 proportional scale of the BSData max.
    """
    key = (faction, unit_name, variant_name)
    if key in FLAT_CAPS:
        return FLAT_CAPS[key]
    if bsdata_max is None:
        return None
    if pool_capacity is not None and bsdata_max >= pool_capacity:
        # Base / any-number variant ("any number of models can take this"):
        # cap at the squad budget, never above the pool capacity. The min()
        # matters when the parser dropped a leader (Havocs: 4-model pool +
        # dropped champion -> budget 5, but no variant may exceed the 4-model
        # pool).
        return min(budget, pool_capacity)
    return scaled_max(bsdata_max, n, ref)


def expected_group_max(
    group_per5: bool,
    group_max: int | None,
    n: int,
    ref: int | None,
) -> int | None:
    """Expected shared group cap at config squad size n.

    group_per5: True when the nested SEG carries a "per N models" marker —
    its BSData max is ref-scaled and must be scaled by n/ref (Raptors 4@10 ->
    2@5). False: the max is already the datasheet rate (Purifier 2, Purgation
    flat 4) — kept verbatim.
    """
    if not group_per5 or group_max is None:
        return group_max
    return scaled_max(group_max, n, ref)


def expected_shared_group_max(
    faction: str | None,
    unit_name: str | None,
    melee: str | None,
    n: int,
    ref: int | None,
) -> int | None:
    """Expected shared group cap for a variant carrying `melee` at config n.

    Returns None when the melee weapon is not in SHARED_GROUPS — the variant
    has no shared-budget constraint and callers leave group_max unset. When
    found, the registry stores the cap AT REF SQUAD SIZE (verified against the
    ../../datasheet), so scale it by n/ref like any per-5 cap.
    """
    if not isinstance(melee, str) or (faction, unit_name, melee) not in SHARED_GROUPS:
        return None
    return scaled_max(SHARED_GROUPS[(faction, unit_name, melee)], n, ref)


def shared_group_weapons(faction: str | None, unit_name: str | None) -> set[str]:
    """Melee weapons that are shared-budget swaps for this unit.

    Slot choices carrying these weapons MUST NOT be emitted as nested slot
    choices: the shared budget is enforced at variant level (group_max), and a
    per-model slot copy would let the engine double-count (e.g. CSM Terminator
    Heavy weapon melee slot offering Power fist on top of the 3-per-5 power
    fist variants). The slot keeps only its default choice.
    """
    return {mw for (fac, un, mw) in SHARED_GROUPS if fac == faction and un == unit_name}
