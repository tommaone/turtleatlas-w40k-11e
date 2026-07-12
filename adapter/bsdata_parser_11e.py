"""
BSData 11e catalogue JSON parser.

Parses 11e .json catalogue files to extract unit profiles (stats, weapons, abilities, keywords).
Handles cross-file catalogue linking via importRootEntries, entryLink resolution, Legends filtering.

11e format differs from 10e:
  - JSON instead of XML .cat
  - Characteristics are lists of {"name": "...", "$text": "..."} dicts
  - Weapons live in sharedSelectionEntries, referenced by entryLinks via targetId
  - Profile types (Unit, Ranged Weapons, etc.) defined in game system file

Usage:
    from adapter.bsdata_parser_11e import BSDataParser11e
    parser = BSDataParser11e()
    factions = parser.list_factions()
    data = parser.query_faction("Imperium - Grey Knights")
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any


SKIP_PREFIXES = ["Library -"]
SKIP_FACTIONS = {"Unaligned Forces"}
CRUCIBLE_RE = re.compile(r'\[Crucible\]', re.IGNORECASE)


class BSDataParser11e:
    """Parses BSData 11e JSON catalogue files for unit profiles."""

    def __init__(self, bsdata_dir: str | Path | None = None):
        self.bsdata_dir = Path(bsdata_dir or
                               Path(__file__).resolve().parent.parent / "bsdata")
        self._gsys_data: dict | None = None

    # -- Helpers ----------------------------------------------------------------

    def _load_json(self, path: Path) -> dict | None:
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {path}: {e}", file=sys.stderr)
            return None

    def _get_catalogue(self, data: dict) -> dict:
        """Extract the catalogue dict from a JSON file (may be wrapped)."""
        return data.get("catalogue", data)

    def _get_chars_dict(self, profile: dict) -> dict[str, str]:
        """
        Convert 11e characteristics list to a flat dict.

        11e format: [{"name": "M", "$text": "5\""}, {"name": "T", "$text": "5"}, ...]
        Returns: {"M": "5\"", "T": "5", ...}
        """
        chars = profile.get("characteristics", [])
        if isinstance(chars, dict):
            return {k: str(v) for k, v in chars.items()}
        result: dict[str, str] = {}
        for c in chars if isinstance(chars, list) else []:
            if isinstance(c, dict):
                name = c.get("name", "")
                text = c.get("$text", "")
                if name:
                    result[name] = text
                elif text:
                    # Fallback for list of plain $text entries (e.g. Abilities)
                    result.setdefault("Description", text)
        return result

    # -- File discovery --------------------------------------------------------

    def _find_json_files(self) -> list[Path]:
        if not self.bsdata_dir.is_dir():
            return []
        return sorted(self.bsdata_dir.glob("*.json"))

    def is_playable_faction(self, name: str) -> bool:
        if not name:
            return False
        if CRUCIBLE_RE.search(name):
            return False
        if name in SKIP_FACTIONS:
            return False
        if name.endswith("Library"):
            return False
        for prefix in SKIP_PREFIXES:
            if name.startswith(prefix):
                return False
        return True

    def list_factions(self) -> list[str]:
        factions: list[str] = []
        for path in self._find_json_files():
            data = self._load_json(path)
            if data is None:
                continue
            cat = self._get_catalogue(data)
            name = cat.get("name", "")
            if name and self.is_playable_faction(name):
                factions.append(name)
        return sorted(factions)

    def slug_to_faction(self, slug: str) -> str | None:
        for faction in self.list_factions():
            if slug.replace("-", " ").lower() in faction.lower() or \
               slug.lower().replace("-", " ") in faction.lower():
                return faction
        return None

    # -- Loading catalogues and linked roots -----------------------------------

    def _load_catalogue_by_name(self, name: str) -> dict | None:
        """Find and load a catalogue JSON file by its name field."""
        for path in self._find_json_files():
            data = self._load_json(path)
            if data is None:
                continue
            cat = self._get_catalogue(data)
            if cat.get("name", "").lower() == name.lower():
                return cat
        return None

    def _load_catalogue_roots(self, cat: dict) -> list[dict]:
        """
        Load linked catalogues marked importRootEntries=true.

        Returns list of catalogue dicts (including self as first entry).
        """
        roots: list[dict] = [cat]
        for link in cat.get("catalogueLinks", []):
            import_root = link.get("importRootEntries", False)
            name = link.get("name", "")
            if not import_root or not name:
                continue
            linked = self._load_catalogue_by_name(name)
            if linked is not None:
                roots.append(linked)
        return roots

    def _build_entry_index(self, roots: list[dict]) -> dict[str, dict]:
        """Build id -> entry index from all sharedSelectionEntries and sharedProfiles across roots."""
        index: dict[str, dict] = {}
        for root in roots:
            for entry in root.get("sharedSelectionEntries", []):
                eid = entry.get("id", "")
                if eid:
                    index[eid] = entry
            # Also index sharedProfiles (e.g. Invulnerable Save)
            for profile in root.get("sharedProfiles", []):
                pid = profile.get("id", "")
                if pid:
                    index[pid] = profile
        return index

    # -- Entry resolution ------------------------------------------------------

    def _resolve_entry(self, target_id: str, entry_index: dict[str, dict]) -> dict | None:
        """Resolve a targetId to a sharedSelectionEntry."""
        return entry_index.get(target_id)

    def _resolve_profiles(self, item: dict, entry_index: dict[str, dict],
                          depth: int = 0, _cache: dict[str, list[dict]] | None = None) -> list[dict]:
        """
        Recursively resolve weapon profiles from an item (selectionEntry,
        entryLink, etc.) following entryLinks and selectionEntries.
        """
        if depth > 5:
            return []

        # Cache by item id to avoid re-resolving shared entries
        item_id = item.get("id", "")
        if _cache is not None and item_id:
            cached = _cache.get(item_id)
            if cached is not None:
                return cached

        if _cache is None:
            _cache = {}

        results: list[dict] = []

        # Direct profiles on this item
        for p in item.get("profiles", []):
            ptype = p.get("typeName", "")
            if "Weapon" in ptype:
                results.append({
                    "name": p.get("name", ""),
                    "typeName": ptype,
                    "stats": self._get_chars_dict(p),
                })

        # Follow entryLinks
        for el in item.get("entryLinks", []):
            if el.get("hidden") == "true":
                continue
            tid = el.get("targetId", "")
            if not tid:
                continue
            target = self._resolve_entry(tid, entry_index)
            if target is not None:
                results.extend(self._resolve_profiles(target, entry_index, depth + 1))

        # Recurse into selectionEntries (sub-options)
        for sel in item.get("selectionEntries", []):
            if sel.get("hidden") == "true":
                continue
            results.extend(self._resolve_profiles(sel, entry_index, depth + 1, _cache))

        # Cache result by item id
        if item_id:
            _cache[item_id] = results
        return results

    # -- Unit extraction -------------------------------------------------------

    def _collect_entries(self, roots: list[dict]) -> list[dict]:
        """Collect all unique sharedSelectionEntries across all roots."""
        seen: set[str] = set()
        entries: list[dict] = []
        for root in roots:
            for entry in root.get("sharedSelectionEntries", []):
                eid = entry.get("id", "")
                if eid and eid not in seen:
                    seen.add(eid)
                    entries.append(entry)
        return entries

    def extract_units(self, cat: dict, faction_name: str,
                      include_legends: bool = False,
                      entry_index: dict[str, dict] | None = None) -> list[dict]:
        if entry_index is None:
            roots = self._load_catalogue_roots(cat)
            entry_index = self._build_entry_index(roots)
        else:
            roots = self._load_catalogue_roots(cat)

        units: list[dict] = []
        _profile_cache: dict[str, list[dict]] = {}

        entries = self._collect_entries(roots)
        for entry in entries:
            entry_type = entry.get("type", "")
            if entry_type not in ("model", "unit"):
                continue
            name = entry.get("name", "")
            hidden = entry.get("hidden", "false")
            if hidden == "true":
                continue
            if not include_legends and "[Legends]" in name:
                continue

            # -- Points --
            points: int | None = None
            for cost in entry.get("costs", []):
                if cost.get("name", "").lower() == "pts":
                    try:
                        points = int(cost.get("value", 0))
                    except (ValueError, TypeError):
                        points = None
                    break

            # -- Unit profile (stats) --
            stats: dict[str, str] = {}
            for p in entry.get("profiles", []):
                if p.get("typeName", "") == "Unit":
                    stats = self._get_chars_dict(p)
                    break

            # -- Keywords / category links --
            keywords: list[str] = []
            skip_categories = {"Configuration", "No Force Org Slot"}
            for cl in entry.get("categoryLinks", []):
                cname = cl.get("name", "")
                if cname and cname not in skip_categories:
                    keywords.append(cname)

            # -- Abilities --
            abilities: list[dict] = []
            for p in entry.get("profiles", []):
                if p.get("typeName", "") in ("Abilities", "Ability"):
                    chars = self._get_chars_dict(p)
                    desc = chars.get("Description", "")
                    abilities.append({
                        "name": p.get("name", ""),
                        "description": desc,
                    })

            # -- Resolve profile entryLinks (e.g. Invulnerable Save) --
            for el in entry.get("entryLinks", []):
                if el.get("hidden") == "true":
                    continue
                el_type = el.get("type", "")
                if el_type == "profile":
                    tid = el.get("targetId", "")
                    if tid:
                        target = self._resolve_entry(tid, entry_index)
                        if target is not None:
                            for p in target.get("profiles", []):
                                if p.get("typeName", "") in ("Abilities", "Ability"):
                                    chars = self._get_chars_dict(p)
                                    desc = chars.get("Description", "")
                                    abilities.append({
                                        "name": p.get("name", ""),
                                        "description": desc,
                                    })

            # -- Weapons --
            weapons: list[dict] = []

            # 1. Direct entryLinks on the unit
            for el in entry.get("entryLinks", []):
                if el.get("hidden") == "true":
                    continue
                el_type = el.get("type", "")
                if el_type == "selectionEntryGroup":
                    # Resolve group → its selectionEntries
                    tid = el.get("targetId", "")
                    if tid:
                        group = self._resolve_entry(tid, entry_index)
                        if group is not None:
                            for sel in group.get("selectionEntries", []):
                                if sel.get("hidden") == "true":
                                    continue
                                wprofs = self._resolve_profiles(sel, entry_index, _cache=_profile_cache)
                                if wprofs:
                                    weapons.append({
                                        "name": sel.get("name", ""),
                                        "profiles": wprofs,
                                    })
                elif el_type == "selectionEntry":
                    tid = el.get("targetId", "")
                    if tid:
                        target = self._resolve_entry(tid, entry_index)
                        if target is not None:
                            wprofs = self._resolve_profiles(target, entry_index, _cache=_profile_cache)
                            if wprofs:
                                weapons.append({
                                    "name": target.get("name", ""),
                                    "profiles": wprofs,
                                })

            # 2. SelectionEntryGroups → options with weapons
            for sg in entry.get("selectionEntryGroups", []):
                for sel in sg.get("selectionEntries", []):
                    if sel.get("hidden") == "true":
                        continue
                    wprofs = self._resolve_profiles(sel, entry_index, _cache=_profile_cache)
                    if wprofs:
                        weapons.append({
                            "name": sel.get("name", ""),
                            "profiles": wprofs,
                        })

                # entryLinks inside groups too
                for el in sg.get("entryLinks", []):
                    if el.get("hidden") == "true":
                        continue
                    tid = el.get("targetId", "")
                    if not tid:
                        continue
                    # Could be selectionEntry or selectionEntryGroup
                    target = self._resolve_entry(tid, entry_index)
                    if target is not None:
                        wprofs = self._resolve_profiles(target, entry_index, _cache=_profile_cache)
                        if wprofs:
                            weapons.append({
                                "name": target.get("name", ""),
                                "profiles": wprofs,
                            })

            # 3. Direct selectionEntries (units with inline weapons)
            for sel in entry.get("selectionEntries", []):
                if sel.get("hidden") == "true":
                    continue
                wprofs = self._resolve_profiles(sel, entry_index, _cache=_profile_cache)
                if wprofs:
                    weapons.append({
                        "name": sel.get("name", ""),
                        "profiles": wprofs,
                    })

            # -- Rules / infoLinks --
            rules: list[str] = []
            for il in entry.get("infoLinks", []):
                rname = il.get("name", "")
                hidden_r = il.get("hidden", "false")
                if hidden_r == "true" or not rname:
                    continue
                rules.append(rname)

            unit_entry: dict = {
                "name": name,
                "points": points,
                "stats": stats,
                "keywords": keywords,
                "abilities": abilities,
                "weapons": weapons,
                "rules": rules,
            }

            units.append(unit_entry)

        return units

    def query_faction(self, faction_name: str, include_legends: bool = False) -> dict | None:
        """Return full data for a faction, including linked catalogues."""
        for path in self._find_json_files():
            data = self._load_json(path)
            if data is None:
                continue
            cat = self._get_catalogue(data)
            name = cat.get("name", "")
            if name and name.lower() == faction_name.lower():
                roots = self._load_catalogue_roots(cat)
                entry_index = self._build_entry_index(roots)
                units = self.extract_units(cat, name, include_legends, entry_index)
                all_units = self.extract_units(cat, name, include_legends=True, entry_index=entry_index)
                legends_count = len(all_units) - len(units)
                return {
                    "name": name,
                    "id": cat.get("id", ""),
                    "revision": cat.get("revision", ""),
                    "units": units,
                    "legends_count": legends_count,
                }
        return None
