"""Data-driven weapon profile loader from BSData merged JSON.

Replaces all hardcoded factory functions with a single source of truth
read from the merged faction JSON files.

Usage:
    W = WeaponCatalog("data/merged/grey-knights.json")
    psycannon = W.load("Psycannon")
    nfw = W.load("Nemesis force weapon", unit_name="Strike Squad")
    inc = W.load("Incinerator")
"""

import sys
import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine.dpp import WeaponProfile


# ── Stat value parsers ──────────────────────────────────────────────

def _parse_int(s: str) -> int:
    """Parse '3+' → 3, '2+' → 2. Falls back to 0."""
    return int(s.rstrip("+")) if s and s.rstrip("+").isdigit() else 0


def _parse_ap(s: str) -> int:
    """Parse '-1' → -1, '0' → 0."""
    try:
        return int(s)
    except (ValueError, TypeError):
        return 0


def _parse_attacks(s: str) -> float:
    """Parse attacks string to float average.

    'D6' → 3.5, '2D6' → 7.0, '3' → 3.0, 'D3+1' → 3.0, etc.
    """
    if not s or s == "-":
        return 0.0

    s = s.strip()
    # Dice expressions
    dice_map = {"D6": 3.5, "D3": 2.0}
    # Try 2D6, 3D3 etc
    m = re.match(r"^(\d*)D(6|3)(?:\s*\+\s*(\d+))?$", s)
    if m:
        count = int(m.group(1)) if m.group(1) else 1
        die = 6 if m.group(2) == "6" else 3
        bonus = int(m.group(3)) if m.group(3) else 0
        return count * (die + 1) / 2.0 + bonus

    # Plain number
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def _parse_keywords(s: str) -> list[str]:
    """Parse 'Ignores Cover, Torrent' → ['Ignores Cover', 'Torrent']."""
    if not s or s == "-":
        return []
    return [kw.strip() for kw in s.split(",") if kw.strip()]


# ── Faction overlays ────────────────────────────────────────────────

FACTION_OVERLAYS: dict[str, list[str]] = {
    # Grey Knights: Psychic is a faction rule — all weapons add it
    "grey-knights": ["Psychic"],
    # Chaos Knights: no faction-wide weapon overlay
    "chaos-knights": [],
    # Future factions can add their own overlays
}


# ── WeaponCatalog ───────────────────────────────────────────────────

