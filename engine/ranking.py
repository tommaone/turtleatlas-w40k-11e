"""
Generic three-vector (DPS/SURV/MOB) ranking engine.

Loads faction config from data/config/{faction}/ JSON files and
unit data from data/merged/{faction}.json BSData output.

Usage:
    engine = RankingEngine("grey-knights")
    results = engine.compute_ranking(target=engine.targets["MEQ"])
    engine.print_ranking(results, target_name="MEQ")
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.dpp import (
    WeaponProfile, TargetProfile, WeaponModifier,
    compute_weapon_dpp, HitMode,
    UnitDefense, compute_surv, compute_mob,
    DetachmentModifier,
    merge_weapon_modifiers, merge_detachment_modifiers,
)
from engine.weapon_loader import WeaponCatalog


# ---------------------------------------------------------------------------
# Faction config loader
# ---------------------------------------------------------------------------

class FactionConfig:
    """Loads and holds all config JSONs for a faction."""

    def __init__(self, faction_dir: str):
        self._dir = Path(faction_dir)

        def _load(name):
            p = self._dir / f"{name}.json"
            if not p.exists():
                return {}
            data = json.loads(p.read_text())
            # Support _extends inheritance — faction overrides base keys
            extends = data.pop("_extends", None)
            if extends:
                # Resolve base relative to data/config/ (parent of faction dir)
                base_p = self._dir.parent / f"{extends}.json"
                if not base_p.exists():
                    # Fallback: same dir
                    base_p = self._dir / f"{extends}.json"
                base_data = json.loads(base_p.read_text())
                merged = {}
                merged.update(base_data)
                merged.update(data)  # faction keys override base
                return merged
            return data

        self.supported: dict = _load("supported")
        self.squads: dict = _load("squads")
        self.characters: dict = _load("characters")
        self.vehicles: dict = _load("vehicles")
        self.weapon_options: dict = _load("weapon_options")
        self.notes: dict = _load("notes")

        # Build lookup sets (skip metadata keys starting with _)
        self.known_units: set[str] = set()
        for src in (self.squads, self.characters, self.vehicles, self.weapon_options):
            self.known_units.update(k for k in src.keys() if not k.startswith("_"))

        # Extra units handled by resolve_loadout but not in config dicts
        self._extra_known: set[str] = set()
        for name in self.weapon_options:
            if name.startswith("_"):
                continue
            if name not in self.squads and name not in self.vehicles and name not in self.characters:
                self._extra_known.add(name)
        self.known_units.update(self._extra_known)

        # Target profiles
        self.target_profiles: dict[str, TargetProfile] = {}
        for name, spec in self.supported["target_profiles"].items():
            self.target_profiles[name] = TargetProfile(
                toughness=spec["toughness"],
                save=spec["save"],
                invuln=spec.get("invuln"),
                wounds_per_model=spec.get("wounds_per_model", 1),
                model_count=spec.get("model_count", 1),
            )

        # Mission profiles
        self.mission_profiles: dict = self.supported.get("mission_profiles", {})

        # Meta profiles
        self.meta_profiles: dict = self.supported.get("meta_profiles", {})

        # Force Dispositions — maps detachment kebab-case name → disposition ID
        self.dispositions: dict[str, str] = self.supported.get("dispositions", {})

    @property
    def faction_key(self) -> str:
        return self.supported.get("key", "")

    @property
    def army_rules(self) -> list[str]:
        return self.supported.get("army_rules", [])

    @property
    def faction_keywords(self) -> list[str]:
        return self.supported.get("keywords", [])

    def get_detachments_for_disposition(self, disposition_id: str) -> list[str]:
        """Return detachment names whose disposition matches the given ID."""
        return [
            det_name for det_name, disp in self.dispositions.items()
            if disp == disposition_id
        ]

    def can_detachment_play_disposition(self, det_name: str, disposition_id: str) -> bool:
        """Check if a detachment is valid for a given disposition."""
        actual = self.dispositions.get(det_name.lower().replace(" ", "-"))
        return actual == disposition_id

    def is_legends(self, name: str) -> bool:
        """Check if a unit is marked as Legends (unavailable in regular play)."""
        for d in (self.squads, self.characters, self.vehicles, self.weapon_options):
            entry = d.get(name)
            if entry and isinstance(entry, dict) and entry.get("legends"):
                return True
        return False

    def _resolve_meta(self, meta_spec):
        """Convert meta profile name or list to (name, TargetProfile, weight) list."""
        if isinstance(meta_spec, str):
            raw = self.meta_profiles[meta_spec]
        else:
            raw = meta_spec
        # Support both old format (list of [name, weight]) and new format (dict with "profiles" key)
        spec = raw["profiles"] if isinstance(raw, dict) else raw
        total = sum(w for _, w in spec)
        return [(tn, self.target_profiles[tn], w / total) for tn, w in spec]


# ---------------------------------------------------------------------------
# Ranking engine
# ---------------------------------------------------------------------------

def _load_catalog(merged_path: str, faction: str | None = None) -> WeaponCatalog:
    """Load WeaponCatalog from a merged JSON path.

    For SM subfactions, also load SM's merged data as fallback so weapons
    referenced from the base SM catalog can be found.
    """
    cat = WeaponCatalog(merged_path, faction=faction)
    # SM subfactions inherit from Space Marines — load SM weapons as fallback
    SM_SUBFACTIONS = {
        'dark-angels', 'blood-angels', 'black-templars', 'space-wolves',
        'deathwatch', 'imperial-fists', 'iron-hands', 'raven-guard',
        'salamanders', 'ultramarines', 'white-scars',
    }
    if faction and faction in SM_SUBFACTIONS:
        sm_path = str(Path(merged_path).parent / "space-marines.json")
        if Path(sm_path).exists():
            sm_cat = WeaponCatalog(sm_path, faction='space-marines')
            for key, entries in sm_cat.by_name.items():
                if key not in cat.by_name:
                    cat.by_name[key] = entries
    return cat


def _ld_dmg(ranged, melee, innate, target, modifier: Optional[WeaponModifier] = None,
            melta_active: bool = False, heavy_stationary: bool = False,
            hit_mode: HitMode = HitMode.NORMAL, n_models: int = 1):
    """Total damage across all weapon lists against a target.

    11e melee rule [24.11]: [Extra Attacks] weapons are ALWAYS used in
    addition to one other melee weapon. So for melee:
      - All [EA] weapons are summed
      - The best non-[EA] weapon is chosen per model
      - If all weapons are [EA], sum all

    Multi-model handling (n_models):
      - n_models=1 (character): multiple melee weapons = loadout choices → pick best (max)
      - n_models>1 (squad): resolve_loadout returns one weapon per model →
        best per model = max within each model's options, then SUM across models.
        The weapon list already has n_models entries (one per model), each already
        the best pick for that model's loadout. Sum them all.
    """
    d = 0
    for wp in ranged:
        d += _wp_dmg(wp, target, modifier, melta_active=melta_active,
                     heavy_stationary=heavy_stationary, hit_mode=hit_mode)

    ea_melee = []
    other_melee = []
    for wp in melee:
        if "Extra Attacks" in wp.abilities or "Extra Attack" in wp.abilities:
            ea_melee.append(wp)
        else:
            other_melee.append(wp)

    if ea_melee:
        for wp in ea_melee:
            d += _wp_dmg(wp, target, modifier, melta_active=melta_active,
                         heavy_stationary=heavy_stationary, hit_mode=hit_mode)
        if other_melee:
            d += _best_melee(other_melee, target, modifier, melta_active,
                             heavy_stationary, hit_mode, n_models)
    elif other_melee:
        d += _best_melee(other_melee, target, modifier, melta_active,
                         heavy_stationary, hit_mode, n_models)

    for wp in innate:
        d += _wp_dmg(wp, target, modifier, melta_active=melta_active,
                     heavy_stationary=heavy_stationary, hit_mode=hit_mode)
    return d


def _ld_dmg_conditional(ranged, melee, innate, target, base_mod,
                        reroll_spec, phase, melta_active=False,
                        heavy_stationary=False, hit_mode=HitMode.NORMAL,
                        n_models=1):
    from engine.reroll_detect import _target_matches

    def _phase_applies():
        ph = reroll_spec["phase"]
        if ph == "both":
            return True
        return ph == phase  # phase is "ranged" or "melee" for the list being computed

    def _mod(include):
        if base_mod is None:
            m = WeaponModifier()
        else:
            m = WeaponModifier(
                hit_modifier=base_mod.hit_modifier,
                sustained_hits_extra=base_mod.sustained_hits_extra,
                lethal_hits=base_mod.lethal_hits,
                plus1_to_wound=base_mod.plus1_to_wound,
                extra_ap=base_mod.extra_ap,
                ignore_cover=base_mod.ignore_cover,
                twin_linked=base_mod.twin_linked,
                devastating_wounds=base_mod.devastating_wounds,
                reroll_hits=base_mod.reroll_hits,
                reroll_wounds=base_mod.reroll_wounds,
                reroll_damage=base_mod.reroll_damage,
            )
        if include:
            for f in ("reroll_hits", "reroll_wounds", "reroll_damage"):
                a = getattr(m, f)
                b = reroll_spec.get(f)
                setattr(m, f, _pick(a, b))
        return m

    def _one(pro, w):
        inc = _target_matches(reroll_spec["targets"], pro.toughness) and _phase_applies()
        return _ld_dmg(ranged, melee, innate, pro, _mod(inc),
                       melta_active=melta_active, heavy_stationary=heavy_stationary,
                       hit_mode=hit_mode, n_models=n_models) * w

    return sum(_one(p, w) for _, p, w in target) if isinstance(target, list) \
        else _one(target, 1.0)


def _pick(a, b):
    """Merge two reroll modes: 'all' > '1s' > None."""
    if not a and not b:
        return None
    if "all" in (a, b):
        return "all"
    if "1s" in (a, b):
        return "1s"
    return None


def _best_melee(weapons, target, modifier, melta_active, heavy_stationary, hit_mode,
                n_models: int = 1):
    """Best melee damage considering model count.

    n_models=1 (character): multiple weapons = loadout choices → pick best (max).
    n_models>1 (squad): weapon list already has one entry per model (resolved by
    _best_squad_variant). Each entry is already the best for that model. Sum all.
    """
    if n_models <= 1:
        # Character / single model: pick best weapon
        return max(
            (_wp_dmg(wp, target, modifier, melta_active=melta_active,
                     heavy_stationary=heavy_stationary, hit_mode=hit_mode)
             for wp in weapons),
            default=0
        )

    # Squad: one weapon per model → sum all
    return sum(
        _wp_dmg(wp, target, modifier, melta_active=melta_active,
                heavy_stationary=heavy_stationary, hit_mode=hit_mode)
        for wp in weapons
    )


def _reduce_squad_melee(melee: list, target, modifier: Optional[WeaponModifier] = None,
                        melta_active: bool = False, heavy_stationary: bool = False,
                        hit_mode: HitMode = HitMode.NORMAL) -> list:
    """Reduce a model's fixed melee weapons to the squad contract: one
    non-Extra-Attacks weapon per model (all [EA] weapons kept, added on top).
    Mirrors _ld_dmg's melee rule [24.11] so a model with [Power sword, Close
    Combat Weapon] contributes only its best weapon.
    """
    if len(melee) <= 1:
        return melee
    ea = [w for w in melee if "Extra Attacks" in w.abilities or "Extra Attack" in w.abilities]
    others = [w for w in melee if w not in ea]
    if not others:
        return melee
    best = max(others, key=lambda w: _wp_dmg(w, target, modifier, melta_active=melta_active,
                                             heavy_stationary=heavy_stationary,
                                             hit_mode=hit_mode))
    return ea + [best]


def _best_alloc_index(metas: list[dict], alloc_n: list[int], indices,
                      groups: dict | None = None) -> int:
    """Index of the highest-damage alloc variant among indices with spare
    capacity (cap = its max, or unlimited when max is absent).

    Variants tagged with a shared group_max may together contribute at most
    group_max (e.g. Purgation's 'Heavy Weapons' group: 4 specials total,
    mixed freely across types) — a variant whose group is at cap is skipped.
    """
    best_i, best_d = -1, -1
    for i in indices:
        m = metas[i]
        cap = m["max"] if m["max"] is not None else float("inf")
        if alloc_n[i] >= cap:
            continue
        gm = m.get("group_max")
        if gm and groups and gm in groups:
            used = sum(alloc_n[j] for j in groups[gm])
            if used >= gm:
                continue
        if m["dmg"] > best_d:
            best_i, best_d = i, m["dmg"]
    return best_i


def _wp_dmg(wp, target, modifier: Optional[WeaponModifier] = None,
            melta_active: bool = False, heavy_stationary: bool = False, hit_mode: HitMode = HitMode.NORMAL):
    """Damage for a single weapon against target (single or weighted list)."""
    if isinstance(target, list):
        return sum(w * compute_weapon_dpp(wp, tp, modifier=modifier, unit_points=1, hit_mode=hit_mode,
                                          melta_active=melta_active, heavy_stationary=heavy_stationary)["total_damage"]
                   for _, tp, w in target)
    return compute_weapon_dpp(wp, target, modifier=modifier, unit_points=1, hit_mode=hit_mode,
                              melta_active=melta_active, heavy_stationary=heavy_stationary)["total_damage"]


# ---------------------------------------------------------------------------
# Terrain ability detection
# ---------------------------------------------------------------------------

# Patterns that indicate a unit can traverse terrain despite being a Vehicle/Monster/Titanic.
# Scanned against ability descriptions (case-insensitive).
_TERRAIN_ABILITY_PATTERNS = [
    "titanic stride",
    "titanic agil",
    "titanic advance",
    "scuttling walker",
    "clankin' forward",
    "clankin\u2019 forward",
    "stompin' forward",
    "stompin\u2019 forward",
    "gargantuan",      # Gargantuan Squiggoth — moves over terrain 4"
    "heavy walker",    # Stormsurge
    "stalking forward",  # Hierophant
    "serpentine",      # Fulgrim
    "skilled riders",  # Suboden Khan
    "fire riders",     # Lord Invocatus
    "aggressive advance",  # Lord on Juggernaut
    "shokk-boosta",    # Big Mek
    "move through terrain",
    "move over terrain",
    "move through models",
    "move over models",
    "move over sections of terrain",
]

# Rules-level terrain traversal — "Super-Heavy Walker" lives in rules[], not abilities[]
_TERRAIN_RULE_PATTERNS = [
    "super-heavy walker",
]


def _has_terrain_ability(profile: dict) -> bool:
    """Detect if a unit has a special ability that allows terrain traversal.

    Scans BOTH the unit's abilities list AND rules list for known terrain
    interaction patterns. "Super-Heavy Walker" lives in rules[], while
    "Clankin' Forward" etc. live in abilities[].
    """
    profile = profile or {}
    # Check abilities (named abilities with descriptions)
    for ability in profile.get("abilities") or []:
        desc = (ability.get("description") or "").lower()
        name = (ability.get("name") or "").lower()
        for pattern in _TERRAIN_ABILITY_PATTERNS:
            if pattern in desc or pattern in name:
                return True
    # Check rules (e.g. "Super-Heavy Walker" is a rule, not an ability)
    for rule in profile.get("rules") or []:
        rule_lower = str(rule).lower()
        for pattern in _TERRAIN_RULE_PATTERNS:
            if pattern in rule_lower:
                return True
    return False


def _has_frame_keyword(profile: dict) -> bool:
    """Detect if unit has Frame keyword — hull measurement, no base.

    Frame units (Baneblade, Lord of Skulls) measure to hull, not base.
    They can't fit through terrain gaps and must go diagonally (2x movement cost).
    """
    keywords = (profile or {}).get("keywords") or []
    return "Frame" in keywords


class RankingEngine:
    """Ranking engine for a specific faction."""

    def __init__(self, faction_key: str, no_t1_reinforcements: bool = True):
        self.faction_key = faction_key
        self.no_t1_reinforcements = no_t1_reinforcements
        repo_root = Path(__file__).resolve().parent.parent

        # Config dir: data/config/{faction_key}/
        config_dir = repo_root / "data" / "config" / faction_key
        if not config_dir.exists():
            raise FileNotFoundError(
                f"No config dir for faction '{faction_key}': {config_dir}"
            )
        self.config = FactionConfig(str(config_dir))

        # Merged data: data/merged/{faction_key}.json
        self.merged_path = str(repo_root / "data" / "merged" / f"{faction_key}.json")
        self.catalog = _load_catalog(self.merged_path, faction=faction_key)
        self.data = json.loads(Path(self.merged_path).read_text())

        # Extra merged sources — for subfactions that share units with parent factions
        # e.g. dark-angels config includes generic SM chars from space-marines.json
        extras = self.config.supported.get("merged_extras", [])
        if extras:
            seen_names = {u["name"] for u in self.data["units"]}
            for extra_key in extras:
                extra_path = repo_root / "data" / "merged" / f"{extra_key}.json"
                if extra_path.exists():
                    extra_data = json.loads(extra_path.read_text())
                    for u in extra_data["units"]:
                        if u["name"] not in seen_names:
                            self.data["units"].append(u)
                            seen_names.add(u["name"])

        # Detachment modifiers — loaded lazily on first access
        self._detachment_modifiers: dict[str, list[DetachmentModifier]] | None = None

    # ── Detachment modifiers ───────────────────────────────────────────

    def _load_detachment_modifiers(self) -> dict[str, list[DetachmentModifier]]:
        """Load detachment modifiers from faction pack JSON.

        Returns dict mapping detachment name → list of DetachmentModifier choices.
        """
        if self._detachment_modifiers is not None:
            return self._detachment_modifiers

        repo_root = Path(__file__).resolve().parent.parent

        # Try config dir first (our own data, no GW IP)
        config_mod_path = repo_root / "data" / "config" / self.faction_key / "detachment_modifiers.json"
        if config_mod_path.exists():
            config_data = json.loads(config_mod_path.read_text())
            raw = config_data.get("detachments", {})
            result = {}
            for det_name, det_data in raw.items():
                choices = det_data.get("choices", [])
                if choices:
                    result[det_name] = [DetachmentModifier.from_dict(c) for c in choices]
            self._detachment_modifiers = result
            return result

        # Fallback: old faction-pack JSON location (may not exist after GW IP cleanup)
        fp_name = f"{self.faction_key}-faction-pack.json"
        fp_path = repo_root / "data" / fp_name
        if not fp_path.exists():
            self._detachment_modifiers = {}
            return self._detachment_modifiers

        fp = json.loads(fp_path.read_text())
        result = {}
        for det in fp.get("detachments", []):
            mods_data = det.get("modifiers", {})
            choices = mods_data.get("choices", [])
            if choices:
                mods = [DetachmentModifier.from_dict(c) for c in choices]
                result[det["name"]] = mods
        self._detachment_modifiers = result
        return result

    def get_detachment_modifiers(self, detachment_name: str) -> list[DetachmentModifier]:
        """Get modifier choices for a given detachment."""
        mods = self._load_detachment_modifiers()
        return mods.get(detachment_name.upper(), [])

    def list_detachments_with_modifiers(self) -> list[str]:
        """List detachment names that have defined modifiers."""
        return list(self._load_detachment_modifiers().keys())

    # ── Helper: load weapon via catalog ───────────────────────────────

    def W(self, name: str, **kw) -> WeaponProfile:
        """Load a weapon profile from the catalog (shortcut)."""
        return self.catalog.load(name, **kw)

    # ── Target / meta helpers ─────────────────────────────────────────

    def resolve_target(self, target_name: str) -> TargetProfile:
        """Get a TargetProfile by name."""
        return self.config.target_profiles[target_name]

    def resolve_meta(self, meta_spec):
        """Convert meta profile name to (name, TargetProfile, weight) list."""
        return self.config._resolve_meta(meta_spec)

    # ── Loadout resolution ────────────────────────────────────────────

    def _best_choice_combo(self, base_r: list, base_m: list, slots, unit_name: str,
                           target) -> tuple[list, list]:
        """Pick the best bundle combo for a model/choice with slots.

        Each slot is choose-one over choices; bundles override the base
        weapons for the types present. Returns (best_ranged, best_melee).
        With no slots or no target, returns the base loadout unchanged.
        """
        if not slots or target is None:
            return base_r, base_m
        import itertools
        slot_choice_lists = [s["choices"] for s in slots]
        best_d, best_r, best_m = -1, None, None
        for combo in itertools.product(*slot_choice_lists):
            combo_r = list(base_r)
            combo_m = list(base_m)
            skip = False
            for choice in combo:
                try:
                    if "ranged" in choice:
                        combo_r = [self.W(choice["ranged"], unit_name=unit_name,
                                          count=1, category="ranged")
                                   for _ in range(choice.get("ranged_count", 1) or 1)]
                    if "melee" in choice:
                        combo_m = [self.W(choice["melee"], unit_name=unit_name,
                                          count=1, category="melee")
                                   for _ in range(choice.get("melee_count", 1) or 1)]
                except KeyError:
                    skip = True
                    break
            if skip:
                continue
            d = _ld_dmg(combo_r, combo_m, [], target, n_models=1)
            if d > best_d:
                best_d, best_r, best_m = d, combo_r, combo_m
        if best_r is None:
            return base_r, base_m
        return best_r, best_m

    def _resolve_alloc_model(self, model: dict, unit_name: str, target,
                             ranged: list, melee: list, alloc_info: list) -> None:
        """Distribute the squad budget across parallel-variant choices.

        Parallel variants (Troupe players, Windriders, Storm Guardians) share
        the squad's model budget. Each variant contributes independent
        per-model damage, so the optimal allocation is greedy: fill per-variant
        minimums first, then assign remaining models to the highest-damage
        variant with spare capacity.
        """
        count = model.get("count", 0)
        if count <= 0:
            return
        choices = model.get("alloc", []) or []
        metas = []
        for ch in choices:
            r_names = ch.get("ranged") or []
            m_names = ch.get("melee") or []
            if isinstance(r_names, str):
                r_names = [r_names]
            if isinstance(m_names, str):
                m_names = [m_names]
            base_r = [self.W(rn, unit_name=unit_name, count=1, category="ranged") for rn in r_names]
            base_m = [self.W(mn, unit_name=unit_name, count=1, category="melee") for mn in m_names]
            try:
                ch_r, ch_m = self._best_choice_combo(base_r, base_m, ch.get("slots"),
                                                     unit_name, target)
                if target is not None:
                    ch_m = _reduce_squad_melee(ch_m, target)
                dmg = _ld_dmg(ch_r, ch_m, [], target, n_models=1) if target is not None else 0
            except KeyError:
                dmg = -1
                ch_r, ch_m = [], []
            metas.append({"name": ch.get("name", ""), "ranged": ch_r, "melee": ch_m,
                          "dmg": dmg, "min": ch.get("min", 0) or 0, "max": ch.get("max"),
                          "pool_min": ch.get("pool_min", 0) or 0,
                          "group_max": ch.get("group_max", 0) or 0})
        alloc_n = [0] * len(metas)
        remaining = count
        # Shared caps (e.g. Purgation 'Heavy Weapons' max=4): variants in the
        # same group may together contribute at most group_max. Enforced in
        # _best_alloc_index so both the pool loop and the greedy fill stop at
        # the combined budget.
        groups: dict[int, list[int]] = {}
        for i, m in enumerate(metas):
            if m["group_max"]:
                groups.setdefault(m["group_max"], []).append(i)
        # Per-variant minimums (e.g. Ynnari Reaver min=2) fill first.
        for i, m in enumerate(metas):
            take = min(m["min"], remaining)
            alloc_n[i] = take
            remaining -= take
        # Nested pool minimums (e.g. Voidscarred base pool min=4): variants
        # sharing a pool_min must together contribute at least that many.
        pools: dict[int, list[int]] = {}
        for i, m in enumerate(metas):
            if m["pool_min"]:
                pools.setdefault(m["pool_min"], []).append(i)
        for pool_min, members in pools.items():
            while sum(alloc_n[i] for i in members) < pool_min and remaining > 0:
                best_i = _best_alloc_index(metas, alloc_n, members, groups)
                if best_i < 0:
                    break
                alloc_n[best_i] += 1
                remaining -= 1
        # Remaining budget → highest-damage variant with spare capacity.
        while remaining > 0:
            best_i = _best_alloc_index(metas, alloc_n, range(len(metas)), groups)
            if best_i < 0:
                break
            alloc_n[best_i] += 1
            remaining -= 1
        used = [(metas[i]["name"], alloc_n[i])
                for i in range(len(metas)) if alloc_n[i] > 0]
        if used:
            alloc_info.append((model.get("name", "Model"), used))
        for i, m in enumerate(metas):
            for _ in range(alloc_n[i]):
                ranged.extend(m["ranged"])
                melee.extend(m["melee"])

    def _alloc_combo_space(self, choices: list[dict], count: int) -> int:
        """Count the loadout space of an alloc model: bounded compositions of
        `count` across the variant choices (each capped by its max; variants
        tagged with a shared group_max may together contribute at most that).
        """
        if count <= 0 or not choices:
            return 1
        n = len(choices)
        caps = [ch.get("max") if ch.get("max") is not None else count
                for ch in choices]
        # Group membership keyed by group_max value (one shared-cap group per
        # unit in practice — Purgation/Purifier 'Heavy Weapons').
        groups: dict[int, list[int]] = {}
        for i, ch in enumerate(choices):
            gm = ch.get("group_max")
            if gm:
                groups.setdefault(gm, []).append(i)
        gid_of: dict[int, int] = {}
        for k, members in groups.items():
            for i in members:
                gid_of[i] = k
        group_order = list(groups.keys())

        from functools import lru_cache
        @lru_cache(maxsize=None)
        def dfs(i: int, remaining: int, used: tuple) -> int:
            # Exact compositions: all `count` models must be allocated, so the
            # last variant must consume whatever is left.
            if i == n:
                return 1 if remaining == 0 else 0
            total = 0
            cap = min(caps[i], remaining)
            if i in gid_of:
                k = gid_of[i]
                pos = group_order.index(k)
                limit = k  # group key IS the shared group_max value
                for t in range(cap + 1):
                    if used[pos] + t > limit:
                        continue
                    u = list(used)
                    u[pos] += t
                    total += dfs(i + 1, remaining - t, tuple(u))
            else:
                for t in range(cap + 1):
                    total += dfs(i + 1, remaining - t, used)
            return total

        return dfs(0, count, tuple([0] * len(group_order)))

    def _eval_squad_build(self, build, unit_name, target=None):
        """Evaluate one explicit build for a squad.

        Each build has a 'models' array: [{count, ranged, melee}, ...]
        Models may carry per-model 'slots' (choose-one groups, mirroring BSData
        composition): the best combo of slot choices is picked independently
        per model type (squad damage sums over models) and each choice's bundle
        payload ({ranged, melee}) OVERRIDES that model's top-level weapons for
        the types present.

        Models may instead carry 'alloc' (parallel variants): the count is a
        budget distributed across the variant choices (see _resolve_alloc_model).

        Returns {"ranged": [...], "melee": [...], "innate": [], "_build": build_dict}
        with one weapon entry per model (count models × each weapon).
        """
        ranged, melee, innate = [], [], []
        alloc_info = []
        for model in build["models"]:
            if model.get("alloc"):
                self._resolve_alloc_model(model, unit_name, target, ranged, melee, alloc_info)
                continue
            count = model.get("count", 1)
            r_names = model.get("ranged") or []
            m_names = model.get("melee") or []
            if isinstance(r_names, str):
                r_names = [r_names]
            if isinstance(m_names, str):
                m_names = [m_names]
            r_kw = {}
            if "ranged_a" in model:
                r_kw["a"] = model["ranged_a"]
            base_r = [self.W(rn, unit_name=unit_name, count=1, category="ranged", **r_kw)
                      for rn in r_names]
            base_m = [self.W(mn, unit_name=unit_name, count=1, category="melee") for mn in m_names]

            # Per-model slots: pick the best bundle combo for this model type.
            best_r, best_m = self._best_choice_combo(base_r, base_m, model.get("slots"),
                                                     unit_name, target)
            # Fixed melee may list several weapons (Power sword + CCW): the
            # squad damage contract is one non-EA melee weapon per model.
            if target is not None:
                best_m = _reduce_squad_melee(best_m, target)
            for _ in range(count):
                ranged.extend(best_r)
                melee.extend(best_m)
        result = {"ranged": ranged, "melee": melee, "innate": innate, "_build": build}
        if alloc_info:
            result["_alloc_info"] = alloc_info
        return result

    def _best_squad_variant(self, name, target, mode=None):
        """Find optimal build for a squad vs a target.

        All squads use the builds format (legacy specials/special_max path
        removed — 467/467 squads converted fleet-wide). See
        scripts/convert_squad_builds.py for the converter.
        """
        cfg = self.config.squads.get(name)
        if not cfg:
            return None
        unit_name = cfg.get("unit") or name
        return self._best_squad_build(cfg, unit_name, target, mode=mode)

    def _best_squad_build(self, cfg, unit_name, target, mode=None):
        """Pick best build from explicit builds array.

        Each build defines a full squad loadout as model entries.
        DPP = total squad damage / n (per-model contribution).
        Returns the best build's loadout dict.
        """
        n = cfg["n"]
        builds = [b for b in cfg["builds"] if not mode or b.get("name") == mode]
        n_combos = len(builds)
        if mode and not builds:
            raise ValueError(
                f"Unknown mode '{mode}' for {unit_name}. Available modes: {[b.get('name') for b in cfg['builds']]}"
            )
        best, best_dpp = None, -1
        for build in builds:
            ld = self._eval_squad_build(build, unit_name, target=target)
            # Squad-level innate weapons (e.g. Purifying Flame on every
            # Purifier model) apply once per model — mirror the legacy path.
            if cfg.get("innate"):
                for _ in range(n):
                    for iname in cfg["innate"]:
                        ld["innate"].append(self.W(iname, unit_name=unit_name, count=1))
            total_d = _ld_dmg(ld["ranged"], ld["melee"], ld["innate"], target, n_models=n)
            dpp = total_d / n if n > 0 else 0
            if dpp > best_dpp:
                best_dpp = dpp
                best = ld

        if best:
            # Combo space = builds × per-model slot combos (e.g. Dark Reapers
            # exarch Weapon slot explores 4 choices → 4 combos, not 1) × alloc
            # distributions for parallel-variant models (bounded compositions).
            slot_combos = 1
            for m in best.get("_build", {}).get("models", []):
                for slot in m.get("slots", []) or []:
                    slot_combos *= max(1, len(slot.get("choices", []) or []))
                if m.get("alloc"):
                    slot_combos *= self._alloc_combo_space(m["alloc"], m.get("count", 0))
            n_combos = len(builds) * slot_combos
            best["_n_combos"] = n_combos
            # Build description with per-model breakdown
            r_counts = {}
            for wp in best["ranged"]:
                r_counts[wp.name] = r_counts.get(wp.name, 0) + 1
            m_counts = {}
            for wp in best["melee"]:
                m_counts[wp.name] = m_counts.get(wp.name, 0) + 1

            target_tag = None
            for tname, tp in self.config.target_profiles.items():
                if target == tp:
                    target_tag = tname
                    break
            tag = target_tag or (
                "meta" if isinstance(target, list) else "custom"
            )

            # Human-readable model list from the winning build
            build_info = best.get("_build", {})
            alloc_info = best.get("_alloc_info", [])
            alloc_by_name = {name: used for name, used in alloc_info}
            model_parts = []
            for m in build_info.get("models", []):
                count = m.get("count", 1)
                if m.get("alloc"):
                    used = alloc_by_name.get(m.get("name"), [])
                    inner = ", ".join(f"{n}×{cname}" for cname, n in used) if used else "-"
                    model_parts.append(f"{count}×{m.get('name', 'Model')}[{inner}]")
                    continue
                r = m.get("ranged", "-")
                me = m.get("melee", "-")
                if isinstance(r, list):
                    r = "+".join(r)
                if isinstance(me, list):
                    me = "+".join(me)
                model_parts.append(f"{count}×{r}+{me}")
            parts = ["Models: " + ", ".join(model_parts)]
            parts.append(f"[best of {n_combos} builds vs {tag}, DPP/model={best_dpp:.4f}]")
            best["_desc"] = "; ".join(parts)

            # Weapon details for turtledeck — full stats per weapon
            weapon_details = []
            for wp in best["ranged"]:
                weapon_details.append({
                    "slot": "ranged",
                    "name": wp.name,
                    "attacks": wp.attacks,
                    "skill": wp.bs,
                    "strength": wp.strength,
                    "ap": wp.ap,
                    "damage": wp.damage,
                    "abilities": wp.abilities,
                })
            for wp in best["melee"]:
                weapon_details.append({
                    "slot": "melee",
                    "name": wp.name,
                    "attacks": wp.attacks,
                    "skill": wp.bs,
                    "strength": wp.strength,
                    "ap": wp.ap,
                    "damage": wp.damage,
                    "abilities": wp.abilities,
                })
            best["_weapon_details"] = weapon_details
            best["_dpp_per_model"] = best_dpp
        return best

    def _resolve_pts(self, pts_base, pts_3rd, pricing, models, tier):
        """Resolve points for a unit given tier and pricing overrides.

        Args:
            pts_base: Base pts from config (1st unit).
            pts_3rd: pts for 3rd+ unit (None if same as base).
            pricing: Pricing data from merged JSON (list of tier dicts).
            models: Number of models in the unit.
            tier: '1st' (default) or '3rd'.

        Returns resolved points.
        """
        if tier == "3rd" and pts_3rd is not None:
            pts = pts_3rd
        else:
            pts = pts_base

        if pricing:
            # For 3rd tier: try to find [3,) range pricing entry
            target_range = "[3,)" if tier == "3rd" else None
            for pr in pricing:
                if target_range and pr.get("range") != target_range:
                    continue
                for cost in pr.get("costs", []):
                    if cost.get("models") == models:
                        pts = cost["points"]
                        break
                else:
                    continue
                break

        return pts

    def resolve_loadout(self, name, target, pricing=None, tier="1st", mode=None):
        """Resolve a unit's weapons for a given target.

        Args:
            name: Unit name.
            target: TargetProfile (or weighted list).
            pricing: Pricing data from merged JSON.
            tier: '1st' (default) or '3rd' (progressive pricing).
            mode: Restrict to a single named build/mode (None = best of all builds).

        Returns (points, ranged, melee, innate, info_dict) or None.
        """
        # Squad: optimise special weapons per target
        if name in self.config.squads:
            sdetail = self.config.squads[name]
            pts = self._resolve_pts(
                sdetail["pts"], sdetail.get("pts_3rd"),
                pricing, sdetail["n"], tier,
            )
            # Mode filter only applies when the squad actually has that build;
            # otherwise it's a no-op (full build list) for cross-unit filters.
            squad_mode = (
                mode
                if mode and "builds" in sdetail
                and any(b.get("name") == mode for b in sdetail["builds"])
                else None
            )
            ld = self._best_squad_variant(name, target, mode=squad_mode)
            squad_info = dict(sdetail.get("info", {}))
            if "builds" in sdetail:
                squad_info["_modes"] = [b.get("name") for b in sdetail["builds"]]
                squad_info["_multimodal"] = len(squad_info["_modes"]) > 1
            if ld and "_n_combos" in ld:
                squad_info["_n_combos"] = ld["_n_combos"]
            return (pts, ld["ranged"], ld["melee"], ld["innate"], squad_info)

        # Vehicle with weapon options (NDK / GMNDK / all vehicles)
        if name in self.config.weapon_options:
            wo = self.config.weapon_options[name]
            pts = self._resolve_pts(
                wo.get("pts", 0), wo.get("pts_3rd"),
                pricing, 1, tier,
            )
            info = wo.get("info", {})

            # Build-level resolution: BSData constraint-based builds
            # Each build has fixed_ranged, fixed_melee, ranged_choices, melee_choices,
            # max_ranged, max_melee (how many weapons can be picked from choice lists)
            if "builds" in wo:
                best_build = None
                best_d = -1
                n_combos = 0
                for build in wo["builds"]:
                    # Mode filter: skip non-matching builds only when the unit
                    # actually HAS the requested mode (no-op otherwise).
                    if mode and mode != build.get("name") and any(
                        b.get("name") == mode for b in wo["builds"]
                    ):
                        continue
                    # New format: untyped slots with typed choices
                    sb = self._resolve_slots_build(build, name, target)
                    if sb is not None:
                        b_ranged, b_melee, sb_n = sb
                        n_combos += sb_n
                        d = _ld_dmg(b_ranged, b_melee, [], target)
                        if d > best_d:
                            best_d = d
                            best_build = (b_ranged, b_melee)
                        continue
                    
                    b_ranged = [self.W(rn, unit_name=name)
                                for rn in build.get("fixed_ranged", [])]
                    b_melee = [self.W(mn, unit_name=name)
                               for mn in build.get("fixed_melee", [])]
                    # Handle ranged choices
                    ranged_choice_lists = build.get("ranged_choices", [])
                    if ranged_choice_lists:
                        import itertools
                        max_r = build.get("max_ranged")
                        if max_r and max_r < len(ranged_choice_lists):
                            all_options = list({opt for cl in ranged_choice_lists for opt in cl})
                            best_combo_d = -1
                            best_combo_ranged = None
                            for combo in itertools.combinations(all_options, max_r):
                                n_combos += 1
                                combo_ranged = list(b_ranged)
                                for choice_name in combo:
                                    combo_ranged.append(self.W(choice_name, unit_name=name))
                                combo_d = _ld_dmg(combo_ranged, b_melee, [], target)
                                if combo_d > best_combo_d:
                                    best_combo_d = combo_d
                                    best_combo_ranged = combo_ranged
                            b_ranged = best_combo_ranged
                        elif max_r and max_r >= len(ranged_choice_lists):
                            all_options = list({opt for cl in ranged_choice_lists for opt in cl})
                            best_combo_d = -1
                            best_combo_ranged = None
                            for combo in itertools.combinations(all_options, min(max_r, len(all_options))):
                                n_combos += 1
                                combo_ranged = list(b_ranged)
                                for choice_name in combo:
                                    combo_ranged.append(self.W(choice_name, unit_name=name))
                                combo_d = _ld_dmg(combo_ranged, b_melee, [], target)
                                if combo_d > best_combo_d:
                                    best_combo_d = combo_d
                                    best_combo_ranged = combo_ranged
                            b_ranged = best_combo_ranged
                        else:
                            choice_combos = itertools.product(*ranged_choice_lists)
                            best_combo_d = -1
                            best_combo_ranged = None
                            for combo in choice_combos:
                                n_combos += 1
                                combo_ranged = list(b_ranged)
                                for choice_list in combo:
                                    combo_ranged.append(self.W(choice_list, unit_name=name))
                                combo_d = _ld_dmg(combo_ranged, b_melee, [], target)
                                if combo_d > best_combo_d:
                                    best_combo_d = combo_d
                                    best_combo_ranged = combo_ranged
                            b_ranged = best_combo_ranged
                    # Handle melee choices
                    melee_choice_lists = build.get("melee_choices", [])
                    if melee_choice_lists:
                        import itertools
                        max_m = build.get("max_melee")
                        if max_m and max_m < len(melee_choice_lists):
                            all_options = list({opt for cl in melee_choice_lists for opt in cl})
                            best_combo_d = -1
                            best_combo_melee = None
                            for combo in itertools.combinations(all_options, max_m):
                                n_combos += 1
                                combo_melee = list(b_melee)
                                for choice_name in combo:
                                    combo_melee.append(self.W(choice_name, unit_name=name))
                                combo_d = _ld_dmg(b_ranged, combo_melee, [], target)
                                if combo_d > best_combo_d:
                                    best_combo_d = combo_d
                                    best_combo_melee = combo_melee
                            b_melee = best_combo_melee
                        elif max_m and max_m >= len(melee_choice_lists):
                            all_options = list({opt for cl in melee_choice_lists for opt in cl})
                            best_combo_d = -1
                            best_combo_melee = None
                            for combo in itertools.combinations(all_options, min(max_m, len(all_options))):
                                n_combos += 1
                                combo_melee = list(b_melee)
                                for choice_name in combo:
                                    combo_melee.append(self.W(choice_name, unit_name=name))
                                combo_d = _ld_dmg(b_ranged, combo_melee, [], target)
                                if combo_d > best_combo_d:
                                    best_combo_d = combo_d
                                    best_combo_melee = combo_melee
                            b_melee = best_combo_melee
                        else:
                            choice_combos = itertools.product(*melee_choice_lists)
                            best_combo_d = -1
                            best_combo_melee = None
                            for combo in choice_combos:
                                n_combos += 1
                                combo_melee = list(b_melee)
                                for choice_list in combo:
                                    combo_melee.append(self.W(choice_list, unit_name=name))
                                combo_d = _ld_dmg(b_ranged, combo_melee, [], target)
                                if combo_d > best_combo_d:
                                    best_combo_d = combo_d
                                    best_combo_melee = combo_melee
                            b_melee = best_combo_melee

                    d = _ld_dmg(b_ranged, b_melee, [], target)
                    if d > best_d:
                        best_d = d
                        best_build = (b_ranged, b_melee)

                if best_build:
                    info["_n_combos"] = n_combos
                    info["_modes"] = [b.get("name") for b in wo["builds"]]
                    info["_multimodal"] = len(wo["builds"]) > 1
                    return (pts, best_build[0], best_build[1], [], info)

            # The flat ranged/melee fallback (legacy _best_vehicle_variant)
            # was removed — every weapon_options entry fleet-wide now uses
            # the builds format (locked by TestNoFlatWeaponOptions). A flat
            # re-add is a config regression: fail loudly instead of silently
            # resolving via the removed legacy path.
            raise ValueError(
                f"{name}: weapon_options entry has no 'builds'. Flat "
                f"ranged/melee format was removed; convert to builds "
                f"(see docs/changes/army-config-refresh-playbook.md)."
            )

        # Character: fixed loadout (with optional weapon choice)
        if name in self.config.characters:
            ch = self.config.characters[name]
            pts = self._resolve_pts(
                ch["pts"], ch.get("pts_3rd"),
                pricing, 1, tier,
            )

            # Build-level resolution: BSData constraint-based builds
            # Each build has ranged, melee (fixed), ranged_choices, melee_choices,
            # max_ranged, max_melee (how many weapons can be picked from choice lists)
            if "weapon_options" in ch and "builds" in ch.get("weapon_options", {}):
                import itertools as _itertools_ch
                best_build = None
                best_d = -1
                n_combos = 0
                for build in ch["weapon_options"]["builds"]:
                    # Mode filter: skip non-matching builds only when the unit
                    # actually HAS the requested mode (no-op otherwise).
                    if mode and mode != build.get("name") and any(
                        b.get("name") == mode for b in ch["weapon_options"]["builds"]
                    ):
                        continue
                    # New format: untyped slots with typed choices
                    sb = self._resolve_slots_build(build, name, target)
                    if sb is not None:
                        b_ranged, b_melee, sb_n = sb
                        n_combos += sb_n
                        d = _ld_dmg(b_ranged, b_melee, [], target)
                        if d > best_d:
                            best_d = d
                            best_build = (b_ranged, b_melee)
                        continue
                    
                    b_ranged = [self.W(rn, unit_name=name)
                                for rn in build.get("ranged", [])]
                    b_melee = [self.W(mn, unit_name=name)
                               for mn in build.get("melee", [])]
                    # Handle ranged choices within build
                    ranged_choice_lists = build.get("ranged_choices", [])
                    if ranged_choice_lists:
                        max_r = build.get("max_ranged")
                        if max_r and max_r < len(ranged_choice_lists):
                            all_options = list({opt for cl in ranged_choice_lists for opt in cl})
                            best_combo_d = -1
                            best_combo_ranged = None
                            for combo in _itertools_ch.combinations(all_options, max_r):
                                n_combos += 1
                                combo_ranged = list(b_ranged)
                                for choice_name in combo:
                                    combo_ranged.append(self.W(choice_name, unit_name=name))
                                combo_d = _ld_dmg(combo_ranged, b_melee, [], target)
                                if combo_d > best_combo_d:
                                    best_combo_d = combo_d
                                    best_combo_ranged = combo_ranged
                            b_ranged = best_combo_ranged
                        elif max_r and max_r >= len(ranged_choice_lists):
                            all_options = list({opt for cl in ranged_choice_lists for opt in cl})
                            best_combo_d = -1
                            best_combo_ranged = None
                            for combo in _itertools_ch.combinations(all_options, min(max_r, len(all_options))):
                                n_combos += 1
                                combo_ranged = list(b_ranged)
                                for choice_name in combo:
                                    combo_ranged.append(self.W(choice_name, unit_name=name))
                                combo_d = _ld_dmg(combo_ranged, b_melee, [], target)
                                if combo_d > best_combo_d:
                                    best_combo_d = combo_d
                                    best_combo_ranged = combo_ranged
                            b_ranged = best_combo_ranged
                        else:
                            choice_combos = _itertools_ch.product(*ranged_choice_lists)
                            best_combo_d = -1
                            best_combo_ranged = None
                            for combo in choice_combos:
                                n_combos += 1
                                combo_ranged = list(b_ranged)
                                for choice_list in combo:
                                    combo_ranged.append(self.W(choice_list, unit_name=name))
                                combo_d = _ld_dmg(combo_ranged, b_melee, [], target)
                                if combo_d > best_combo_d:
                                    best_combo_d = combo_d
                                    best_combo_ranged = combo_ranged
                            b_ranged = best_combo_ranged
                    # Handle melee choices within build
                    melee_choice_lists = build.get("melee_choices", [])
                    if melee_choice_lists:
                        max_m = build.get("max_melee")
                        if max_m and max_m < len(melee_choice_lists):
                            all_options = list({opt for cl in melee_choice_lists for opt in cl})
                            best_combo_d = -1
                            best_combo_melee = None
                            for combo in _itertools_ch.combinations(all_options, max_m):
                                n_combos += 1
                                combo_melee = list(b_melee)
                                for choice_name in combo:
                                    combo_melee.append(self.W(choice_name, unit_name=name))
                                combo_d = _ld_dmg(b_ranged, combo_melee, [], target)
                                if combo_d > best_combo_d:
                                    best_combo_d = combo_d
                                    best_combo_melee = combo_melee
                            b_melee = best_combo_melee
                        elif max_m and max_m >= len(melee_choice_lists):
                            all_options = list({opt for cl in melee_choice_lists for opt in cl})
                            best_combo_d = -1
                            best_combo_melee = None
                            for combo in _itertools_ch.combinations(all_options, min(max_m, len(all_options))):
                                n_combos += 1
                                combo_melee = list(b_melee)
                                for choice_name in combo:
                                    combo_melee.append(self.W(choice_name, unit_name=name))
                                combo_d = _ld_dmg(b_ranged, combo_melee, [], target)
                                if combo_d > best_combo_d:
                                    best_combo_d = combo_d
                                    best_combo_melee = combo_melee
                            b_melee = best_combo_melee
                        else:
                            choice_combos = _itertools_ch.product(*melee_choice_lists)
                            best_combo_d = -1
                            best_combo_melee = None
                            for combo in choice_combos:
                                n_combos += 1
                                combo_melee = list(b_melee)
                                for choice_list in combo:
                                    combo_melee.append(self.W(choice_list, unit_name=name))
                                combo_d = _ld_dmg(b_ranged, combo_melee, [], target)
                                if combo_d > best_combo_d:
                                    best_combo_d = combo_d
                                    best_combo_melee = combo_melee
                            b_melee = best_combo_melee

                    d = _ld_dmg(b_ranged, b_melee, [], target)
                    if d > best_d:
                        best_d = d
                        best_build = (b_ranged, b_melee)

                if best_build:
                    ch_info = dict(ch.get("info", {}))
                    ch_info["_n_combos"] = n_combos
                    ch_info["_modes"] = [b.get("name") for b in ch["weapon_options"]["builds"]]
                    ch_info["_multimodal"] = len(ch["weapon_options"]["builds"]) > 1
                    return (pts, best_build[0], best_build[1], [], ch_info)

            # Per-slot weapon_options (existing fallback for non-build configs)
            ranged = [self.W(rn, unit_name=name) for rn in ch["ranged"]]
            # Witchfire dedup: when both "X - witchfire" and "X - focused witchfire"
            # exist, keep only the focused profile (always better).
            has_focused = any("focused witchfire" in w.name.lower() for w in ranged)
            if has_focused:
                ranged = [w for w in ranged
                         if "witchfire" not in w.name.lower()
                         or "focused witchfire" in w.name.lower()]
            melee = [self.W(mn, unit_name=name) for mn in ch["melee"]]
            innate = [self.W(inn, unit_name=name) for inn in ch.get("innate", [])]
            n_combos = 0
            # Weapon options: pick best variant vs target
            if "weapon_options" in ch:
                opts = ch["weapon_options"]
                if "ranged" in opts:
                    n_combos = len(opts["ranged"])
                    best_rng = max(
                        ([self.W(rn, unit_name=name) for rn in opt] for opt in opts["ranged"]),
                        key=lambda ws: _ld_dmg(ws, melee, innate, target),
                    )
                    ranged = best_rng
                if "melee" in opts:
                    n_combos = n_combos or 1
                    n_combos *= len(opts["melee"])
                    best_ml = max(
                        ([self.W(mn, unit_name=name) for mn in opt] for opt in opts["melee"]),
                        key=lambda ws: _ld_dmg(ranged, ws, innate, target),
                    )
                    melee = best_ml
            ch_info = dict(ch.get("info", {}))
            if n_combos > 1:
                ch_info["_n_combos"] = n_combos
            return (pts, ranged, melee, innate, ch_info)

        # Fixed vehicle loadout — or weapon_slots based
        if name in self.config.vehicles:
            vh = self.config.vehicles[name]
            if "weapon_slots" in vh:
                return self._resolve_slots(name, vh, target, pricing, tier)
            pts = self._resolve_pts(
                vh["pts"], vh.get("pts_3rd"),
                pricing, 1, tier,
            )
            ranged = [self.W(w["name"], unit_name=w.get("unit_name", name))
                      for w in vh.get("ranged", [])]
            melee = [self.W(w["name"], unit_name=w.get("unit_name", name))
                     for w in vh.get("melee", [])]
            innate = [self.W(w["name"], unit_name=w.get("unit_name", name))
                      for w in vh.get("innate", [])]
            return (pts, ranged, melee, innate, vh.get("info"))

        return None

    # ── Weapon slot resolution ───────────────────────────────────────

    def _resolve_slots(self, name, vh, target, pricing, tier):
        """Resolve a vehicle's loadout from weapon_slots — finds best combo vs target."""
        # Slot-based units: pts is chassis base, don't override with MFM (which quotes full price)
        base_pts = self._resolve_pts(
            vh["pts"], vh.get("pts_3rd"),
            None, 1, tier,
        )
        fixed_ranged = [self.W(wn, unit_name=name)
                        for wn in vh.get("fixed_ranged", [])]
        fixed_melee = [self.W(wn, unit_name=name)
                       for wn in vh.get("fixed_melee", [])]
        fixed_innate = [self.W(wn, unit_name=name)
                        for wn in vh.get("fixed_innate", [])]

        slots = vh["weapon_slots"]
        import itertools

        best_ranged, best_melee = list(fixed_ranged), list(fixed_melee)
        best_d, best_pts = -1, base_pts
        n_combos = 0

        # Build lists of choices per slot
        slot_choices = []
        for slot in slots:
            choose = slot.get("choose", 1)
            entries = slot["from"]
            # Each entry is { "weapon": "name" } or { "weapons": ["n1", "n2"] }
            # combinations_with_replacement with length = choose
            slot_choices.append(list(itertools.combinations_with_replacement(
                range(len(entries)), choose
            )))

        # Iterate all slot combinations
        for combo in itertools.product(*slot_choices):
            n_combos += 1
            slot_pts = base_pts
            slot_ranged = list(fixed_ranged)
            slot_melee = list(fixed_melee)
            slot_innate = list(fixed_innate)
            skip_combo = False

            for slot_idx, choice_indices in enumerate(combo):
                entries = slots[slot_idx]["from"]
                max_dup = slots[slot_idx].get("max_duplicates", slots[slot_idx].get("choose", 1))
                # Check max_duplicates constraint
                from collections import Counter
                idx_counts = Counter(choice_indices)
                if any(c > max_dup for c in idx_counts.values()):
                    skip_combo = True
                    break
                for entry_idx in choice_indices:
                    entry = entries[entry_idx]
                    slot_pts += entry.get("pts", 0)
                    if "weapon" in entry:
                        wp = self.W(entry["weapon"], unit_name=name)
                        wp._slot_pts = entry.get("pts", 0)  # annotate
                        slot_ranged.append(wp)
                    if "weapons" in entry:
                        for wn in entry["weapons"]:
                            wp = self.W(wn, unit_name=name)
                            wp._slot_pts = entry.get("pts", 0)
                            slot_ranged.append(wp)
                    if "melee_weapon" in entry:
                        wp = self.W(entry["melee_weapon"], unit_name=name)
                        wp._slot_pts = entry.get("pts", 0)
                        slot_melee.append(wp)
                    if "melee_weapons" in entry:
                        for wn in entry["melee_weapons"]:
                            wp = self.W(wn, unit_name=name)
                            wp._slot_pts = entry.get("pts", 0)
                            slot_melee.append(wp)

            if skip_combo:
                continue
            d = _ld_dmg(slot_ranged, slot_melee, slot_innate, target)
            if d > best_d:
                best_d = d
                best_ranged = slot_ranged
                best_melee = slot_melee
                best_pts = slot_pts

        slot_info = dict(vh.get("info", {}))
        slot_info["_n_combos"] = n_combos
        return (best_pts, best_ranged, best_melee, fixed_innate, slot_info)

    def _resolve_slots_build(self, build: dict, name: str, target) -> tuple | None:
        """Resolve a build using 'slots' format.
        
        New format: untyped slots (each slot is independent), typed choices
        (each weapon has its own 'ranged'/'melee' type). No cross-slot
        constraints — you pick 1 from each slot, period.
        
        Returns (ranged_list, melee_list) or None if build lacks slots format.

        Supports build-level "no_duplicates": true — enforces "cannot take
        duplicates" across slots (e.g. 2× Sublimator is invalid). Combos with
        a repeated weapon name are skipped and not counted in n_combos.
        """
        slots = build.get("slots")
        if slots is None:
            return None
        
        import itertools
        
        no_duplicates = build.get("no_duplicates", False)
        
        # Fixed weapons sorted by type (skip unresolvable)
        fixed_items = build.get("fixed", [])
        b_ranged = []
        b_melee = []
        for f in fixed_items:
            try:
                w = self.W(f["name"], unit_name=name)
            except KeyError:
                continue
            if f.get("type") == "melee":
                b_melee.append(w)
            else:
                b_ranged.append(w)
        
        slot_choice_lists = [s["choices"] for s in slots]
        
        if not slot_choice_lists:
            return (b_ranged, b_melee, 0)
        
        best_d = -1
        best_ranged = None
        best_melee = None
        n_combos = 0
        
        for combo in itertools.product(*slot_choice_lists):
            if no_duplicates:
                combo_names = [c["name"] for c in combo]
                if len(set(combo_names)) != len(combo_names):
                    continue  # duplicate weapon picked in 2+ slots — invalid
            n_combos += 1
            combo_ranged = list(b_ranged)
            combo_melee = list(b_melee)
            skip_combo = False
            for choice in combo:
                try:
                    profile = self.W(choice["name"], unit_name=name)
                except KeyError:
                    skip_combo = True
                    break
                # Choice may carry a count multiplier (e.g. '2 Starcannons' →
                # Starcannon ×2). Append the profile once per count so
                # multi-weapon options keep their multiplicity.
                count = choice.get("count", 1) or 1
                for _ in range(count):
                    if choice.get("type") == "melee":
                        combo_melee.append(profile)
                    else:
                        combo_ranged.append(profile)
            if skip_combo:
                continue
            
            d = _ld_dmg(combo_ranged, combo_melee, [], target)
            if d > best_d:
                best_d = d
                best_ranged = combo_ranged
                best_melee = combo_melee
        
        if best_ranged is not None:
            return (best_ranged, best_melee, n_combos)
        return (b_ranged, b_melee, n_combos)

    # ── Unit info ────────────────────────────────────────────────────

    def get_unit_info(self, name, profile_data):
        """Return (keywords, toughness, save, wounds, oc, invuln) from config + profile."""
        def _safe_int(val, default=0):
            s = str(val).replace('"', '').replace('+', '').replace('*', '').strip()
            digits = ''.join(c for c in s if c.isdigit() or c == '-')
            return int(digits) if digits else default

        # Squad info
        if name in self.config.squads:
            info = self.config.squads[name]["info"]
            if not info.get("T"):
                pass  # fall through to profile-based fallback
            else:
                kw = ["INFANTRY"]
                kw.extend(self.config.faction_keywords)
                if info.get("deep_strike"):
                    kw.append("DEEP STRIKE")
                if info.get("FLY"):
                    kw.append("FLY")
                if "Terminator" in name:
                    kw.append("TERMINATOR")
                return kw, info["T"], info["SV"], _safe_int(info["W"], 2), info.get("OC", 0), info.get("invuln") or info.get("INV")

        # Vehicle info — weapon_options.json is authoritative (matches
        # resolve_loadout precedence); vehicles.json is only a fallback for
        # units WITHOUT weapon-option builds. Both share the same keyword
        # logic so a shadowed stale vehicles.json entry can never override
        # the curated weapon_options data.
        veh_info = None
        for src in (self.config.weapon_options, self.config.vehicles):
            if name in src:
                veh_info = src[name].get("info", {})
                if veh_info.get("T"):
                    break
        if veh_info and veh_info.get("T"):
            kw = ["VEHICLE"]
            kw.extend(self.config.faction_keywords)
            if "DREADNOUGHT" in name.upper():
                kw.append("DREADNOUGHT")
            if veh_info.get("deep_strike"):
                kw.append("DEEP STRIKE")
            # WALKER keyword is sourced from authoritative merged profile keywords
            # (merged at line ~1436 via profile_kw merge). Do NOT infer WALKER from
            # INV presence — that tags any shielded vehicle (Foetid Bloat-Drone,
            # Plagueburst Crawler) as a walker. Real walkers (Helbrute, Defiler,
            # Dreadnoughts) carry "Walker" in merged profile.keywords.
            return kw, veh_info["T"], veh_info["SV"], _safe_int(veh_info["W"], 2), veh_info.get("OC", 0), veh_info.get("invuln") or veh_info.get("INV")

        # Character info
        if name in self.config.characters:
            ch = self.config.characters[name]
            info = ch.get("info", {})
            if not info.get("T"):
                pass  # fall through to profile-based fallback
            else:
                t_val = info.get("T", 4)
                kw = ["INFANTRY", "CHARACTER"]
                if info.get("deep_strike"):
                    kw.append("DEEP STRIKE")
                kw.extend(self.config.faction_keywords)
                if t_val >= 5:
                    kw.append("TERMINATOR")
                return kw, info["T"], info["SV"], _safe_int(info["W"], 2), info.get("OC", 0), info.get("invuln") or info.get("INV")

        # Fallback: from profile data
        stats = profile_data.get("stats", {})
        if stats.get("T"):
            def _safe_int(val, default=0):
                """Extract leading integer from a stat value. Returns default if unparseable."""
                s = str(val).replace('"', '').replace('+', '').replace('*', '').strip()
                digits = ''.join(c for c in s if c.isdigit() or c == '-')
                return int(digits) if digits else default
            t_val = _safe_int(stats.get("T", "4"), 4)
            sv_val = _safe_int(stats.get("Sv", stats.get("SV", "3+")), 3)
            w_val = _safe_int(stats.get("W", "2"), 2)
            oc_val = _safe_int(stats.get("OC", "1"), 1)
            raw_kw = [k.upper() for k in profile_data.get("keywords", [])]
            kw = []
            for k in ("INFANTRY", "VEHICLE", "WALKER", "CHARACTER", "FLY"):
                if k in raw_kw:
                    kw.append(k)
            kw.extend(self.config.faction_keywords)
            inv = None
            for rule in profile_data.get("rules", []):
                if "INVULNERABLE" in rule.upper():
                    m = re.search(r'(\d+)\+', rule)
                    if m:
                        inv = int(m.group(1))
            return kw, t_val, sv_val, w_val, oc_val, inv

        return [], 4, 3, 2, 1, None

    # ── Ranking computation ──────────────────────────────────────────

    def compute_ranking(self, target=None, mission=None, meta_name=None, tier="1st",
                         detachment: Optional[str] = None,
                         detachment_choice: Optional[int] = None,
                         detachments: Optional[list[tuple[str, int]]] = None,
                         disposition: Optional[str] = None,
                         melta_active: bool = False,
                         heavy_stationary: bool = False,
                         plunging: bool = True,
                         mode: Optional[str] = None,
                         max_points: Optional[int] = 2000):
        """Compute unit ranking for a given target, optionally weighted by mission or tier.

        Args:
            target: TargetProfile (or weighted list). Ignored if meta_name set.
            mission: Mission profile name.
            meta_name: Meta profile name — loadouts optimised for weighted mix.
            tier: Pricing tier — '1st' (default) or '3rd' (3rd+ unit pricing).
            detachment: Single detachment name (backward compat).
            detachment_choice: Index of the modifier choice (backward compat).
            detachments: List of (detachment_name, choice_index) for multi-detachment.
                        Overrides detachment/detachment_choice if set.
            disposition: Mission disposition ID — validates at least one detachment is playable.
            melta_active: assume ≤ half range for Melta bonus.
            heavy_stationary: assume the unit remained stationary for Heavy bonus.
            plunging: auto-apply Plunging Fire (+1 BS) for TOWERING units (default True).
            mode: Restrict to a single named build/mode (None = best of all builds).

        Returns:
            list of result dicts sorted by mission score (or DPP).
        """
        target = target or self.config.target_profiles.get("MEQ")

        # ── Resolve detachment modifiers (single or multi) ────────────
        detachment_pairs: list[tuple[DetachmentModifier, WeaponModifier]] = []

        if detachments is not None:
            # Multi-detachment mode
            for det_name, choice_idx in detachments:
                choices = self.get_detachment_modifiers(det_name)
                if 0 <= choice_idx < len(choices):
                    mod = choices[choice_idx]
                    detachment_pairs.append((mod, mod.to_weapon_modifier()))
            # Validate disposition against at least one detachment
            if disposition and self.config.dispositions:
                any_valid = any(
                    self.config.can_detachment_play_disposition(d, disposition)
                    for d, _ in detachments
                )
                if not any_valid:
                    valid = self.config.get_detachments_for_disposition(disposition)
                    raise ValueError(
                        f"None of the selected detachments can be used in '{disposition}' mission. "
                        f"Valid detachments: {valid}"
                    )
        elif detachment:
            # Single detachment mode (backward compat)
            if disposition and self.config.dispositions:
                if not self.config.can_detachment_play_disposition(detachment, disposition):
                    valid = self.config.get_detachments_for_disposition(disposition)
                    raise ValueError(
                        f"Detachment '{detachment}' cannot be used in '{disposition}' mission. "
                        f"Valid detachments: {valid}"
                    )
            choices = self.get_detachment_modifiers(detachment)
            if choices:
                choice_idx = detachment_choice if detachment_choice is not None else 0
                if 0 <= choice_idx < len(choices):
                    mod = choices[choice_idx]
                    detachment_pairs.append((mod, mod.to_weapon_modifier()))

        def _modifier_applies(mod: Optional[DetachmentModifier], unit_name: str, unit_kw: list[str]) -> bool:
            """Check if a detachment modifier applies to a given unit.

            Matches unit_filter against both unit name and keywords.
            """
            if mod is None:
                return False
            if not mod.unit_filter:
                return True  # no filter = applies to all
            upper_name = unit_name.upper()
            upper_kw = [k.upper() for k in unit_kw]
            return any(
                f.upper() in upper_name or f.upper() in upper_kw
                for f in mod.unit_filter
            )

        # Resolve meta
        meta_targets = None
        actual_target = target
        melee_penalty = 1.0
        if meta_name:
            mp_spec = self.config.meta_profiles.get(meta_name, [])
            if isinstance(mp_spec, dict):
                melee_penalty = mp_spec.get("melee_penalty", 1.0)
            meta_targets = self.config._resolve_meta(meta_name)
            actual_target = meta_targets

        results = []
        for unit in self.data["units"]:
            name = unit["name"]
            profile = unit.get("profile")
            if profile is None:
                profile = {}

            # Skip units not in our config (fast path)
            if name not in self.config.known_units:
                continue

            # Skip Legends units (unavailable in regular play)
            if self.config.is_legends(name):
                continue

            # Faction keyword filter — only rank units whose Faction keyword
            # matches this faction's keywords. Prevents ranking cross-faction
            # BSData imports (e.g. Guilliman in DA, GK Termies in AM).
            # Units with NO Faction keyword are allowed (generic units like Drop Pod).
            def _norm_kw(s):
                return s.upper().replace("\u2019", "'").replace("\u2018", "'")
            fk_upper = [_norm_kw(fk) for fk in self.config.faction_keywords]
            # Only check Faction: prefixed keywords, not all keywords
            unit_fks = [_norm_kw(k) for k in profile.get("keywords", [])
                        if _norm_kw(k).startswith("FACTION:")]
            if profile and unit_fks and not any(fk in unit_fks for fk in fk_upper):
                continue

            # Unit info (needed before modifier check for keyword-based filters)
            kw_list, t_val, sv_val, w_val, oc_val, inv_val = self.get_unit_info(name, profile)

            # Merge profile keywords (e.g. TOWERING) not present in config-derived kw_list
            profile_kw = [k.upper() for k in profile.get("keywords", [])]
            for pk in profile_kw:
                if pk not in kw_list:
                    kw_list.append(pk)

            pricing = unit.get("pricing", [])
            stats = profile.get("stats", {})

            resolved = self.resolve_loadout(name, actual_target, pricing, tier=tier, mode=mode)
            if resolved is None:
                continue
            pts, ranged_profiles, melee_profiles, innate_profiles, info = resolved

            # Auto-detect datasheet abilities that grant re-rolls vs MONSTER/VEHICLE
            # (Surge of Wrath, Assured Destruction, Bring it Down! etc). The reroll
            # applies per-target, so damage is computed conditionally via
            # _ld_dmg_conditional. No hand-authored config entries for these.
            reroll_spec = None
            try:
                from engine.reroll_detect import detect_reroll_ability
                for ab in profile.get("abilities", []) or []:
                    spec = detect_reroll_ability(ab)
                    if spec is not None:
                        reroll_spec = spec
                        break
            except Exception:
                reroll_spec = None

            # Skip units exceeding max game size (e.g. 2100pt Titan in 2000pt game)
            if max_points and pts > max_points:
                continue

            # Auto-apply Plunging Fire (+1 BS) for TOWERING units [11e core rules]
            # TOWERING units are always considered elevated vs ground targets.
            # Psychic weapons will ignore this per [24.29] in compute_weapon_dpp.
            unit_hit_mode = HitMode.NORMAL
            if plunging and "TOWERING" in profile_kw:
                unit_hit_mode = HitMode.PLUNGING_FIRE

            # Apply save bonus from wargear (Brute Shield, Relic Shield, etc.)
            if info and info.get("save_bonus"):
                sv_val = max(2, sv_val - info["save_bonus"])

            # Per-unit multi-detachment modifier merge
            # Collect applicable modifiers from all selected detachments
            applicable_dms = [dm for dm, _ in detachment_pairs if _modifier_applies(dm, name, kw_list)]
            applicable_wms = [wm for dm, wm in detachment_pairs if _modifier_applies(dm, name, kw_list)]

            if applicable_wms:
                unit_weapon_mod = merge_weapon_modifiers(applicable_wms)
            else:
                unit_weapon_mod = None

            merged_surv = merge_detachment_modifiers(applicable_dms) if applicable_dms else None
            merged_mob = merge_detachment_modifiers(applicable_dms) if applicable_dms else None

            # SURV modifier: only applies if at least one has `affects == "surv"`
            unit_surv_mod = merged_surv if (merged_surv and any(dm.affects == "surv" for dm in applicable_dms)) else None
            # MOB modifier: only applies if at least one has `affects == "mob"`
            unit_mob_mod = merged_mob if (merged_mob and any(dm.affects == "mob" for dm in applicable_dms)) else None

            n_models = 1
            if name in self.config.squads:
                n_models = self.config.squads[name]["n"]

            # DPP (with optional detachment modifier)
            if reroll_spec is not None:
                dmg_ranged = _ld_dmg_conditional(ranged_profiles, [], [], actual_target, unit_weapon_mod,
                                                 reroll_spec, "ranged",
                                                 melta_active=melta_active, heavy_stationary=heavy_stationary,
                                                 hit_mode=unit_hit_mode, n_models=n_models) if ranged_profiles else 0
                dmg_melee = _ld_dmg_conditional([], melee_profiles, [], actual_target, unit_weapon_mod,
                                                reroll_spec, "melee",
                                                melta_active=melta_active, heavy_stationary=heavy_stationary,
                                                hit_mode=HitMode.NORMAL, n_models=n_models) if melee_profiles else 0
                dmg_innate = _ld_dmg_conditional([], [], innate_profiles, actual_target, unit_weapon_mod,
                                                 reroll_spec, "both",
                                                 melta_active=melta_active, heavy_stationary=heavy_stationary,
                                                 hit_mode=HitMode.NORMAL, n_models=n_models) if innate_profiles else 0
            else:
                dmg_ranged = _ld_dmg(ranged_profiles, [], [], actual_target, unit_weapon_mod,
                                     melta_active=melta_active, heavy_stationary=heavy_stationary,
                                     hit_mode=unit_hit_mode, n_models=n_models) if ranged_profiles else 0
                dmg_melee = _ld_dmg([], melee_profiles, [], actual_target, unit_weapon_mod,
                                    melta_active=melta_active, heavy_stationary=heavy_stationary,
                                    hit_mode=HitMode.NORMAL, n_models=n_models) if melee_profiles else 0
                dmg_innate = _ld_dmg([], [], innate_profiles, actual_target, unit_weapon_mod,
                                     melta_active=melta_active, heavy_stationary=heavy_stationary,
                                     hit_mode=HitMode.NORMAL, n_models=n_models) if innate_profiles else 0
            total_dmg = dmg_ranged + (dmg_melee * melee_penalty) + dmg_innate
            dpp_val = total_dmg / pts if pts > 0 else 0

            # Ignore Cover aura — units that grant Ignore Cover to allies
            # Boost reflects value to army beyond own damage (covers common in competitive)
            # Hammerstrike-type: strip cover from enemies after shooting
            # Aura-type: grant ignore cover to nearby units (Tor Garadon, Styrix, etc.)
            if info and info.get("ignore_cover_aura"):
                dpp_val *= 1.15  # +15% for granting army-wide cover ignore

            is_infantry = "INFANTRY" in kw_list

            # SURV (with optional detachment modifier)
            # Note: unit_surv_mod is already gated on original DM having affects=="surv" above
            if unit_surv_mod:
                final_invuln = inv_val or unit_surv_mod.invulnerable_save
                final_fnp = unit_surv_mod.feel_no_pain
            else:
                final_invuln = inv_val
                # FNP only if the unit/config explicitly has it — NOT a default for infantry
                final_fnp = info.get("fnp", info.get("FNP", info.get("feel_no_pain", None))) if info else None

            # Conditional FNP (e.g. vs Psychic) — informational only, NOT in SURV scoring
            cond_fnp = info.get("conditional_fnp", None) if info else None
            cond_fnp_type = info.get("conditional_fnp_type", None) if info else None

            defense = UnitDefense(
                toughness=t_val,
                wounds_per_model=w_val,
                save=sv_val,
                invuln=final_invuln,
                fnp=final_fnp,
                models=n_models,
                damage_reduction=info.get("damage_reduction", 0) if info else 0,
            )
            surv = compute_surv(defense, pts)

            # MOB (with optional detachment modifier)
            m_val = 6
            if info:
                m_m = re.search(r'(\d+)', str(info.get("M", '6"')))
                if m_m:
                    m_val = int(m_m.group(1))
                if info.get("FLY"):
                    kw_list.append("FLY")
            else:
                m_str = stats.get("M", '6"')
                m_m = re.search(r'(\d+)', str(m_str))
                if m_m:
                    m_val = int(m_m.group(1))

            # Apply movement bonus from detachment
            # Note: unit_mob_mod is already gated on original DM having affects=="mob" above
            if unit_mob_mod:
                m_val += unit_mob_mod.movement_bonus

            has_fly = "FLY" in kw_list
            has_deep_strike = "DEEP STRIKE" in kw_list
            for rule in profile.get("rules", []):
                if "DEEP STRIKE" in rule.upper():
                    has_deep_strike = True

            has_gate = False  # Gate of Infinity is GK-specific, not default for infantry

            # Detect terrain traversal abilities (Titanic Strides, Scuttling Walker, etc.)
            has_terrain = _has_terrain_ability(profile)

            mob = compute_mob(
                movement=m_val,
                fly=has_fly,
                deep_strike=has_deep_strike,
                oc=oc_val,
                keywords=kw_list,
                gate_of_infinity=has_gate,
                no_t1_reinforcements=self.no_t1_reinforcements,
                has_terrain_ability=has_terrain,
            )

            notes = self.config.notes.get(name, "")

            # OC boost from banner/Astartes Banner wargear (+1 OC per model to attached unit)
            oc_boost_val = info.get("oc_boost", 0) if info else 0

            n_combos = info.get("_n_combos", 0) if info else 0
            ld = self._loadout_desc(ranged_profiles, melee_profiles, innate_profiles)
            if n_combos > 1:
                ld += f" [best of {n_combos} combos]"
            result_entry = {
                "name": name,
                "points": pts,
                "dpp": round(dpp_val, 4),
                "total_damage": round(total_dmg, 2),
                "surv": surv,
                "mob": mob,
                "ranged": ranged_profiles,
                "melee": melee_profiles,
                "innate": innate_profiles,
                "loadout_desc": ld,
                "n_combos": n_combos,
                "modes": info.get("_modes") if info else None,
                "multimodal": bool(info.get("_multimodal")) if info else False,
                "notes": notes,
                "conditional_fnp": cond_fnp,
                "conditional_fnp_type": cond_fnp_type,
                "oc_boost": oc_boost_val,
            }
            if meta_name:
                result_entry["_meta_name"] = meta_name
            results.append(result_entry)

        # Score/sort
        if mission and mission in self.config.mission_profiles:
            w = self.config.mission_profiles[mission]
            dps_vals = [r["dpp"] for r in results]
            # Surv turns: toughness-bracketed benchmark (fair per unit type)
            SURV_SHOTS_PER_TURN = 5
            surv_vals = []
            for r in results:
                raw_turns = r["surv"]["primary_shots"] / SURV_SHOTS_PER_TURN
                surv_vals.append(raw_turns)
            # OBJ: (OC + banner_boost) × models × min(wpm, 3) × survival_turns
            # wounds_per_model: W1 models lose OC 1:1 with wounds, W2 lose 1:2, etc.
            # Capped at 3 — prevents high-W vehicles (W10+) from dominating OBJ.
            # Visibility-adjusted: bigger units can't hide → fewer effective turns on objective
            obj_vals = []
            for r in results:
                vis = self._surv_visibility_multiplier(r["mob"])
                st = r["surv"]["primary_shots"] * vis / SURV_SHOTS_PER_TURN
                base_oc = r["mob"].get("objective_control", 0)
                boost = r.get("oc_boost", 0)
                models = r["surv"].get("models", 1)
                wpm = min(r["surv"].get("wounds_per_model", 1), 3)
                total_oc = (base_oc + boost) * models * wpm
                obj_vals.append(self.obj_score(total_oc, st))
            n = len(results)

            def _pct(val, series):
                if n <= 1:
                    return 100
                below = sum(1 for x in series if x < val)
                same = sum(1 for x in series if x == val)
                return round((below + 0.5 * (same - 1)) / (n - 1) * 100)

            for r in results:
                r["_dps_pct"] = _pct(r["dpp"], dps_vals)
                raw_turns = r["surv"]["primary_shots"] / SURV_SHOTS_PER_TURN
                r["_surv_turns"] = round(raw_turns, 1)
                r["_surv_pct"] = _pct(raw_turns, surv_vals)
                # Cost penalty: linear from 50pts (0%) to 2000pts (100%)
                # Below 50pts: no penalty (cheap units are efficient)
                # At 450pts: ~80% (Baneblade gets moderate penalty)
                # Applied only to SURV contribution, not the entire score.
                pts = r["points"] if r["points"] > 0 else 1
                if pts <= 50:
                    cost_eff = 100.0
                else:
                    cost_eff = max(0.0, 100.0 * (1.0 - (pts - 50) / 1950.0))
                r["_cost_eff"] = round(cost_eff, 1)
                # MOB: absolute score (0-100), NOT percentile — same baseline across all factions
                r["_mob_pct"] = self.mob_score(r["mob"])
                base_oc = r["mob"].get("objective_control", 0)
                boost = r.get("oc_boost", 0)
                models = r["surv"].get("models", 1)
                wpm = r["surv"].get("wounds_per_model", 1)
                total_oc = (base_oc + boost) * models * wpm
                if total_oc == 0:
                    r["_obj_pct"] = 0.0
                else:
                    vis = self._surv_visibility_multiplier(r["mob"])
                    vis_turns = raw_turns * vis
                    r["_obj_pct"] = _pct(self.obj_score(total_oc, vis_turns), obj_vals)
                # Mission score: cost penalty + visibility multiplier applied to SURV and OBJ
                # Visibility: bigger units can't hide → focused down before holding objectives
                vis_mult = self._surv_visibility_multiplier(r["mob"])
                surv_contrib = w["surv"] * r["_surv_pct"] * cost_eff * vis_mult / 100.0
                obj_contrib = w.get("obj", 0) * r["_obj_pct"] * vis_mult
                r["_mission_score"] = (
                    w["dps"] * r["_dps_pct"] +
                    surv_contrib +
                    obj_contrib +
                    w["mob"] * r["_mob_pct"]
                )
                # Action-capability penalty: OC0 units can't perform actions
                # Harsher in action-heavy missions
                if total_oc == 0:
                    ACTION_PENALTIES = {
                        'Reconnaissance': 0.5,   # Actions are THE scoring mechanism
                        'Disruption': 0.8,        # Actions matter but not everything
                    }
                    penalty = ACTION_PENALTIES.get(mission, 1.0)
                    r["_mission_score"] *= penalty
            results.sort(key=lambda r: r["_mission_score"], reverse=True)
        else:
            dps_vals = [r["dpp"] for r in results]
            SURV_SHOTS_PER_TURN = 5
            surv_vals = [
                r["surv"]["primary_shots"] / SURV_SHOTS_PER_TURN
                for r in results
            ]
            obj_vals = []
            for r in results:
                st = r["surv"]["primary_shots"] / SURV_SHOTS_PER_TURN
                base_oc = r["mob"].get("objective_control", 0)
                boost = r.get("oc_boost", 0)
                models = r["surv"].get("models", 1)
                wpm = min(r["surv"].get("wounds_per_model", 1), 3)
                total_oc = (base_oc + boost) * models * wpm
                obj_vals.append(self.obj_score(total_oc, st))
            n = len(results)

            def _pct(val, series):
                if n <= 1:
                    return 100
                below = sum(1 for x in series if x < val)
                same = sum(1 for x in series if x == val)
                return round((below + 0.5 * (same - 1)) / (n - 1) * 100)

            for r in results:
                r["_dps_pct"] = _pct(r["dpp"], dps_vals)
                surv_turns = r["surv"]["primary_shots"] / SURV_SHOTS_PER_TURN
                r["_surv_turns"] = round(surv_turns, 1)
                r["_surv_pct"] = _pct(surv_turns, surv_vals)
                r["_mob_pct"] = self.mob_score(r["mob"])
                base_oc = r["mob"].get("objective_control", 0)
                boost = r.get("oc_boost", 0)
                total_oc = (base_oc + boost) * r["surv"].get("models", 1)
                if total_oc == 0:
                    r["_obj_pct"] = 0.0
                else:
                    r["_obj_pct"] = _pct(self.obj_score(total_oc, surv_turns), obj_vals)
            results.sort(key=lambda r: r["dpp"], reverse=True)

        return results

    def compute_disposition_ranking(self, disposition: str, target=None, mission=None,
                                     meta_name: Optional[str] = None, **kwargs) -> dict:
        """Compute ranking for all detachments valid for a given disposition.

        Returns dict mapping detachment name → ranking results (or error dict).
        """
        valid = self.config.get_detachments_for_disposition(disposition)
        results = {}
        for det_name in valid:
            try:
                r = self.compute_ranking(
                    target=target, mission=mission, meta_name=meta_name,
                    detachment=det_name, disposition=disposition, **kwargs
                )
                results[det_name] = r
            except Exception as e:
                results[det_name] = {"error": str(e)}
        return results

    # ── Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _surv_visibility_multiplier(mob):
        """SURV visibility multiplier based on model size.

        Larger models can't hide behind terrain → more attackers target them
        per turn → they die faster in practice. Multiplier applied to
        primary_shots BEFORE percentile calculation.

        Range: 0.80 (super-heavy) to 1.00 (infantry).
        """
        keywords_upper = [k.upper() for k in mob.get("keywords", [])]
        has_titanic = "TITANIC" in keywords_upper
        has_frame = mob.get("has_frame", False)
        is_infantry = "INFANTRY" in keywords_upper
        is_character = mob.get("is_character", False)
        is_vehicle = "VEHICLE" in keywords_upper
        is_monster = "MONSTER" in keywords_upper
        is_mounted = "MOUNTED" in keywords_upper
        is_jump = "JUMP PACK" in keywords_upper

        if has_titanic and has_frame:
            return 0.80   # Super-heavy: Baneblade, Stompa — visible from everywhere
        if has_titanic:
            return 0.85   # Titanic: Knight, Wraithknight — big, hard to hide
        if is_vehicle or is_monster:
            return 0.90   # Vehicle/Monster: visible but can use some terrain
        if is_mounted or is_jump:
            return 0.95   # Cavalry/Jump: slightly bigger, slightly more visible
        if is_character and not is_infantry:
            return 0.95   # Non-infantry character: single model, easy to hide
        return 1.00       # Infantry/small unit: can spread behind terrain

    @staticmethod
    def obj_score(total_oc, surv_turns):
        """Objective holding score 0-100.

        Formula: effective_OC × survival_turns, normalized to 0-100.
        effective_OC = OC_per_model × models × wounds_per_model.
        Wounds_per_model accounts for OC decay: W1 models lose OC 1:1 with wounds,
        W3 models absorb 3 wounds per model before losing OC.
        - effective_OC=0 → score=0 (Thunderhawk, flyers cannot hold objectives)
        """
        if total_oc == 0:
            return 0
        # Raw: effective_OC × turns. Max realistic ~8 OC × 3W × 6 turns = 144
        raw = total_oc * surv_turns
        # Normalize: 0 → 0, 144+ → 100
        return min(round(raw / 144 * 100), 100)

    @staticmethod
    def mob_score(mob):
        """Pure mobility score 0-100.

        Terrain Navigation Factor (TNF) model:
        - Infantry/Beast/Swarm move through walls (1" cost) → TNF 1.0
        - Vehicles/Monsters must go AROUND terrain → TNF 0.5
        - Titanic without terrain ability → TNF 0.35 (barely navigates)
        - Titanic with terrain ability (Titanic Strides etc.) → TNF 0.65
        - Fly ignores all terrain → TNF 1.0
        - Terrain abilities (Scuttling Walker, Clankin' Forward, etc.) improve TNF

        Footprint penalty reflects model size relative to terrain gaps:
        - Infantry/Beast/Swarm → no penalty (small bases)
        - Mounted/Jump Pack → -2 (medium bases)
        - Vehicle Walker / Monster (non-Titanic) → -4 (medium-large)
        - Vehicle non-Walker (tracked) → -6 (large footprint)
        - Titanic → -10 (huge, barely fits on table)
        """
        keywords_upper = [k.upper() for k in mob.get("keywords", [])]
        has_goi = mob.get("gate_of_infinity", False)
        has_ds = mob.get("deep_strike", False)
        has_fly = mob.get("fly", False)
        has_fortification = "FORTIFICATION" in keywords_upper
        has_titanic = "TITANIC" in keywords_upper
        has_terrain = mob.get("has_terrain_ability", False)
        no_t1 = mob.get("no_t1_reinforcements", True)

        is_infantry = "INFANTRY" in keywords_upper
        is_vehicle = "VEHICLE" in keywords_upper
        is_walker = "WALKER" in keywords_upper
        is_monster = "MONSTER" in keywords_upper
        is_beast = "BEAST" in keywords_upper
        is_swarm = "SWARM" in keywords_upper
        is_mounted = "MOUNTED" in keywords_upper
        is_jump = "JUMP PACK" in keywords_upper

        # Parse movement from string like '6"'
        m_str = mob.get("movement", "6\"")
        try:
            movement = int(m_str.replace('"', '').replace("'", ""))
        except (ValueError, AttributeError):
            movement = 6

        # Fortification = can't move
        if has_fortification:
            return 0

        # --- Frame detection ---
        # Frame = hull measurement (no base). Baneblade, Lord of Skulls, etc.
        # These units must fit their ENTIRE hull through terrain gaps.
        has_frame = mob.get("has_frame", False)

        # --- Terrain Navigation Factor (TNF) ---
        # Reflects how well the unit navigates terrain in practice.
        #
        # Key hierarchy (11e terrain rules):
        # - FLY/HOVER/INFANTRY/BEAST/SWARM: ignore terrain (TNF 1.0)
        # - TITANIC + terrain ability + no Frame: can go over 4" terrain, has base (0.70)
        # - TITANIC + terrain ability + Frame: can go over 4" terrain, hull measurement (0.55)
        # - TITANIC + no terrain + Frame: must go around, hull, diagonal = 2x (0.25)
        # - TITANIC + no terrain + no Frame: must go around, has base (0.40)
        # - VEHICLE/MONSTER + terrain ability: can go over terrain (0.75)
        # - VEHICLE/MONSTER no terrain: must go around (0.55)
        if has_fly:
            tnf = 1.0
        elif is_infantry or is_beast or is_swarm:
            tnf = 1.0
        elif is_mounted or is_jump:
            tnf = 1.0
        elif has_titanic:
            if has_terrain and not has_frame:
                tnf = 0.70  # Knights on base: can go over 4" terrain
            elif has_terrain and has_frame:
                tnf = 0.55  # Stompa/Warlord: terrain ability but hull measurement
            elif not has_terrain and has_frame:
                tnf = 0.25  # Baneblade: must go around, diagonal = 2x movement
            else:
                tnf = 0.40  # TITANIC no ability, has base: rare case
        elif is_vehicle or is_monster:
            if has_terrain:
                tnf = 0.75  # Can go over terrain (Clankin' Forward, etc.)
            else:
                tnf = 0.55  # Must go around terrain
        else:
            tnf = 0.85  # Default for unclassified units (Psyker, Character, etc.)

        # --- Footprint penalty ---
        # Larger models are harder to position and navigate through gaps.
        # Frame = hull measurement = extra penalty (can't fit through gaps easily)
        if has_titanic and has_frame:
            footprint_penalty = -12  # Hull + huge = diagonal movement kills you
        elif has_titanic:
            footprint_penalty = -6   # Large base but has terrain ability
        elif is_infantry or is_beast or is_swarm:
            footprint_penalty = 0
        elif is_mounted or is_jump:
            footprint_penalty = -2
        elif is_vehicle and not is_walker:
            footprint_penalty = -6  # Tracked vehicles: wide, can't fit gaps
        elif is_walker or is_monster:
            footprint_penalty = -4  # Walkers/monsters: medium-large
        else:
            footprint_penalty = -2  # Default: medium

        # --- Base movement score ---
        base_movement = min(movement * 4.5, 90)
        movement_score = base_movement * tnf + footprint_penalty

        # --- Minimum floor ---
        # Even the worst unit (Baneblade, Lord of Skulls) still moves ~half its M.
        # Score 0 = half movement, not zero movement. Floor = 15% of base_movement.
        if movement > 0:
            min_score = base_movement * 0.15
            movement_score = max(movement_score, min_score)

        # --- Bonuses ---
        # Deep Strike: one-time ingress positioning (not ongoing mobility)
        if has_ds:
            movement_score += 10 if no_t1 else 15

        # Fly: persistent mobility advantage (on top of TNF=1.0)
        if has_fly:
            movement_score += 10

        # Gate of Infinity: unlimited redeploy
        if has_goi:
            movement_score = max(movement_score, 85)

        return min(max(int(movement_score), 0), 100)

    @staticmethod
    def _loadout_desc(ranged, melee, innate):
        """Human-readable loadout description."""
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

    # ── Printing ─────────────────────────────────────────────────────

    @staticmethod
    def _bar(pct, width=10):
        filled = round(pct / 100 * width)
        return "█" * filled + "░" * (width - filled)

    def format_mob(self, mob_dict):
        """Human-readable mobility string."""
        m = mob_dict["movement"]
        fly = " Fly" if mob_dict["fly"] else ""
        ds = " DS" if mob_dict["deep_strike"] else ""
        oc = mob_dict["objective_control"]
        tier = mob_dict["mobility_tier"]
        return f'M={m}{fly}{ds} OC={oc} [{tier}]'

    def format_surv(self, defense_dict):
        """Human-readable survivability string."""
        ew = defense_dict["effective_wounds"]
        prim = defense_dict.get("primary_metric", "lascannon")
        pps_prim = defense_dict.get(f"pts_per_shot_{prim}", "?")
        pps_l = defense_dict.get("pts_per_shot_lascannon", "?")
        pps_m = defense_dict.get("pts_per_shot_melta", "?")
        prim_label = prim.upper()[:3]
        return (f'T{defense_dict["toughness"]} W{defense_dict["total_wounds"]} '
                f'SV{defense_dict["save"]}{defense_dict.get("invuln","") or ""}'
                f'{defense_dict.get("fnp","") or ""} '
                f'| effW {ew["ap0"]}/{ew["ap2"]}/{ew["ap4"]} '
                f'| ★{prim_label}={pps_prim}pts/shot LC={pps_l}pts/shot MC={pps_m}pts/shot')

    def print_ranking(self, results, target_name="MEQ", mission_name=None, meta_name=None, tier="1st"):
        """Print ranking table and detail."""
        n = len(results)
        if not n:
            print("No results.")
            return

        is_meta = bool(meta_name)
        display_target = meta_name or target_name

        if is_meta:
            meta_targets = self.config._resolve_meta(meta_name)
            meta_desc = ", ".join(f"{tn}×{w:.0%}" for tn, _, w in meta_targets)
            title = f"## {self.config.supported['name']} — Meta Ranking: {meta_name}  ({meta_desc})"
        else:
            title = f"## {self.config.supported['name']} — Ranking vs {display_target}"
        tier_label = " — 3rd+ unit pricing" if tier == "3rd" else ""
        if mission_name:
            title += f" (mission: {mission_name})"
        title += tier_label
        print(f"{title}\n")

        has_mission = bool(mission_name) and "_mission_score" in (results[0] if results else {})

        # Survivability: heavy anti-tank (S14 AP-4 D6+1) benchmark
        # Computed as expected turns to kill: 5 heavy shots per turn.
        # 100% = survives 5+ turns, 0% = dies instantly.
        SURV_SHOTS_PER_TURN = 5  # assumed incoming heavy shots per turn
        surv_vals = []
        for r in results:
            prim_shots = r["surv"]["primary_shots"]
            turns = prim_shots / SURV_SHOTS_PER_TURN
            r["_surv_turns"] = round(turns, 1)
            surv_vals.append(turns)
        dps_vals = [r["dpp"] for r in results]
        mob_vals = [self.mob_score(r["mob"]) for r in results]

        def _norm(val, series):
            """Normalise as percentage of max (ratio-of-max, not min-max).
            
            A unit with half the top value shows as 50%, not 0%.
            """
            if not series:
                return 0
            mx = max(series)
            if mx == 0:
                return 0
            return round(val / mx * 100)

        for r in results:
            r["_dps_bar"] = _norm(r["dpp"], dps_vals)
            r["_surv_turns"] = r.get("_surv_turns", r["surv"]["primary_shots"] / 5)
            r["_surv_bar"] = min(int(r["_surv_turns"] / 5 * 100), 100)
            r["_mob_bar"] = _norm(self.mob_score(r["mob"]), mob_vals)
            r["_mob_raw"] = self.mob_score(r["mob"])

        # Sort by mission score or DPP
        if has_mission:
            results.sort(key=lambda r: r["_mission_score"], reverse=True)
        else:
            results.sort(key=lambda r: r["dpp"], reverse=True)

        # ── Table ────────────────────────────────────────────────────
        print("```")
        header = f'{"Unit":<42s} {"Pts":>5s} {"Scr":>4s}  {"DPS":>4s} {"SURV":>4s} {"MOB":>4s}  {"Bars":<33s}'
        print(header)
        print("-" * len(header))

        for r in results:
            name = r["name"]
            name_display = name[:42]
            pts = r["points"]
            score = r.get("_mission_score", r["dpp"])
            score_display = f"{score:>3.0f}" if has_mission else ""

            dps_b = self._bar(r["_dps_bar"])
            surv_b = self._bar(r["_surv_bar"])
            mob_b = self._bar(r["_mob_bar"])

            print(f'{name_display:<42s} {pts:>5d} {score_display:>4s}  {r["_dps_bar"]:>3d}% {r["_surv_bar"]:>3d}%  {r["_mob_bar"]:>3d}%  {dps_b} {surv_b} {mob_b}')

        print("```")
        print("  SURV bars show expected turns to die (100% = 5+ turns vs 5 heavy AT shots/turn)")
        if has_mission:
            print(f"  Scr  = mission-weighted score (higher = better fit for {mission_name})")
        print()

        # ── Detail ───────────────────────────────────────────────────
        for r in results[:5]:
            print(f"### {r['name']} ({r['points']}pts)")
            print(f'**Profile:** DPS {self._bar(r["_dps_bar"])} {r["_dps_bar"]:>2d}%  '
                  f'SURV {self._bar(r["_surv_bar"])} {r["_surv_bar"]:>2d}%  '
                  f'MOB {self._bar(r["_mob_bar"])} {r["_mob_bar"]:>2d}%')
            print(f'**Loadout:** {r["loadout_desc"]}')
            surv_turns = r.get("_surv_turns", 0)
            print(f'**SURV:** {self.format_surv(r["surv"])}'
                  f'  |  ~{surv_turns:.1f}t vs heavy AT (at 5 shots/turn)')
            print(f'**MOB:** raw={r["_mob_raw"]}/100 ({self.format_mob(r["mob"])})')
            if r["notes"]:
                print(f'*{r["notes"]}*')
            print()

        # ── Footer ───────────────────────────────────────────────────
        fk = self.config.faction_key
        print("---")
        print(f"*{len(results)} units ranked | faction: {self.config.supported['name']} | engine: ranking.py*")
        print()
        print("**Assumptions:**")
        print("- opponent unknown (all-comers)")
        print("- no cover factored into saves")
        print("- no detachment buffs, stratagems, or command rerolls")
        print("- no unit coherency or transport constraints")
        print("- average dice (no variance band)")
        print("- Melee DPP included in total (assumes charge reaches target)")
        print("- No FNP on the target")
        print("- Blast modelled (11e: +X attacks per 5 models)")
        print("- Melta half-range bonus only if --melta flag set")
        print("- Heavy stationary bonus only if --heavy flag set")
        print("- Plunging Fire auto-applied for TOWERING units (--no-plunging to disable)")
        print("- Character buffs to their squad NOT included (only solo model output)")
        print()
        print("**What DPP does NOT model:**")
        print("- Detachment buffs")
        print("- Stratagem support")
        # Faction-specific limitations
        fk = self.config.faction_key.lower() if self.config.faction_key else ""
        if "grey knight" in fk:
            print("- Gate of Infinity redeployment value")
            print("- Purifying Flame Anti-Infantry 2+ critical wounds bonus")
            print("- Interceptor's Personal Teleporters mobility")
        elif "chaos knight" in fk:
            print("- Harbingers of Dread abilities")
            print("- Malefic Surge mortal wound risk")
            print("- Super-heavy Walker ignore terrain / stomp attacks")
            print("- DAMNED ally interactions")
            print("- Aura effects (Dread auras, battleshock synergies)")
