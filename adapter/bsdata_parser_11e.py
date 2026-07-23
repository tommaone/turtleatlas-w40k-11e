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
MULTIPLICITY_RE = re.compile(r'^(\d+)\s+(.+)$')


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

    # Manual overrides for slugs that don't fuzzy-match any BSData name
    _SLUG_OVERRIDES: dict[str, str] = {
        "imperial-agents": "Imperium - Agents of the Imperium",
        "chaos-titan-legions": "Chaos - Titanicus Traitoris",
        "titan-legions": "Imperium - Adeptus Titanicus",
    }

    def slug_to_faction(self, slug: str) -> str | None:
        """Map MFM slug to BSData faction name.

        Prefers exact matches and avoids 'Chaos' factions when slug doesn't contain 'chaos'.
        Handles apostrophes (T'au → tau), word order, and prefix stripping.
        """
        # Manual overrides first
        if slug in self._SLUG_OVERRIDES:
            target = self._SLUG_OVERRIDES[slug]
            for faction in self.list_factions():
                if faction.lower() == target.lower():
                    return faction
            return None  # override exists but BSData name not found

        def _norm(s: str) -> str:
            """Strip punctuation and lowercase for fuzzy matching."""
            return s.replace("'", "").replace("\u2019", "").replace("-", " ").lower()

        slug_words = _norm(slug)
        slug_set = set(slug_words.split())
        candidates = []
        for faction in self.list_factions():
            faction_norm = _norm(faction)
            # Check 1: slug is a substring of faction name (original behaviour)
            # Check 2: all slug words appear in faction name (handles word order)
            if slug_words in faction_norm or slug_set.issubset(set(faction_norm.split())):
                is_chaos = "chaos" in faction_norm
                slug_has_chaos = "chaos" in slug_words
                if is_chaos and not slug_has_chaos:
                    score = 2
                elif not is_chaos and slug_has_chaos:
                    score = 2
                else:
                    score = 0
                candidates.append((score, faction))
        if candidates:
            candidates.sort(key=lambda x: x[0])
            return candidates[0][1]
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

    def _load_catalogue_roots(self, cat: dict, include_linked: bool = False) -> list[dict]:
        """
        Load linked catalogues.

        Always includes importRootEntries=true catalogues.
        If include_linked=True, also loads all linked catalogues (needed for
        entryLinks resolution in factions like Drukhari that store units in
        a shared Library rather than sharedSelectionEntries).
        """
        roots: list[dict] = [cat]
        for link in cat.get("catalogueLinks", []):
            import_root = link.get("importRootEntries", False)
            name = link.get("name", "")
            if not name:
                continue
            if not import_root and not include_linked:
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

    def _build_parent_groups(self, obj, _parent_group: dict | None = None):
        """Recursively build index of entry_id → parent selectionEntryGroups.

        Used by level 4 weapon extraction to find weapons stored as siblings
        in the parent group rather than in the model entry itself.
        """
        if isinstance(obj, dict):
            if obj.get("type") == "selectionEntryGroup":
                _parent_group = obj
            # If this references a model (via selectionEntry or entryLink), record the parent
            if _parent_group:
                target_id = obj.get("targetId", "")
                entry_type = obj.get("type", "")
                if target_id and entry_type in ("selectionEntry", "entryLink"):
                    self._parent_groups.setdefault(target_id, []).append(_parent_group)
            for v in obj.values():
                self._build_parent_groups(v, _parent_group)
        elif isinstance(obj, list):
            for item in obj:
                self._build_parent_groups(item, _parent_group)

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
                # Strip leading unicode arrows (➤, ►, ▸) from BSData weapon names
                pname = p.get("name", "")
                for prefix in ("\u27A4", "\u25BA", "\u25B8"):
                    if pname.startswith(prefix):
                        pname = pname[len(prefix):].lstrip()
                results.append({
                    "name": pname,
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

    def _collect_entries(self, roots: list[dict],
                         entry_index: dict[str, dict] | None = None) -> list[dict]:
        """Collect all unique unit/model entries across all roots.

        Collects from:
        1. sharedSelectionEntries on root catalogues
        2. entryLinks on root catalogues (for factions like Drukhari that
           reference units via a shared Library instead of inline entries)
        """
        seen: set[str] = set()
        entries: list[dict] = []
        for root in roots:
            for entry in root.get("sharedSelectionEntries", []):
                eid = entry.get("id", "")
                if eid and eid not in seen:
                    seen.add(eid)
                    entries.append(entry)

            # Resolve entryLinks that reference unit/model selection entries
            if entry_index:
                for el in root.get("entryLinks", []):
                    tid = el.get("targetId", "")
                    if not tid or tid in seen:
                        continue
                    target = entry_index.get(tid)
                    if target is None:
                        continue
                    seen.add(tid)
                    entries.append(target)
        return entries

    def extract_units(self, cat: dict, faction_name: str,
                      include_legends: bool = False,
                      entry_index: dict[str, dict] | None = None) -> list[dict]:
        if entry_index is None:
            roots = self._load_catalogue_roots(cat, include_linked=True)
            entry_index = self._build_entry_index(roots)
        else:
            roots = self._load_catalogue_roots(cat)

        units: list[dict] = []
        _profile_cache: dict[str, list[dict]] = {}

        # Build parent_groups index: entry_id → list of parent selectionEntryGroups
        # Used by level 4 weapon extraction to find weapons stored as siblings
        self._parent_groups: dict[str, list[dict]] = {}
        for root in (roots if entry_index else self._load_catalogue_roots(cat, include_linked=True)):
            self._build_parent_groups(root)

        entries = self._collect_entries(roots, entry_index=entry_index)
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
            # BSData stores stats in different places depending on the faction:
            # 1. On model entries inside selectionEntryGroups (most infantry squads)
            # 2. On model entries inside selectionEntries (some factions like Aeldari)
            # 3. Directly on the entry as a "Unit" profile (vehicles, characters)
            # 4. In sharedProfiles, referenced via infoLinks → targetId
            # 5. Name-matching fallback to sharedProfiles
            stats: dict[str, str] = {}

            def _find_stats_in_entries(entries_list: list[dict]) -> dict[str, str]:
                """Walk a list of selection entries looking for model entries with Unit profiles."""
                for sel in entries_list:
                    if sel.get("type") != "model":
                        continue
                    for p in sel.get("profiles", []):
                        if p.get("typeName", "") == "Unit":
                            return self._get_chars_dict(p)
                return {}

            # 1. selectionEntryGroups → selectionEntries (type=model)
            for seg in entry.get("selectionEntryGroups", []):
                stats = _find_stats_in_entries(seg.get("selectionEntries", []))
                if stats:
                    break

            # 2. selectionEntries directly (type=model)
            if not stats:
                stats = _find_stats_in_entries(entry.get("selectionEntries", []))

            # 3. Direct "Unit" profile on the entry itself
            if not stats:
                for p in entry.get("profiles", []):
                    if p.get("typeName", "") == "Unit":
                        stats = self._get_chars_dict(p)
                        break

            # 4. Resolve from sharedProfiles via infoLinks
            if not stats:
                for seg in entry.get("selectionEntryGroups", []):
                    for sel in seg.get("selectionEntries", []):
                        for il in sel.get("infoLinks", []):
                            if il.get("type") == "profile":
                                tid = il.get("targetId", "")
                                if tid:
                                    target = self._resolve_entry(tid, entry_index)
                                    if target is not None and target.get("typeName") == "Unit":
                                        stats = self._get_chars_dict(target)
                                        break
                        if stats:
                            break
                    if stats:
                        break

            # 5. Name-matching fallback: match unit name to sharedProfile name
            if not stats and entry_index:
                unit_name_lower = name.lower().strip()
                best_match = None
                best_score = 0
                for eid, eobj in entry_index.items():
                    if eobj.get("typeName") != "Unit":
                        continue
                    pname = eobj.get("name", "").lower().strip()
                    # Exact match
                    if pname == unit_name_lower:
                        best_match = eobj
                        best_score = 100
                        break
                    # Singular match (strip trailing 's')
                    if pname == unit_name_lower.rstrip("s"):
                        best_match = eobj
                        best_score = 90
                        continue
                    # Profile name is contained in unit name
                    if len(pname) > 3 and pname in unit_name_lower:
                        score = len(pname)
                        if score > best_score:
                            best_match = eobj
                            best_score = score
                    # Leading words match (handles "Leman Russ Eradicator" → "Leman Russ Battle Tank")
                    pname_words = pname.split()
                    uname_words = unit_name_lower.split()
                    shared = 0
                    for pw, uw in zip(pname_words, uname_words):
                        if pw == uw:
                            shared += 1
                        else:
                            break
                    if shared >= 2 and shared > best_score:
                        best_match = eobj
                        best_score = shared
                if best_match and best_score >= 2:
                    stats = self._get_chars_dict(best_match)

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

            def _make_weapon(entry_name: str, profiles: list[dict]) -> dict:
                """Build a weapon dict, extracting multiplicity from BSData names.

                BSData encodes weapon counts in selection entry names like
                "2 Lascannons", "2 Hurricane Bolters", etc. The count is the
                leading number; the rest is the base weapon name.

                Only apply count when the entry has a single weapon profile
                (not mixed ranged+melee squad entries like "5 Plasma pistols").
                """
                count = 1
                name = entry_name
                m = MULTIPLICITY_RE.match(entry_name)
                if m and len(profiles) == 1:
                    count = int(m.group(1))
                    name = profiles[0].get("name", m.group(2))
                elif m and len(profiles) > 1:
                    # Multi-profile entries (e.g. "5 Plasma pistols" = squad option)
                    # Don't apply count — these are loadout choices, not weapon multiplicities
                    name = m.group(2)
                w = {"name": name, "profiles": profiles}
                if count > 1:
                    w["count"] = count
                return w

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
                                    weapons.append(_make_weapon(sel.get("name", ""), wprofs))
                elif el_type == "selectionEntry":
                    tid = el.get("targetId", "")
                    if tid:
                        target = self._resolve_entry(tid, entry_index)
                        if target is not None:
                            wprofs = self._resolve_profiles(target, entry_index, _cache=_profile_cache)
                            if wprofs:
                                weapons.append(_make_weapon(target.get("name", ""), wprofs))

            # 2. SelectionEntryGroups → options with weapons
            #    Recurse into nested groups (some weapons are 3+ levels deep,
            #    e.g. Bloodthirster: Wargear → Replace great axe → Axe and flail → profiles)
            def _extract_weapons_from_group(group: dict):
                for sel in group.get("selectionEntries", []):
                    if sel.get("hidden") == "true":
                        continue
                    wprofs = self._resolve_profiles(sel, entry_index, _cache=_profile_cache)
                    if wprofs:
                        weapons.append(_make_weapon(sel.get("name", ""), wprofs))
                    # Also recurse into nested selectionEntries
                    for sel2 in sel.get("selectionEntries", []):
                        wprofs2 = self._resolve_profiles(sel2, entry_index, _cache=_profile_cache)
                        if wprofs2:
                            weapons.append(_make_weapon(sel2.get("name", ""), wprofs2))
                    # Recurse into model's own selectionEntryGroups (e.g. Wargear groups
                    # with entryLinks to weapons, as in Deffkoptas, Carnifexes, etc.)
                    for model_sg in sel.get("selectionEntryGroups", []):
                        _extract_weapons_from_group(model_sg)

                for el in group.get("entryLinks", []):
                    if el.get("hidden") == "true":
                        continue
                    tid = el.get("targetId", "")
                    if not tid:
                        continue
                    target = self._resolve_entry(tid, entry_index)
                    if target is not None:
                        wprofs = self._resolve_profiles(target, entry_index, _cache=_profile_cache)
                        if wprofs:
                            weapons.append(_make_weapon(target.get("name", ""), wprofs))

                # Recurse into nested selectionEntryGroups
                for sub_group in group.get("selectionEntryGroups", []):
                    _extract_weapons_from_group(sub_group)

            for sg in entry.get("selectionEntryGroups", []):
                _extract_weapons_from_group(sg)

            # 2b. Recurse into model selectionEntries → their selectionEntryGroups
            #     Some units (e.g. Carnifexes, Wraithguard) have weapons defined
            #     inside model entries, not at the unit level.
            if not weapons:
                for sel in entry.get("selectionEntries", []):
                    if sel.get("type") == "model":
                        for sg in sel.get("selectionEntryGroups", []):
                            _extract_weapons_from_group(sg)

            # 3. Direct selectionEntries (units with inline weapons)
            for sel in entry.get("selectionEntries", []):
                if sel.get("hidden") == "true":
                    continue
                wprofs = self._resolve_profiles(sel, entry_index, _cache=_profile_cache)
                if wprofs:
                    weapons.append(_make_weapon(sel.get("name", ""), wprofs))

            # 4. Parent selectionEntryGroups — weapons stored as siblings
            #    Some models (e.g. Bloodthirster) have weapons defined as
            #    sibling entries in the parent group, not in the model itself.
            #    Find parent groups that reference this model and extract weapons.
            if not weapons:
                entry_id = entry.get("id", "")
                if entry_id:
                    for group in self._parent_groups.get(entry_id, []):
                        for sel in group.get("selections", []):
                            if sel.get("hidden") == "true":
                                continue
                            # Skip entries that reference other models
                            if sel.get("type") == "selectionEntry" and sel.get("targetId"):
                                continue
                            wprofs = self._resolve_profiles(sel, entry_index, _cache=_profile_cache)
                            if wprofs:
                                weapons.append(_make_weapon(sel.get("name", ""), wprofs))

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

    def build_multiplicity_index(self, cat: dict,
                                  entry_index: dict[str, dict] | None = None
                                  ) -> dict[str, list[dict]]:
        """Scan raw BSData for weapon multiplicity entries (e.g. "2 Lascannons").

        Returns dict mapping unit name → list of {count, weapon_name, target_id}.
        These are wargear OPTION entries (sponsons, etc.) that the normal
        weapon extraction misses because they live in parent selectionEntryGroups.
        """
        if entry_index is None:
            roots = self._load_catalogue_roots(cat, include_linked=True)
            entry_index = self._build_entry_index(roots)

        result: dict[str, list[dict]] = {}

        def _scan(obj, unit_name: str = ""):
            if isinstance(obj, dict):
                name = obj.get("name", "")
                # Track unit/model entries
                new_unit = unit_name
                if obj.get("type") in ("model", "unit") and name:
                    new_unit = name

                # Check for multiplicity pattern
                m = MULTIPLICITY_RE.match(name)
                if m and int(m.group(1)) <= 10:
                    count = int(m.group(1))
                    weapon_name = m.group(2)
                    # Find target weapon profile via entryLinks
                    target_ids = []
                    for el in obj.get("entryLinks", []):
                        tid = el.get("targetId", "")
                        if tid:
                            target_ids.append(tid)
                    # Also check selections for weapon references
                    for sel in obj.get("selections", []):
                        for el in sel.get("entryLinks", []):
                            tid = el.get("targetId", "")
                            if tid:
                                target_ids.append(tid)

                    if new_unit and count > 1:
                        result.setdefault(new_unit, []).append({
                            "count": count,
                            "weapon_name": weapon_name,
                            "target_ids": target_ids,
                        })

                for v in obj.values():
                    _scan(v, new_unit)
            elif isinstance(obj, list):
                for item in obj:
                    _scan(item, unit_name)

        _scan(cat)
        return result

    def query_faction(self, faction_name: str, include_legends: bool = False) -> dict | None:
        """Return full data for a faction, including linked catalogues."""
        for path in self._find_json_files():
            data = self._load_json(path)
            if data is None:
                continue
            cat = self._get_catalogue(data)
            name = cat.get("name", "")
            if name and name.lower() == faction_name.lower():
                roots = self._load_catalogue_roots(cat, include_linked=True)
                entry_index = self._build_entry_index(roots)
                units = self.extract_units(cat, name, include_legends, entry_index)
                # Deduplicate: truly identical entries (same name + same stats)
                # Different datasheets (e.g. "Gretchin" vs "Gretchin (Armageddon)") are NOT dupes
                seen = {}
                deduped = []
                for u in units:
                    stats_str = str(sorted((u.get("stats") or {}).items()))
                    key = f"{u['name'].lower().strip()}|{stats_str}"
                    if key in seen:
                        prev = seen[key]
                        if len(u.get("weapons", [])) > len(prev.get("weapons", [])):
                            deduped.remove(prev)
                            deduped.append(u)
                            seen[key] = u
                    else:
                        deduped.append(u)
                        seen[key] = u
                units = deduped
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
