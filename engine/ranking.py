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

        # Build lookup sets
        self.known_units: set[str] = set()
        self.known_units.update(self.squads.keys())
        self.known_units.update(self.characters.keys())
        self.known_units.update(self.vehicles.keys())
        self.known_units.update(self.weapon_options.keys())

        # Extra units handled by resolve_loadout but not in config dicts
        self._extra_known: set[str] = set()
        for name in self.weapon_options:
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
    """Load WeaponCatalog from a merged JSON path."""
    return WeaponCatalog(merged_path, faction=faction)


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


def _wp_dmg(wp, target, modifier: Optional[WeaponModifier] = None,
            melta_active: bool = False, heavy_stationary: bool = False, hit_mode: HitMode = HitMode.NORMAL):
    """Damage for a single weapon against target (single or weighted list)."""
    if isinstance(target, list):
        return sum(w * compute_weapon_dpp(wp, tp, modifier=modifier, unit_points=1, hit_mode=hit_mode,
                                          melta_active=melta_active, heavy_stationary=heavy_stationary)["total_damage"]
                   for _, tp, w in target)
    return compute_weapon_dpp(wp, target, modifier=modifier, unit_points=1, hit_mode=hit_mode,
                              melta_active=melta_active, heavy_stationary=heavy_stationary)["total_damage"]


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

    def _eval_squad_variant(self, cfg, spec_indices):
        """Evaluate one loadout variant for a squad config."""
        n = cfg["n"]
        n_sp = len(spec_indices)
        if n_sp > cfg["special_max"]:
            return None
        unit_name = cfg.get("unit") or next(
            (k for k, v in self.config.squads.items() if v is cfg),
            cfg.get("unit", "")
        )
        opts = cfg["specials"]
        sp_loses_r = cfg.get("sp_loses_r", True)
        sp_loses_m = cfg.get("sp_loses_m", False)
        apoth = cfg.get("apoth_loses_r", False)

        ranged, melee, innate = [], [], []
        si = 0
        for i in range(n):
            for iname in cfg.get("innate", []):
                innate.append(self.W(iname, unit_name=unit_name))
            if si < n_sp:
                sname = opts[spec_indices[si]]
                si += 1
                ranged.append(self.W(sname, unit_name=unit_name))
                if sp_loses_m:
                    melee.append(self.W("Close combat weapon", unit_name=unit_name))
                else:
                    melee.append(self.W(cfg["melee"], unit_name=unit_name))
            else:
                is_apoth = apoth and i == n - 1
                if not is_apoth:
                    if cfg.get("ranged"):
                        kw = {}
                        if "ranged_a" in cfg:
                            kw["a"] = cfg["ranged_a"]
                        ranged.append(self.W(cfg["ranged"], unit_name=unit_name, **kw))
                melee.append(self.W(cfg["melee"], unit_name=unit_name))
        return {"ranged": ranged, "melee": melee, "innate": innate}

    def _best_squad_variant(self, name, target):
        """Find optimal special weapon loadout for a squad vs a target."""
        cfg = self.config.squads.get(name)
        if not cfg:
            return None
        import itertools
        opts = cfg["specials"]
        best, best_d = None, -1
        for n_sp in range(0, cfg["special_max"] + 1):
            for indices in itertools.product(range(len(opts)), repeat=n_sp):
                ld = self._eval_squad_variant(cfg, list(indices))
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
            for tname, tp in self.config.target_profiles.items():
                if target == tp:
                    target_tag = tname
                    break
            tag = target_tag or (
                "meta" if isinstance(target, list) else "custom"
            )
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

    def _best_vehicle_variant(self, ranged_names, melee_names, unit_name, target):
        """Try all ranged+melee combos for a weapon-option vehicle."""
        import itertools
        best, best_d = None, -1
        for (rf1_name,), (rf2_name,) in itertools.combinations_with_replacement(
            [(n,) for n in ranged_names], 2
        ):
            for mm_name in melee_names:
                ranged = [
                    self.W(rf1_name, unit_name=unit_name),
                    self.W(rf2_name, unit_name=unit_name),
                ]
                melee = [self.W(mm_name, unit_name=unit_name)]
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

    def resolve_loadout(self, name, target, pricing=None, tier="1st"):
        """Resolve a unit's weapons for a given target.

        Args:
            name: Unit name.
            target: TargetProfile (or weighted list).
            pricing: Pricing data from merged JSON.
            tier: '1st' (default) or '3rd' (progressive pricing).

        Returns (points, ranged, melee, innate, info_dict) or None.
        """
        # Squad: optimise special weapons per target
        if name in self.config.squads:
            sdetail = self.config.squads[name]
            pts = self._resolve_pts(
                sdetail["pts"], sdetail.get("pts_3rd"),
                pricing, sdetail["n"], tier,
            )
            ld = self._best_squad_variant(name, target)
            return (pts, ld["ranged"], ld["melee"], ld["innate"], sdetail["info"])

        # Vehicle with weapon options (NDK / GMNDK)
        if name in self.config.weapon_options:
            wo = self.config.weapon_options[name]
            pts = self._resolve_pts(
                wo.get("pts", 0), wo.get("pts_3rd"),
                pricing, 1, tier,
            )
            bv = self._best_vehicle_variant(wo["ranged"], wo["melee"], name, target)
            info = wo.get("info", {})
            return (pts, bv["ranged"], bv["melee"], bv["innate"], info)

        # Character: fixed loadout (with optional weapon choice)
        if name in self.config.characters:
            ch = self.config.characters[name]
            pts = self._resolve_pts(
                ch["pts"], ch.get("pts_3rd"),
                pricing, 1, tier,
            )
            ranged = [self.W(rn, unit_name=name) for rn in ch["ranged"]]
            melee = [self.W(mn, unit_name=name) for mn in ch["melee"]]
            innate = [self.W(inn, unit_name=name) for inn in ch.get("innate", [])]
            # Weapon options: pick best variant vs target
            if "weapon_options" in ch:
                opts = ch["weapon_options"]
                if "ranged" in opts:
                    best_rng = max(
                        ([self.W(rn, unit_name=name) for rn in opt] for opt in opts["ranged"]),
                        key=lambda ws: _ld_dmg(ws, melee, innate, target),
                    )
                    ranged = best_rng
                if "melee" in opts:
                    best_ml = max(
                        ([self.W(mn, unit_name=name) for mn in opt] for opt in opts["melee"]),
                        key=lambda ws: _ld_dmg(ranged, ws, innate, target),
                    )
                    melee = best_ml
            return (pts, ranged, melee, innate, ch.get("info"))

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

        return (best_pts, best_ranged, best_melee, fixed_innate, vh.get("info"))

    # ── Unit info ────────────────────────────────────────────────────

    def get_unit_info(self, name, profile_data):
        """Return (keywords, toughness, save, wounds, oc, invuln) from config + profile."""
        # Squad info
        if name in self.config.squads:
            info = self.config.squads[name]["info"]
            kw = ["INFANTRY", "DEEP STRIKE"]
            kw.extend(self.config.faction_keywords)
            if info.get("FLY"):
                kw.append("FLY")
            if "Terminator" in name:
                kw.append("TERMINATOR")
            return kw, info["T"], info["SV"], info["W"], info["OC"], info.get("invuln") or info.get("INV")

        # Vehicle info
        if name in self.config.vehicles:
            vh = self.config.vehicles[name]
            info = vh.get("info", {})
            kw = ["VEHICLE"]
            kw.extend(self.config.faction_keywords)
            if "DREADNOUGHT" in name.upper():
                kw.append("DREADNOUGHT")
            if info.get("invuln") or info.get("INV"):
                kw.append("WALKER")
                kw.append("DEEP STRIKE")
            return kw, info["T"], info["SV"], info["W"], info["OC"], info.get("invuln") or info.get("INV")

        # Weapon-option vehicle info (NDK / GMNDK)
        if name in self.config.weapon_options:
            wo = self.config.weapon_options[name]
            info = wo.get("info", {})
            kw = ["VEHICLE", "WALKER", "DEEP STRIKE"]
            kw.extend(self.config.faction_keywords)
            return kw, info["T"], info["SV"], info["W"], info["OC"], info.get("invuln") or info.get("INV")

        # Character info
        if name in self.config.characters:
            ch = self.config.characters[name]
            info = ch.get("info", {})
            t_val = info.get("T", 4)
            kw = ["INFANTRY", "CHARACTER", "DEEP STRIKE"]
            kw.extend(self.config.faction_keywords)
            if t_val >= 5:
                kw.append("TERMINATOR")
            return kw, info["T"], info["SV"], info["W"], info["OC"], info.get("invuln") or info.get("INV")

        # Fallback: from profile data
        stats = profile_data.get("stats", {})
        if stats.get("T"):
            t_val = int(str(stats.get("T", "4")).replace('"', ""))
            sv_val = int(str(stats.get("SV", "3+")).replace("+", "").replace('"', ""))
            w_val = int(str(stats.get("W", "2")).replace('"', ""))
            oc_val = int(str(stats.get("OC", "1")).replace('"', ""))
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
                         plunging: bool = True):
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

            kws_upper = [k.upper() for k in profile.get("keywords", [])]

            # Skip units without faction keyword (unless no profile data — still rank if config has it)
            if profile and not any(fk in kws_upper for fk in self.config.faction_keywords):
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

            resolved = self.resolve_loadout(name, actual_target, pricing, tier=tier)
            if resolved is None:
                continue
            pts, ranged_profiles, melee_profiles, innate_profiles, info = resolved

            # Auto-apply Plunging Fire (+1 BS) for TOWERING units [11e core rules]
            # TOWERING units are always considered elevated vs ground targets.
            # Psychic weapons will ignore this per [24.29] in compute_weapon_dpp.
            unit_hit_mode = HitMode.NORMAL
            if plunging and "TOWERING" in profile_kw:
                unit_hit_mode = HitMode.PLUNGING_FIRE

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
            is_infantry = "INFANTRY" in kw_list
            fnp_val = 6 if is_infantry else None

            # SURV (with optional detachment modifier)
            # Note: unit_surv_mod is already gated on original DM having affects=="surv" above
            if unit_surv_mod:
                final_invuln = inv_val or unit_surv_mod.invulnerable_save
                final_fnp = unit_surv_mod.feel_no_pain
            else:
                final_invuln = inv_val
                final_fnp = fnp_val

            defense = UnitDefense(
                toughness=t_val,
                wounds_per_model=w_val,
                save=sv_val,
                invuln=final_invuln,
                fnp=final_fnp if is_infantry else final_fnp,
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

            has_gate = is_infantry or "DREADNOUGHT" in kw_list or "WALKER" in kw_list

            mob = compute_mob(
                movement=m_val,
                fly=has_fly,
                deep_strike=has_deep_strike,
                oc=oc_val,
                keywords=kw_list,
                gate_of_infinity=has_gate,
                no_t1_reinforcements=self.no_t1_reinforcements,
            )

            notes = self.config.notes.get(name, "")

            result_entry = {
                "name": name,
                "points": pts,
                "dpp": round(dpp_val, 4),
                "total_damage": round(total_dmg, 2),
                "surv": surv,
                "mob": mob,
                "loadout_desc": self._loadout_desc(ranged_profiles, melee_profiles, innate_profiles),
                "notes": notes,
            }
            if meta_name:
                result_entry["_meta_name"] = meta_name
            results.append(result_entry)

        # Score/sort
        if mission and mission in self.config.mission_profiles:
            w = self.config.mission_profiles[mission]
            dps_vals = [r["dpp"] for r in results]
            # Surv turns: expected turns to die vs 5 heavy AT shots/turn (same as display)
            SURV_SHOTS_PER_TURN = 5
            surv_vals = [
                r["surv"]["primary_shots"] / SURV_SHOTS_PER_TURN
                for r in results
            ]
            mob_vals = [self.mob_score(r["mob"]) for r in results]
            n = len(results)

            def _pct(val, series):
                if n <= 1:
                    return 100
                return round(sum(1 for x in series if x < val) / (n - 1) * 100)

            for r in results:
                r["_dps_pct"] = _pct(r["dpp"], dps_vals)
                surv_turns = r["surv"]["primary_shots"] / SURV_SHOTS_PER_TURN
                r["_surv_turns"] = round(surv_turns, 1)
                r["_surv_pct"] = _pct(surv_turns, surv_vals)
                r["_mob_pct"] = _pct(self.mob_score(r["mob"]), mob_vals)
                r["_mission_score"] = (
                    w["dps"] * r["_dps_pct"] +
                    w["surv"] * r["_surv_pct"] +
                    w["mob"] * r["_mob_pct"]
                )
            results.sort(key=lambda r: r["_mission_score"], reverse=True)
        else:
            dps_vals = [r["dpp"] for r in results]
            SURV_SHOTS_PER_TURN = 5
            surv_vals = [
                r["surv"]["primary_shots"] / SURV_SHOTS_PER_TURN
                for r in results
            ]
            mob_vals = [self.mob_score(r["mob"]) for r in results]
            n = len(results)

            def _pct(val, series):
                if n <= 1:
                    return 100
                return round(sum(1 for x in series if x < val) / (n - 1) * 100)

            for r in results:
                r["_dps_pct"] = _pct(r["dpp"], dps_vals)
                surv_turns = r["surv"]["primary_shots"] / SURV_SHOTS_PER_TURN
                r["_surv_turns"] = round(surv_turns, 1)
                r["_surv_pct"] = _pct(surv_turns, surv_vals)
                r["_mob_pct"] = _pct(self.mob_score(r["mob"]), mob_vals)
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
    def mob_score(mob):
        """Mobility score 0-100."""
        has_goi = mob.get("gate_of_infinity", False)
        has_ds = mob.get("deep_strike", False)
        has_fly = mob.get("fly", False)
        oc = mob.get("objective_control", 1)
        tier = mob.get("mobility_tier", "slow")
        no_t1 = mob.get("no_t1_reinforcements", True)

        # No T1 Reinforcements (11e core rule) reduces Deep Strike value
        ds_bonus = 5 if (has_ds and no_t1) else (10 if has_ds else 0)

        if has_goi:
            base = 75
            m_bonus = {
                "skyborne": 0, "very_fast": 12, "fast": 10, "cavalry": 8,
                "standard": 5, "slow": 3, "transporter": 5, "static": 0,
            }.get(tier, 0)
            fly_bonus = 5 if has_fly else 0
            oc_bonus = min(oc * 3, 20)
            return min(base + m_bonus + fly_bonus + ds_bonus + oc_bonus, 100)
        else:
            tier_map = {"static": 10, "slow": 25, "standard": 45,
                        "fast": 55, "very_fast": 70, "cavalry": 80,
                        "flyer": 95, "skyborne": 95, "transporter": 70}
            base = tier_map.get(tier, 30)
            bonuses = ds_bonus
            if has_fly:
                bonuses += 10
            oc_bonus = min(oc * 3, 20)
            return min(base + bonuses + oc_bonus, 100)

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