class WeaponCatalog:
    """Loads weapon profiles from a BSData merged JSON file."""

    def __init__(self, json_path: str, faction: str | None = "grey-knights"):
        self.faction = faction
        self._faction_keywords = FACTION_OVERLAYS.get(faction, [])

        with open(json_path) as f:
            self.data = json.load(f)

        self._build_index()

    def _build_index(self):
        """Index by weapon name (lowercase) and by unit name.

        Groups variants by stat signature (ignoring BS/WS since those are
        unit stats, not weapon stats). The most common variant becomes the
        default; `unit_name` can select a specific variant.
        """
        self.by_name: dict[str, list[dict]] = {}
        self.by_unit: dict[str, list[dict]] = {}
        # name.lower → {(A, S, AP, D, KW): [entries]}
        self._variant_groups: dict[str, dict[tuple, list[dict]]] = {}

        for u in self.data.get("units", []):
            uname = u.get("name", "")
            self.by_unit.setdefault(uname, [])

            prof = u.get("profile")
            if prof is None or not isinstance(prof, dict):
                continue
            for w in prof.get("weapons", []):
                for p in w.get("profiles", []):
                    raw_name = p.get("name", "").replace("\u27a4 ", "").strip()
                    key = raw_name.lower()
                    stats = p.get("stats", {})

                    entry = {
                        "unit": uname,
                        "weapon_name": w.get("name", "").replace("\u27a4 ", "").strip(),
                        "profile_name": raw_name,
                        "type_name": p.get("typeName", ""),
                        "stats": stats,
                    }

                    self.by_unit.setdefault(uname, []).append(entry)
                    self._variant_groups.setdefault(key, {})

                    # Build signature WITHOUT BS/WS
                    sig = (
                        stats.get("A", "1"),
                        stats.get("S", "4"),
                        stats.get("AP", "0"),
                        stats.get("D", "1"),
                        stats.get("Keywords", "-"),
                    )
                    self._variant_groups[key].setdefault(sig, []).append(entry)

        # Build by_name and default BS/WS per weapon
        self._default_bs: dict[str, int] = {}
        self._default_ws: dict[str, int] = {}

        for key, groups in self._variant_groups.items():
            # Sort groups: largest group first (most common stat variant)
            sorted_groups = sorted(
                groups.values(),
                key=lambda g: len(g),
                reverse=True,
            )
            for group in sorted_groups:
                for entry in group:
                    self.by_name.setdefault(key, []).append(entry)

        # Compute default BS/WS: most common value across all entries
        for key in self.by_name:
            bs_vals: list[int] = []
            ws_vals: list[int] = []
            for entry in self.by_name[key]:
                stats = entry["stats"]
                is_ranged = "ranged" in entry.get("type_name", "").lower()
                if is_ranged:
                    raw = stats.get("BS", "0+")
                    bs_vals.append(_parse_int(raw))
                else:
                    raw = stats.get("WS", "0+")
                    ws_vals.append(_parse_int(raw))
            # Mode (most common value)
            if bs_vals:
                self._default_bs[key] = Counter(bs_vals).most_common(1)[0][0]
            if ws_vals:
                self._default_ws[key] = Counter(ws_vals).most_common(1)[0][0]

    def list_weapons(self, unit_filter: str | None = None) -> list[str]:
        """List all available weapon profile names, optionally filtered by unit."""
        names: set[str] = set()
        if unit_filter:
            key = unit_filter.lower()
            for uname, entries in self.by_unit.items():
                if key in uname.lower():
                    for e in entries:
                        names.add(e["profile_name"])
        else:
            for name, entries in self.by_name.items():
                names.add(entries[0]["profile_name"])
        return sorted(names)

    def load(
        self,
        name: str,
        *,
        unit_name: str | None = None,
        bs: int | None = None,
        ws: int | None = None,
        a: float | None = None,
        abilities: list[str] | None = None,
    ) -> WeaponProfile:
        """Load a weapon profile from the catalog.

        Args:
            name: Weapon name (case-insensitive, partial match OK if unique).
            unit_name: If the weapon varies by unit (e.g. NFW, PF), specify
                       the unit to get the correct profile.
            bs: Override BS (e.g. Paladins BS2+ vs Strike BS3+).
            ws: Override WS (e.g. Paladins WS2+).
            a: Override attacks (e.g. for NFW which varies per model).
            abilities: Override/extend abilities (merged with faction overlay).

        Returns:
            WeaponProfile namedtuple.

        Raises:
            KeyError: If weapon not found (with fuzzy suggestions).
        """
        key = name.lower()

        # Find candidate entries
        if key not in self.by_name:
            # Try partial match
            candidates = [k for k in self.by_name if key in k]
            if not candidates:
                suggestions = sorted(self.by_name.keys())[:10]
                raise KeyError(
                    f"Weapon '{name}' not found. "
                    f"Suggestions: {', '.join(suggestions)}"
                )
            key = candidates[0]

        entries = self.by_name[key]

        # Filter by unit if specified
        if unit_name:
            unit_lower = unit_name.lower()
            unit_entries = [e for e in entries if unit_lower in e["unit"].lower()]
            if unit_entries:
                entries = unit_entries
            # If no match, fall through to first entry

        entry = entries[0]  # Take first matching entry
        stats = entry["stats"]

        # Parse stats
        raw_bs = stats.get("BS") or stats.get("bs", "0+")  
        raw_ws = stats.get("WS") or stats.get("ws", "0+")
        raw_a = stats.get("A", "1")
        raw_s = stats.get("S", "4")
        raw_ap = stats.get("AP", "0")
        raw_d = stats.get("D", "1")
        raw_kw = stats.get("Keywords", "-")

        # Determine type (ranged vs melee)
        is_ranged = "ranged" in entry.get("type_name", "").lower()

        # Parse numeric values
        parsed_a = _parse_attacks(raw_a)
        parsed_s = _parse_int(raw_s)
        parsed_ap = _parse_ap(raw_ap)
        parsed_d = _parse_attacks(raw_d)
        parsed_kw = _parse_keywords(raw_kw)

        # BS/WS priority:
        #   1. Explicit override (bs= or ws=)
        #   2. Unit-specific value from the entry (when unit_name is given)
        #   3. Most common default across all units
        if bs is not None:
            final_bs = bs
        elif unit_name:
            # Use this entry's actual BS/WS from data
            final_bs = _parse_int(raw_bs if is_ranged else raw_ws)
        else:
            final_bs = self._default_bs.get(key, _parse_int(raw_bs))

        if ws is not None:
            final_ws = ws
        elif unit_name:
            final_ws = _parse_int(raw_ws)
        else:
            final_ws = self._default_ws.get(key, _parse_int(raw_ws))

        # melee uses ws, ranged uses bs
        if not is_ranged:
            final_bs = final_ws

        final_a = a if a is not None else parsed_a
        final_kw = abilities if abilities is not None else parsed_kw

        # Apply faction overlay: add faction-wide keywords (e.g. Psychic for GK)
        for fk in self._faction_keywords:
            if fk not in final_kw:
                final_kw = final_kw + [fk]

        return WeaponProfile(
            name=entry["profile_name"],
            attacks=final_a,
            bs=final_bs,
            strength=parsed_s,
            ap=parsed_ap,
            damage=parsed_d,
            abilities=final_kw,
        )


# ── Convenience ─────────────────────────────────────────────────────

_DEFAULT_CATALOG: WeaponCatalog | None = None


def get_default_catalog(faction: str = "grey-knights") -> WeaponCatalog:
    """Get or create the default catalog for the project."""
    global _DEFAULT_CATALOG
    if _DEFAULT_CATALOG is None:
        import os
        _DEFAULT_CATALOG = WeaponCatalog(
            os.path.join(
                os.path.dirname(__file__),
                "..", "data", "merged", f"{faction}.json"
            )
        )
    return _DEFAULT_CATALOG


# Lazy module-level catalog — created on first use
_W: WeaponCatalog | None = None


def W(faction: str = "grey-knights") -> WeaponCatalog:
    """Get the default catalog (lazy init, singleton per faction)."""
    global _W
    if _W is None:
        _W = get_default_catalog(faction)
    return _W


# ── Self-test ───────────────────────────────────────────────────────

if __name__ == "__main__":
    cat = WeaponCatalog("data/merged/grey-knights.json")

    test_cases = [
        ("Storm bolter", {}),
        ("Psycannon", {}),
        ("Incinerator", {}),
        ("Psilencer", {}),
        ("Nemesis force weapon", {"unit_name": "Strike Squad"}),
        ("Nemesis force weapon", {"unit_name": "Paladin Squad"}),
        ("Purifying Flame", {"unit_name": "Purifier Squad"}),
        ("Purifying Flame", {"unit_name": "Castellan Crowe"}),
        ("Heavy psycannon", {}),
        ("Gatling psilencer", {}),
        ("Sublimator", {}),
        ("Nemesis daemon greathammer", {}),
        ("Nemesis flail", {}),
        ("Dreadfists", {}),
    ]

    for name, kwargs in test_cases:
        try:
            wp = cat.load(name, **kwargs)
            print(f"{wp.name:45s} A={wp.attacks:>5} BS={wp.bs} S={wp.strength} AP={wp.ap} D={wp.damage} KW={wp.abilities}")
        except KeyError as e:
            print(f"  MISSING: {name} — {e}")
