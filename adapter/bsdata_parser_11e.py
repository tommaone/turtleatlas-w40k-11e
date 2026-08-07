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
        """Find and load a catalogue JSON file by its name field.
        
        First tries exact match, then falls back to word-level matching
        for BSData 11e catalogueLink name inconsistencies (e.g. 
        "Imperium - Space Marines" → "Imperium - Adeptus Astartes - Space Marines").
        """
        name_lower = name.lower()
        name_words = set(name_lower.replace("-", " ").split())
        # Exact match
        for path in self._find_json_files():
            data = self._load_json(path)
            if data is None:
                continue
            cat = self._get_catalogue(data)
            if cat.get("name", "").lower() == name_lower:
                return cat
        # Fuzzy match: all words from the link name must appear in the catalogue name
        # (in any order). This handles "Imperium - Space Marines" matching
        # "Imperium - Adeptus Astartes - Space Marines".
        best_match = None
        best_overlap = 0
        for path in self._find_json_files():
            data = self._load_json(path)
            if data is None:
                continue
            cat = self._get_catalogue(data)
            cat_name_lower = cat.get("name", "").lower()
            cat_words = set(cat_name_lower.replace("-", " ").split())
            overlap = len(name_words & cat_words)
            # All link words must be present, prefer more specific (shorter) matches
            if overlap >= len(name_words) and overlap > best_overlap:
                best_overlap = overlap
                best_match = cat
            # Also exact if link name is strictly a prefix/suffix/contained
            # after stripping non-alphanumeric chars
            name_clean = re.sub(r'[^a-z0-9\s]', '', name_lower)
            cat_clean = re.sub(r'[^a-z0-9\s]', '', cat_name_lower)
            if name_clean in cat_clean and overlap >= len(name_words):
                best_overlap = len(name_words) + 100  # prefer contained matches
                best_match = cat
        return best_match

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
            # Also index sharedSelectionEntryGroups — entryLinks can target a
            # shared group directly (e.g. War Walker's 'Heavy Weapons' group
            # linked from the model's Wargear group).
            for group in root.get("sharedSelectionEntryGroups", []):
                gid = group.get("id", "")
                if gid:
                    index[gid] = group
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

    _UNICODE_ARROWS = ("\u27A4", "\u25BA", "\u25B8", "\u279C")

    @staticmethod
    def _strip_arrow(name: str) -> str:
        """Strip leading unicode arrows from BSData entry/profile names."""
        for prefix in BSDataParser11e._UNICODE_ARROWS:
            if name.startswith(prefix):
                return name[len(prefix):].lstrip()
        return name

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
                pname = self._strip_arrow(p.get("name", ""))
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

        # Follow infoLinks that reference weapon profiles (type=profile)
        # BSData stores shared weapon profiles via infoLinks → targetId → profile entry
        # e.g. Boltgun upgrade → infoLink → Boltgun profile with characteristics
        for il in item.get("infoLinks", []):
            if il.get("hidden") == "true":
                continue
            if il.get("type") != "profile":
                continue
            tid = il.get("targetId", "")
            if not tid:
                continue
            target = self._resolve_entry(tid, entry_index)
            if target is not None and target.get("type") is None:
                # It's a profile entry — extract characteristics directly
                tname = target.get("name", "")
                ttype = target.get("typeName", "")
                if "Weapon" in ttype or "weapon" in ttype.lower():
                    results.append({
                        "name": tname,
                        "typeName": ttype,
                        "stats": self._get_chars_dict(target),
                    })

        # Recurse into selectionEntries (sub-options)
        for sel in item.get("selectionEntries", []):
            if sel.get("hidden") == "true":
                continue
            results.extend(self._resolve_profiles(sel, entry_index, depth + 1, _cache))

        # Recurse into selectionEntryGroups (sub-model wargear choice groups).
        # BSData stores a model's weapon choices in two equivalent ways:
        #   (a) direct selectionEntries (e.g. TS Aspiring Sorcerer: Force weapon
        #       + Malefic Curse as direct children)
        #   (b) inside a "Wargear" selectionEntryGroup, min/max 1 (e.g. CSM
        #       Aspiring Sorcerer: same weapons as a choice group)
        # Surfacing both as a merged weapon group named after the model matches
        # the (a) behaviour and lets the catalog resolve the sergeant's weapons
        # cross-faction. Non-weapon profiles are filtered by the "Weapon"
        # typeName check above, so upgrade-only choice groups do not pollute.
        for sg in item.get("selectionEntryGroups", []):
            results.extend(self._resolve_profiles(sg, entry_index, depth + 1, _cache))

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
            roots = self._load_catalogue_roots(cat, include_linked=True)

        units: list[dict] = []
        _profile_cache: dict[str, list[dict]] = {}

        # Build parent_groups index: entry_id → list of parent selectionEntryGroups
        # Used by level 4 weapon extraction to find weapons stored as siblings
        self._parent_groups: dict[str, list[dict]] = {}
        for root in roots:
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

            def _find_stats_in_entries(entries_list: list[dict],
                                       unit_name: str = "",
                                       _entry_has_info_links: bool = False) -> dict[str, str]:
                """Walk a list of selection entries looking for model entries with Unit profiles.
                
                When `unit_name` is provided, prefers profiles whose name matches
                the unit name over profiles on wargear/upgrade models
                (e.g. "Serpent's Scale Platform" within "Storm Guardians").
                
                `_entry_has_info_links`: set to True if any model in the parent unit
                uses infoLinks (11e pattern). When True, non-matching models are
                rejected since the correct profile is likely a shared profile (step 4).
                """
                matches: list[dict[str, str]] = []
                non_matches: list[dict[str, str]] = []
                unit_lower = unit_name.lower().strip()
                unit_words = set(unit_lower.split())
                
                for sel in entries_list:
                    if sel.get("type") != "model":
                        continue
                    for p in sel.get("profiles", []):
                        if p.get("typeName", "") == "Unit":
                            stats = self._get_chars_dict(p)
                            if not unit_name:
                                return stats
                            pname = p.get("name", sel.get("name", "")).lower().strip()
                            # Perfect match
                            if pname == unit_lower:
                                return stats
                            # Singular/plural: strip trailing s/z, compare stems
                            _stem = lambda s: s.rstrip("sz")
                            if _stem(pname) == _stem(unit_lower):
                                return stats  # "Boy" ↔ "Boyz"
                            # Word overlap check (with possessive 's stripping)
                            pname_words = set(pname.split())
                            # Handle both straight ' and curly ’ apostrophes in possessives
                            _strip_s = lambda w: w[:-2] if w.endswith(("'s", "\u2019s")) else w
                            overlap = {_strip_s(w) for w in unit_words} & {_strip_s(w) for w in pname_words}
                            if overlap:
                                matches.append(stats)
                            else:
                                non_matches.append(stats)
                
                if matches:
                    return matches[0]
                # No name match found:
                # - If the parent unit has infoLinks elsewhere → defer to step 4
                #   (handles "Serpent's Platform" in "Storm Guardians")
                # - If no infoLinks exist at all → use first non-matching model
                #   (handles "Sword Brother" in "Crusader Squad")
                if _entry_has_info_links:
                    return {}
                return non_matches[0] if non_matches else {}

            # Does any model in this unit use profile-type infoLinks? If so, the 11e
            # pattern is in use and step 4 (shared profile via infoLink) takes
            # priority over direct profiles on non-matching model entries.
            # infoLinks of type "rule" or "infoGroup" are ability references and
            # don't indicate the shared-profile pattern (e.g. "Deadly Demise" on
            # Szarekh in The Silent King).
            _entry_any_info_links = any(
                any(il.get("type") == "profile" for il in (sel.get("infoLinks") or []))
                for seg in entry.get("selectionEntryGroups", [])
                for sel in seg.get("selectionEntries", [])
                if sel.get("type") == "model"
            ) or any(
                any(il.get("type") == "profile" for il in (sel.get("infoLinks") or []))
                for sel in entry.get("selectionEntries", [])
                if sel.get("type") == "model"
            )

            # 1. selectionEntryGroups → selectionEntries (type=model)
            for seg in entry.get("selectionEntryGroups", []):
                stats = _find_stats_in_entries(seg.get("selectionEntries", []),
                                               unit_name=name,
                                               _entry_has_info_links=_entry_any_info_links)
                if stats:
                    break

            # 2. selectionEntries directly (type=model)
            if not stats:
                stats = _find_stats_in_entries(entry.get("selectionEntries", []),
                                               unit_name=name,
                                               _entry_has_info_links=_entry_any_info_links)

            # 3. Direct "Unit" profile on the entry itself
            if not stats:
                for p in entry.get("profiles", []):
                    if p.get("typeName", "") == "Unit":
                        stats = self._get_chars_dict(p)
                        break

            # 3b. Unit profile on selectionEntryGroups* directly
            #     (BSData pattern: Wulfen, Victrix Honour Guard store Unit profile
            #      on the selectionEntryGroup itself, not on child model entries)
            if not stats:
                for seg in entry.get("selectionEntryGroups", []):
                    for p in seg.get("profiles", []):
                        if p.get("typeName", "") == "Unit":
                            stats = self._get_chars_dict(p)
                            break
                    if stats:
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

            # 5. Follow upgrade entryLinks to find stats in 11e BSData.
            #    11e pattern: unit → selectionEntryGroup → upgrade entry → entryLink
            #    → model entry → infoLink → Unit profile (in sharedProfiles).
            if not stats:
                for seg in entry.get("selectionEntryGroups", []):
                    for sel in seg.get("selectionEntries", []):
                        if sel.get("type") != "upgrade":
                            continue
                        for el in sel.get("entryLinks", []):
                            if el.get("type") != "selectionEntry":
                                continue
                            target = self._resolve_entry(el.get("targetId", ""), entry_index) if entry_index else None
                            if not target:
                                continue
                            # Check direct profiles on the model entry
                            for p in target.get("profiles", []):
                                if p.get("typeName", "") == "Unit":
                                    stats = self._get_chars_dict(p)
                                    break
                            if stats:
                                break
                            # Follow infoLinks from the model entry
                            for il in target.get("infoLinks", []):
                                if il.get("type") == "profile":
                                    profile_target = self._resolve_entry(il.get("targetId", ""), entry_index) if entry_index else None
                                    if profile_target and profile_target.get("typeName") == "Unit":
                                        stats = self._get_chars_dict(profile_target)
                                        break
                            if stats:
                                break
                        if stats:
                            break
                    if stats:
                        break

            # 6. Name-matching fallback: match unit name to sharedProfile name
            if not stats and entry_index:
                unit_name_lower = name.lower().strip()
                unit_words = set(unit_name_lower.split())
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
                    # Profile name words are a subset of unit name words
                    # (handles "Shock Trooper" ⊂ "Cadian Shock Troops")
                    pname_words_set = set(pname.split())
                    if len(pname_words_set) >= 2:
                        overlap = len(pname_words_set & unit_words)
                        if overlap >= 2:
                            score = 80 + overlap
                            if score > best_score:
                                best_match = eobj
                                best_score = score
                    # Best single-word overlap: longest shared word wins
                    # (handles "Sister Repentia" ~ "Repentia Squad")
                    if not best_match or best_score < 60:
                        shared_words = pname_words_set & unit_words
                        generic = {"squad", "unit", "team", "group", "warband", "pack", "brood", "cult"}
                        meaningful = [w for w in shared_words if len(w) >= 4 and w not in generic]
                        if meaningful:
                            score = 50 + max(len(w) for w in meaningful)
                            if score > best_score:
                                best_match = eobj
                                best_score = score
                    # Profile name (minus trailing 's') matches unit name (handles "Vypers" ~ "Vyper")
                    if pname.rstrip("s") == unit_name_lower or unit_name_lower.rstrip("s") == pname:
                        score = 70
                        if score > best_score:
                            best_match = eobj
                            best_score = score
                    # Leading words match (handles "Leman Russ Eradicator" → "Leman Russ Battle Tank")
                    pname_words_list = pname.split()
                    uname_words_list = unit_name_lower.split()
                    shared = 0
                    for pw, uw in zip(pname_words_list, uname_words_list):
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

    # -- Wargear constraint extraction ----------------------------------------

    @staticmethod
    def _weapon_category(entry: dict) -> str:
        """Classify a weapon entry as 'ranged', 'melee', or 'ability' based on profiles."""
        for p in entry.get("profiles", []):
            ptype = p.get("typeName", "")
            if "Ranged" in ptype:
                return "ranged"
            if "Melee" in ptype:
                return "melee"
        return "ability"

    @staticmethod
    def _weapon_categories(entry: dict) -> set[str]:
        """ALL weapon categories present in an entry's inline profiles.

        Dual-profile weapons (Singing Spear: Ranged + Melee, Chainsabres:
        Melee + Ranged) return BOTH categories. The first-profile convention
        only applies when a weapon is single-category — a Warlock with a
        Singing Spear ALWAYS has the spear's melee profile too.
        """
        cats: set[str] = set()
        for p in entry.get("profiles", []):
            ptype = p.get("typeName", "")
            if "Ranged" in ptype:
                cats.add("ranged")
            elif "Melee" in ptype:
                cats.add("melee")
        return cats

    def _resolve_entry_category(self, entry: dict, entry_index: dict[str, dict]) -> str:
        """Categorize a wargear entry as 'ranged'/'melee'/'ability', resolving
        infoLink profile references (11e pattern: the weapon profile lives in
        sharedProfiles and the SE carries only an infoLink of type=profile,
        e.g. Harlequin's Blade on Troupe players).

        Falls back to _weapon_category for entries with inline profiles.
        """
        cat = self._weapon_category(entry)
        if cat != "ability":
            return cat
        for il in entry.get("infoLinks", []) or []:
            if il.get("type") != "profile":
                continue
            tid = il.get("targetId", "")
            target = entry_index.get(tid) if tid else None
            if target is None:
                continue
            ptype = target.get("typeName", "")
            if "Ranged" in ptype:
                return "ranged"
            if "Melee" in ptype:
                return "melee"
        return "ability"

    def _resolve_entry_categories(self, entry: dict, entry_index: dict[str, dict]) -> set[str]:
        """ALL categories of a wargear entry, resolving infoLink profile refs.

        Dual-profile entries (Singing Spear, Chainsabres) return BOTH
        categories so callers emit the weapon in both the ranged and melee
        lists — the loader resolves the correct profile per list context.
        """
        cats = self._weapon_categories(entry)
        if cats:
            return cats
        for il in entry.get("infoLinks", []) or []:
            if il.get("type") != "profile":
                continue
            tid = il.get("targetId", "")
            target = entry_index.get(tid) if tid else None
            if target is None:
                continue
            ptype = target.get("typeName", "")
            if "Ranged" in ptype:
                cats.add("ranged")
            elif "Melee" in ptype:
                cats.add("melee")
        return cats

    @staticmethod
    def _weapon_category_deep(entry: dict, depth: int = 0) -> str:
        """Classify an entry, walking nested selectionEntries for the profile.

        Choice wrappers (e.g. '2 Starcannons') are upgrade-type entries with no
        own profile; the actual weapon profile lives on a nested selectionEntry
        ('Starcannon'). Walk down until a profile is found or depth is exhausted.
        """
        if depth > 4:
            return "ability"
        cat = BSDataParser11e._weapon_category(entry)
        if cat != "ability":
            return cat
        for se in entry.get("selectionEntries", []):
            if se.get("hidden") == "true":
                continue
            cat = BSDataParser11e._weapon_category_deep(se, depth + 1)
            if cat != "ability":
                return cat
        return "ability"

    def _resolve_choice_option(self, se: dict) -> tuple[str, int]:
        """Resolve a choice-group option to (catalog weapon name, count).

        Choice wrappers display a count prefix ('2 Starcannons', 'Two magma
        cutters') and nest the real weapon one level down ('Starcannon'). Return
        the nested weapon's name so the engine can resolve it, and the count so
        multi-weapon options (2× Starcannon) keep their multiplicity.

        If the option itself carries a weapon profile, its display name is used
        (a profile name like '➤ Missile Launcher - Starshot' is a BSData mode
        label, not a catalog weapon name — the catalog key is 'Missile Launcher').
        """
        import re
        raw = se.get("name", "")
        name = self._strip_arrow(raw)
        count = 1
        m = re.match(r'^(\d+)\s+(.*)$', name)
        if m:
            count = int(m.group(1))
            name = m.group(2)
        elif name.lower().startswith("two "):
            count = 2
            name = name[4:]
        # Only descend to nested selectionEntries when the option has no own
        # profile (e.g. '2 Starcannons' wrapper). Otherwise keep its display name.
        if self._weapon_category(se) == "ability":
            def find_nested_name(entry: dict, depth: int = 0) -> str | None:
                if depth > 4:
                    return None
                for sub in entry.get("selectionEntries", []):
                    if sub.get("hidden") == "true":
                        continue
                    if self._weapon_category(sub) != "ability":
                        sub_name = self._strip_arrow(sub.get("name", ""))
                        if sub_name:
                            return sub_name
                    found = find_nested_name(sub, depth + 1)
                    if found:
                        return found
                return None
            nested = find_nested_name(se)
            if nested:
                name = nested
        # Strip mode suffixes so the name matches the merged catalog
        # ('Missile Launcher - Starshot' → 'Missile Launcher').
        name = self._strip_mode_suffix(name)
        return name, count

    @staticmethod
    def _strip_mode_suffix(name: str) -> str:
        """Strip firing-mode suffixes from weapon names (e.g. '- Starshot')."""
        for suffix in (" - starshot", " - sunburst", " - supercharge",
                       " - standard", " - focused witchfire", " - witchfire",
                       " - focused", " - sweep", " - strike"):
            if name.lower().endswith(suffix):
                return name[:-len(suffix)]
        return name

    def _get_choice_type(self, choice_name: str,
                         group: dict,
                         entry_index: dict[str, dict]) -> str:
        """Determine weapon type ('ranged'/'melee') for a choice in a group.
        
        Checks entryLinks (by targetId lookup) then selectionEntries (by direct
        or nested profile). Falls back to group-level classification (old
        heuristic) if not found.
        """
        # Check entryLinks first — compare both raw and arrow-stripped names
        for el in group.get("entryLinks", []):
            el_name = self._strip_arrow(el.get("name", ""))
            if el_name != choice_name or el.get("hidden") == "true":
                continue
            tid = el.get("targetId", "")
            if tid:
                target = entry_index.get(tid)
                if target:
                    cat = self._weapon_category_deep(target)
                    if cat != "ability":
                        return cat
            # entryLink itself might have profiles
            cat = self._weapon_category_deep(el)
            if cat != "ability":
                return cat
            break
        
        # Check selectionEntries — compare raw, arrow-stripped, AND
        # count-stripped names. Choice wrappers ('2 Bright Lances') resolve
        # to the base name ('Bright Lances') via _resolve_choice_option, so
        # the raw SE name never matches the stripped choice name directly.
        for se in group.get("selectionEntries", []):
            if se.get("hidden") == "true":
                continue
            se_name = self._strip_arrow(se.get("name", ""))
            resolved_name, _ = self._resolve_choice_option(se)
            if se_name != choice_name and resolved_name != choice_name:
                continue
            cat = self._weapon_category_deep(se)
            if cat != "ability":
                return cat
            break
        
        # Fallback: use group name heuristic
        gname = (group.get("name") or "").lower()
        melee_kw = {"melee", "close combat", "choppa", "axe", "sword",
                    "fist", "claw", "hammer", "blade", "power"}
        ranged_kw = {"pistol", "gun", "bolter", "rifle", "cannon",
                     "launcher", "flamer", "melta", "plasma",
                     "storm bolter", "combi", "ranged", "lance"}
        if any(kw in gname for kw in melee_kw):
            return "melee"
        if any(kw in gname for kw in ranged_kw):
            return "ranged"
        
        # Last fallback: classify from the choice name itself (e.g. '2 Starcannons')
        cname = (choice_name or "").lower()
        if any(kw in cname for kw in melee_kw):
            return "melee"
        if any(kw in cname for kw in ranged_kw):
            return "ranged"

        return "ability"  # skip — not resolvable to a weapon profile

    @staticmethod
    def _is_melee_choice_group(group: dict) -> bool:
        """Heuristic: does this nested group contain melee weapons?

        Checks the group name for melee keywords, or examines the entry targets.
        """
        gname = (group.get("name") or "").lower()
        melee_keywords = {"melee", "close combat", "choppa", "axe", "sword",
                          "fist", "claw", "hammer", "blade", "power"}
        if any(kw in gname for kw in melee_keywords):
            return True
        # Fallback: check if default entry has Melee Weapons profile
        default_id = group.get("defaultSelectionEntryId", "")
        for el in group.get("entryLinks", []):
            if el.get("id") == default_id or el.get("name", "").lower() in gname:
                # Can't resolve profiles here, rely on name heuristic
                break
        return False

    @staticmethod
    def _is_ranged_choice_group(group: dict) -> bool:
        """Heuristic: does this nested group contain ranged weapons?"""
        gname = (group.get("name") or "").lower()
        ranged_keywords = {"pistol", "gun", "bolter", "rifle", "cannon",
                           "launcher", "flamer", "melta", "plasma",
                           "storm bolter", "psycannon", "psilencer",
                           "incinerator", "combi", "ranged", "lance"}
        if any(kw in gname for kw in ranged_keywords):
            return True
        return False

    @staticmethod
    def _get_selection_count(entry: dict) -> int:
        """Get the number of times a selection should be counted.
        
        BSData encodes weapon count in constraints (min selections):
        min=2, max=2 means the weapon is selected 2 times (e.g. 2× cannons).
        """
        for c in entry.get("constraints", []):
            if c.get("field") == "selections" and c.get("type") == "min":
                val = c.get("value", 1)
                if val > 1:
                    return val
        return 1

    def _resolve_shared_group_target(self, el: dict, entry_index: dict[str, dict]) -> dict | None:
        """If an entryLink targets a shared selectionEntryGroup, return that group."""
        if el.get("hidden") == "true":
            return None
        tid = el.get("targetId", "")
        if not tid:
            return None
        target = entry_index.get(tid)
        # Shared selectionEntryGroups carry no "type" field (selectionEntries
        # always have one: upgrade/model/unit). A group exposes selectionEntries
        # and/or entryLinks at its own level.
        if target is not None and "type" not in target and (
                target.get("selectionEntries") is not None
                or target.get("entryLinks") is not None):
            return target
        return None

    def _collect_virtual_groups(self, entry_links: list[dict],
                                entry_index: dict[str, dict]) -> list[dict]:
        """Turn entryLinks that point at shared selectionEntryGroups into choice groups.

        Some models link a whole choice group (e.g. War Walker 'Heavy Weapons')
        rather than physically nesting it. The linked group's own options
        (selectionEntries + entryLinks) become the choice options.
        """
        virtual: list[dict] = []
        for el in entry_links or []:
            group = self._resolve_shared_group_target(el, entry_index)
            if group is not None:
                virtual.append({
                    "name": self._strip_arrow(el.get("name", "")),
                    "entryLinks": group.get("entryLinks", []),
                    "selectionEntries": group.get("selectionEntries", []),
                    "constraints": group.get("constraints", []),
                })
        return virtual

    def _is_build_package(self, se: dict, entry_index: dict[str, dict]) -> bool:
        """True if a wargear selectionEntry is a NAMED build package (Pattern 1).

        Build packages (e.g. 'Bolt Pistol, Master-crafted Bolter, Melee Weapon'
        on a Captain) carry their weapons via entryLinks to real weapon targets,
        or via nested selectionEntryGroups that contain weapons.

        Fixed weapons (Wraithbone hull, Pulse Laser, etc.) also carry entryLinks,
        but those point at crusade/system groups ('Weapon Modifications') that
        resolve to NO weapon profiles. Treating those as build packages wrongly
        flattens every vehicle into an all-fixed default build (the Vyper bug).
        """
        # entryLinks that resolve to weapon profiles → build package
        for el in se.get("entryLinks", []):
            if el.get("hidden") == "true":
                continue
            tid = el.get("targetId", "")
            if not tid:
                continue
            target = self._resolve_entry(tid, entry_index)
            if target is None:
                continue
            if self._resolve_profiles(target, entry_index):
                return True
            # entryLink to a shared selectionEntryGroup containing weapons →
            # also a build package (e.g. a model linking its whole weapon group).
            if "type" not in target and (
                    target.get("selectionEntries") is not None
                    or target.get("entryLinks") is not None):
                for sel in target.get("selectionEntries", []):
                    if sel.get("hidden") == "true":
                        continue
                    if self._resolve_profiles(sel, entry_index):
                        return True
                for el2 in target.get("entryLinks", []):
                    if el2.get("hidden") == "true":
                        continue
                    t2 = self._resolve_entry(el2.get("targetId", ""), entry_index)
                    if t2 is not None and self._resolve_profiles(t2, entry_index):
                        return True
        # nested selectionEntryGroups containing weapons → build package
        for sg in se.get("selectionEntryGroups", []):
            for sel in sg.get("selectionEntries", []):
                if sel.get("hidden") == "true":
                    continue
                if self._resolve_profiles(sel, entry_index):
                    return True
            for el in sg.get("entryLinks", []):
                if el.get("hidden") == "true":
                    continue
                tid = el.get("targetId", "")
                if not tid:
                    continue
                target = self._resolve_entry(tid, entry_index)
                if target is not None and self._resolve_profiles(target, entry_index):
                    return True
        return False

    def _classify_build_items(self, entry_links: list[dict], selection_entries: list[dict],
                               nested_groups: list[dict], entry_index: dict[str, dict],
                               parent_group_name: str = "") -> dict:
        """Classify items in a build into ranged/melee fixed and choice lists.

        Returns: {fixed_ranged, fixed_melee, ranged_choices, melee_choices,
                  max_ranged, max_melee}
        max_ranged/max_melee indicate how many weapons can be picked from
        the combined choice lists (from BSData group max constraints).
        """
        fixed_ranged: list[str] = []
        fixed_melee: list[str] = []
        ranged_choices: list[list[str]] = []
        melee_choices: list[list[str]] = []
        max_ranged: int | None = None
        max_melee: int | None = None

        # Direct entryLinks on this build → fixed weapons
        for el in entry_links:
            if el.get("hidden") == "true":
                continue
            el_type = el.get("type", "")
            if el_type == "selectionEntry":
                tid = el.get("targetId", "")
                name = self._strip_arrow(el.get("name", ""))
                if tid:
                    target = entry_index.get(tid)
                    if target is not None:
                        cat = self._weapon_category(target)
                        if cat == "ranged":
                            fixed_ranged.append(name)
                        elif cat == "melee":
                            fixed_melee.append(name)
                        # "ability" entries (e.g. Relic Shield) → skip
                elif name:
                    # No targetId, use name heuristic
                    fixed_ranged.append(name)

        # selectionEntries on this build → inline weapons (e.g. Twin slugga)
        for se in selection_entries:
            if se.get("hidden") == "true":
                continue
            cat = self._weapon_category(se)
            count = self._get_selection_count(se)
            name = self._strip_arrow(se.get("name", ""))
            if cat == "ranged":
                fixed_ranged.extend([name] * count)
            elif cat == "melee":
                fixed_melee.extend([name] * count)

        # Nested selectionEntryGroups → choice groups. EntryLinks that point at
        # shared selectionEntryGroups (e.g. War Walker 'Heavy Weapons') count as
        # choice groups too — collect them as virtual groups alongside any
        # physically nested groups.
        virtual_groups = self._collect_virtual_groups(entry_links, entry_index)
        for group in nested_groups:
            virtual_groups.extend(
                self._collect_virtual_groups(group.get("entryLinks", []), entry_index))
        all_nested_groups = list(nested_groups) + virtual_groups

        for group in all_nested_groups:
            choices = []
            # entryLinks within the group are the options
            for el in group.get("entryLinks", []):
                if el.get("hidden") == "true":
                    continue
                # Links to shared selectionEntryGroups are separate choice
                # groups (collected above), not options of this group.
                if self._resolve_shared_group_target(el, entry_index) is not None:
                    continue
                ename = self._strip_arrow(el.get("name", ""))
                if ename:
                    choices.append(ename)
            # selectionEntries within the group are also options
            for se in group.get("selectionEntries", []):
                if se.get("hidden") == "true":
                    continue
                ename, _count = self._resolve_choice_option(se)
                if ename:
                    choices.append(ename)

            if not choices:
                continue

            # Drop ability-only options (e.g. Scattershield) — they have no
            # weapon profile and would fail engine resolution. Mirrors the
            # type filter applied to the slots format below.
            choices = [c for c in choices
                       if self._get_choice_type(c, group, entry_index) != "ability"]
            if not choices:
                continue

            # Extract max constraint from this group
            group_max = None
            for c in group.get("constraints", []):
                if c.get("field") == "selections" and c.get("type") == "max":
                    group_max = c.get("value")

            # Classify the group as ranged or melee
            # NOTE: Each group = one independent SLOT. max_ranged/max_melee
            # are NOT set from group constraints — groups use product semantics
            # (pick 1 from each group). Global max is only relevant for
            # cross-slot constraints, which are handled separately.
            gname = (group.get("name") or "").lower()
            if self._is_melee_choice_group(group):
                melee_choices.append(choices)
            elif self._is_ranged_choice_group(group):
                ranged_choices.append(choices)
            else:
                # Ambiguous — classify by first choice's profile if available.
                # Use _get_choice_type (checks BOTH entryLinks and inline
                # selectionEntries) so groups whose options are inline weapons
                # (e.g. Bright Lance Replacement on a Vyper) are not dropped.
                first_name = choices[0] if choices else ""
                cat = self._get_choice_type(first_name, group, entry_index)
                if cat == "ranged":
                    ranged_choices.append(choices)
                elif cat == "melee":
                    melee_choices.append(choices)
                # "ability" groups → skip (e.g. optional wargear that's not a weapon)

        # Build new format: untyped slots + typed choices
        slots: list[dict] = []
        for group in all_nested_groups:
            gname = group.get("name", "")
            choices_typed: list[dict] = []
            for el in group.get("entryLinks", []):
                if el.get("hidden") == "true" or not el.get("name"):
                    continue
                if self._resolve_shared_group_target(el, entry_index) is not None:
                    continue
                ename = self._strip_arrow(el["name"])
                wtype = self._get_choice_type(ename, group, entry_index)
                if wtype != "ability":
                    choices_typed.append({"name": ename, "type": wtype})
            for se in group.get("selectionEntries", []):
                if se.get("hidden") == "true" or not se.get("name"):
                    continue
                ename, count = self._resolve_choice_option(se)
                wtype = self._get_choice_type(ename, group, entry_index)
                if wtype == "ability":
                    # Nested wrapper may carry the profile; recheck against the raw entry.
                    wtype = self._weapon_category_deep(se)
                if wtype != "ability":
                    choice = {"name": ename, "type": wtype}
                    if count > 1:
                        choice["count"] = count
                    choices_typed.append(choice)
            if choices_typed:
                slots.append({"name": gname, "choices": choices_typed})
        
        # Build typed fixed list from old fixed_ranged/fixed_melee
        fixed = []
        fixed.extend({"name": n, "type": "ranged"} for n in fixed_ranged)
        fixed.extend({"name": n, "type": "melee"} for n in fixed_melee)
        
        return {
            "fixed_ranged": fixed_ranged,
            "fixed_melee": fixed_melee,
            "ranged_choices": ranged_choices,
            "melee_choices": melee_choices,
            "max_ranged": max_ranged,
            "max_melee": max_melee,
            # New format
            "fixed": fixed,
            "slots": slots,
                }

    def _resolve_faction_catalogue(self, faction_name: str) -> dict | None:
        """Find a BSData catalogue by exact name, then fuzzy (slug/display) match.

        BSData catalogue names are prefixed (e.g. "Imperium - Grey Knights") while
        callers commonly pass the short display/slug form ("Grey Knights",
        "grey-knights"). Fall back to slug_to_faction's fuzzy resolver.
        """
        target = faction_name
        for path in self._find_json_files():
            data = self._load_json(path)
            if data is None:
                continue
            c = self._get_catalogue(data)
            if c.get("name", "").lower() == target.lower():
                return c
        resolved = self.slug_to_faction(target)
        if resolved:
            for path in self._find_json_files():
                data = self._load_json(path)
                if data is None:
                    continue
                c = self._get_catalogue(data)
                if c.get("name", "").lower() == resolved.lower():
                    return c
        return None

    @staticmethod
    def _norm_name(s: str) -> str:
        return re.sub(r'[^a-z0-9]', '', (s or "").lower())

    def _load_merged_weapon_map(self, faction_name: str) -> dict[str, dict]:
        """Build normalized-unit-name -> {name, fixed_ranged, fixed_melee}.

        Reads the merged data file (`data/merged/<faction>.json`) which already
        contains the fully-resolved weapon list per unit (profiles with
        typeName "Ranged Weapons" / "Melee Weapons"). The merged list is treated
        as the ground-truth FIXED weapon set for augmentation.
        """
        mdir = Path(__file__).resolve().parent.parent / "data" / "merged"
        if not mdir.is_dir():
            return {}
        target = self._norm_name(faction_name)
        merged_data: dict | None = None
        # First pass: exact faction/slug match.
        for path in sorted(mdir.glob("*.json")):
            d = self._load_json(path)
            if not d or "units" not in d:
                continue
            if (self._norm_name(d.get("faction", "")) == target
                    or self._norm_name(d.get("slug", "")) == target):
                merged_data = d
                break
        # Second pass: substring fallback (handles "Imperium - Grey Knights"
        # -> grey-knights.json where display name is "Grey Knights").
        if merged_data is None:
            for path in sorted(mdir.glob("*.json")):
                d = self._load_json(path)
                if not d or "units" not in d:
                    continue
                fac = self._norm_name(d.get("faction", ""))
                slug = self._norm_name(d.get("slug", ""))
                if (target and (target in fac or target in slug
                                or fac in target or slug in target)):
                    merged_data = d
                    break
        if merged_data is None:
            return {}
        out: dict[str, dict] = {}
        for u in merged_data.get("units", []):
            weapons = (u.get("profile") or {}).get("weapons", [])
            if not weapons:
                continue
            fr: list[str] = []
            fm: list[str] = []
            seen_profiles: set[tuple[str, str]] = set()
            for w in weapons:
                wname = w.get("name", "")
                profs = w.get("profiles", [])
                if not profs:
                    continue
                tname = profs[0].get("typeName", "")
                pname = profs[0].get("name", "")
                # Dedupe by PRIMARY profile signature. Model-level entries
                # (e.g. a Vyper model's own weapon entry) duplicate the hull
                # melee profile under the model's name — treat as the same
                # weapon so the augment subset check can match it to BSData.
                sig = (self._norm_name(pname or wname), tname)
                if sig in seen_profiles:
                    continue
                seen_profiles.add(sig)
                if tname == "Melee Weapons":
                    fm.append(wname)
                else:
                    # Default to ranged; covers unknown/missing typeName too.
                    fr.append(wname)
            if not (fr or fm):
                continue
            out[self._norm_name(u.get("name", ""))] = {
                "name": u.get("name", ""),
                "fixed_ranged": fr,
                "fixed_melee": fm,
            }
        return out

    def _is_singular_duplicate(self, key: str, mw: dict,
                               existing: set[str],
                               merged_map: dict[str, dict],
                               result: dict[str, dict] | None = None) -> bool:
        """True if a merged-only unit duplicates an existing unit as singular/plural.

        BSData/merged sometimes carry both the unit entry ('Vypers') and the
        model-level entry ('Vyper') with identical weapon lists. Only dedupe when
        the names differ by a trailing 's' AND the weapon lists are identical.

        Since the merge is book-first (MFM name wins), the plural twin may only
        exist in the BSData extraction (e.g. merged has 'Vyper', BSData extracts
        'Vypers') — compare against `result` too, not just `merged_map`.
        """
        def _weapons(u: dict) -> set[str]:
            return set(u.get("fixed_ranged") or []) | set(u.get("fixed_melee") or [])

        mw_weapons = _weapons(mw)

        def _existing_weapons(norm_name: str) -> set[str] | None:
            if not result:
                return None
            for orig, data in result.items():
                if self._norm_name(orig) != norm_name:
                    continue
                merged_w: set[str] = set()
                for b in data.get("builds", []):
                    merged_w |= set(b.get("fixed_ranged") or [])
                    merged_w |= set(b.get("fixed_melee") or [])
                    for group in b.get("ranged_choices", []) or []:
                        merged_w |= set(group)
                    for group in b.get("melee_choices", []) or []:
                        merged_w |= set(group)
                    for slot in b.get("slots", []) or []:
                        for c in slot.get("choices", []) or []:
                            merged_w.add(c.get("name", ""))
                return merged_w
            return None

        for other_key, other in merged_map.items():
            if other_key == key:
                continue
            if _weapons(other) != mw_weapons:
                continue
            if key + "s" == other_key or other_key + "s" == key:
                return True
            if other_key in existing and (key + "s" == other_key
                                          or other_key + "s" == key):
                return True

        # Book-first: plural twin may live only in the BSData extraction.
        for twin_norm in (key + "s", key[:-1] if key.endswith("s") else ""):
            if not twin_norm or twin_norm not in existing:
                continue
            twin_weps = _existing_weapons(twin_norm)
            if twin_weps is not None and twin_weps == mw_weapons:
                return True
        return False

    def _augment_from_merged(self, result: dict[str, dict],
                             merged_map: dict[str, dict]) -> dict[str, dict]:
        """Augment BSData-extracted constraints with merged-data FIXED weapons.

        BSData wargear groups miss many fixed weapons (they live on model profiles
        or in entryLinks pointing at sharedSelectionEntries). The merged data has
        the full resolved weapon list per unit, so it is the ground truth for the
        FIXED weapons list:

          * If BSData already captures every merged fixed weapon for a unit the
            entry is left untouched (BSData may carry optional upgrades too).
          * If weapons are missing, the unit's builds are collapsed to a single
            "default" build carrying the merged FIXED weapons plus the union of
            BSData's choice lists (ranged_choices/melee_choices/slots).
          * Units present in merged but absent from BSData (no wargear group, e.g.
            most Chaos Daemons) are added as default builds from merged weapons.
        """
        if not merged_map:
            return result
        # Augment existing units.
        for uname, udata in list(result.items()):
            # Squad composition builds (models[] with per-model slots) are
            # complete — never collapse them into a merged default build.
            if any("models" in b for b in udata.get("builds", [])):
                continue
            key = self._norm_name(uname)
            mw = merged_map.get(key)
            if not mw:
                continue
            merged_names = {self._norm_name(x)
                            for x in mw["fixed_ranged"] + mw["fixed_melee"]}
            bs_names: set[str] = set()
            for b in udata.get("builds", []):
                bs_names |= {self._norm_name(x)
                             for x in b.get("fixed_ranged", []) + b.get("fixed_melee", [])}
                # Weapons inside choice groups (and slots) are CAPTURED by
                # BSData — they are options, not missing fixed weapons. The
                # merged weapon list is the union of fixed + all options, so
                # failing to count them here collapses any unit with choice
                # structure into an all-fixed default build (the Vyper bug).
                for group in b.get("ranged_choices", []) or []:
                    bs_names |= {self._norm_name(x) for x in group}
                for group in b.get("melee_choices", []) or []:
                    bs_names |= {self._norm_name(x) for x in group}
                for slot in b.get("slots", []) or []:
                    # Slot/group name itself (e.g. Falcon's 'Heavy Weapons'
                    # group) is captured as a merged weapon — count it as
                    # covered, otherwise the group collapses to a fixed build.
                    bs_names |= {self._norm_name(slot.get("name", ""))}
                    for c in slot.get("choices", []) or []:
                        bs_names |= {self._norm_name(c.get("name", ""))}
            if not merged_names or merged_names.issubset(bs_names):
                continue  # BSData already complete — preserve its structure.
            ranged_choices: list = []
            melee_choices: list = []
            slots: list = []
            for b in udata.get("builds", []):
                ranged_choices.extend(b.get("ranged_choices", []) or [])
                melee_choices.extend(b.get("melee_choices", []) or [])
                slots.extend(b.get("slots", []) or [])
            fixed_typed = ([{"name": n, "type": "ranged"} for n in mw["fixed_ranged"]]
                           + [{"name": n, "type": "melee"} for n in mw["fixed_melee"]])
            result[uname] = {"builds": [{
                "name": "default",
                "fixed_ranged": list(mw["fixed_ranged"]),
                "fixed_melee": list(mw["fixed_melee"]),
                "ranged_choices": ranged_choices,
                "melee_choices": melee_choices,
                "max_ranged": None,
                "max_melee": None,
                "fixed": fixed_typed,
                "slots": slots,
            }]}
        # Add merged-only units (no BSData wargear group) as default builds.
        existing = {self._norm_name(n) for n in result}
        for key, mw in merged_map.items():
            if key in existing or not (mw["fixed_ranged"] or mw["fixed_melee"]):
                continue
            # Skip model-level duplicates: merged lists both 'Vypers' (unit) and
            # 'Vyper' (the model's own entry) with identical weapons. The singular
            # variant is not a separate datasheet — adding it produces a broken
            # all-fixed duplicate build (every weapon fixed, no choices).
            if self._is_singular_duplicate(key, mw, existing, merged_map, result):
                continue
            fixed_typed = ([{"name": n, "type": "ranged"} for n in mw["fixed_ranged"]]
                           + [{"name": n, "type": "melee"} for n in mw["fixed_melee"]])
            result[mw["name"]] = {"builds": [{
                "name": "default",
                "fixed_ranged": list(mw["fixed_ranged"]),
                "fixed_melee": list(mw["fixed_melee"]),
                "ranged_choices": [],
                "melee_choices": [],
                "max_ranged": None,
                "max_melee": None,
                "fixed": fixed_typed,
                "slots": [],
            }]}
            existing.add(key)
        return result

    def extract_wargear_constraints(self, faction_name: str) -> dict[str, dict]:
        """Extract wargear build constraints for all characters in a faction.

        Returns: {
            "Captain": {
                "builds": [
                    {
                        "name": "Bolt Pistol, MC Bolter, Melee Weapon",
                        "fixed_ranged": ["Bolt pistol", "Master-crafted bolter"],
                        "fixed_melee": [],
                        "ranged_choices": [],
                        "melee_choices": [["Chainsword", "Power fist", "Master-crafted power weapon"]]
                    },
                    ...
                ]
            },
            ...
        }
        """
        cat = self._resolve_faction_catalogue(faction_name)
        if cat is None:
            return {}

        roots = self._load_catalogue_roots(cat, include_linked=True)
        entry_index = self._build_entry_index(roots)

        result: dict[str, dict] = {}
        # Iterate ALL root catalogues (not just the main one) —
        # models may live in Library catalogues (e.g. CK War Dogs).
        for root in roots:
            for entry in root.get("sharedSelectionEntries", []):
                etype = entry.get("type", "")
                if etype not in ("unit", "model"):
                    continue
                name = entry.get("name", "")
                hidden = entry.get("hidden", "false")
                if hidden == "true" or not name:
                    continue

                # Find the "Wargear" selectionEntryGroup. Some units (e.g.
                # Vypers) put their Wargear group on the NESTED model
                # selectionEntry rather than the top-level unit entry.
                wargear_group = None
                for seg in entry.get("selectionEntryGroups", []):
                    seg_name = (seg.get("name") or "").lower()
                    if "wargear" in seg_name:
                        wargear_group = seg
                        break
                if wargear_group is None:
                    # Descend into nested model entries — the unit has no
                    # top-level wargear, but the model may carry it.
                    for sel in entry.get("selectionEntries", []):
                        if sel.get("hidden") == "true":
                            continue
                        for seg in sel.get("selectionEntryGroups", []):
                            seg_name = (seg.get("name") or "").lower()
                            if "wargear" in seg_name:
                                wargear_group = seg
                                break
                        if wargear_group is not None:
                            break
                if wargear_group is None:
                    continue

                builds: list[dict] = []

                # Determine if selectionEntries are build packages (Pattern 1)
                # or inline weapons (Pattern 3). Build packages contain weapon
                # entryLinks and/or nested choice groups — they may also have direct
                # profiles (built-in weapon + optional upgrades). Fixed weapons
                # (Pulse Laser, Wraithbone hull) carry only crusade-system
                # entryLinks that resolve to no weapon profiles — NOT packages.
                has_build_packages = False
                for se in wargear_group.get("selectionEntries", []):
                    if se.get("hidden") == "true":
                        continue
                    if self._is_build_package(se, entry_index):
                        has_build_packages = True
                        break

                if has_build_packages:
                    # Pattern 1: Build packages — each selectionEntry is a named build
                    for se in wargear_group["selectionEntries"]:
                        if se.get("hidden") == "true":
                            continue
                        build_name = se.get("name", "")
                        # Also extract weapons from direct profiles on the selection entry
                        # itself — some entries have their built-in weapon as a profile
                        # AND separate entryLinks/selectionEntryGroups for add-ons.
                        extra_inline: list[dict] = []
                        for p in se.get("profiles", []):
                            pname = p.get("typeName", "")
                            if pname in ("Ranged Weapons", "Melee Weapons"):
                                extra_inline.append({
                                    "name": self._strip_arrow(p.get("name", "")),
                                    "profiles": [p],
                                })
                        all_selection_entries = list(se.get("selectionEntries", []))
                        all_selection_entries.extend(extra_inline)
                        classified = self._classify_build_items(
                            se.get("entryLinks", []),
                            all_selection_entries,
                            se.get("selectionEntryGroups", []),
                            entry_index,
                            parent_group_name=build_name,
                        )
                        has_weapons = (classified["fixed_ranged"] or classified["fixed_melee"]
                                       or classified["ranged_choices"] or classified["melee_choices"]
                                       or classified["fixed"] or classified["slots"])
                        if not has_weapons:
                            # Pure abilities/upgrades (e.g. Shadow Field) — not a real weapon build
                            continue
                        builds.append({"name": build_name, **classified})
                else:
                    # Pattern 2+3: Flat or Hybrid — all items on the Wargear group
                    # are part of a single default build
                    classified = self._classify_build_items(
                        wargear_group.get("entryLinks", []),
                        wargear_group.get("selectionEntries", []),
                        wargear_group.get("selectionEntryGroups", []),
                        entry_index,
                        parent_group_name="default",
                    )
                    has_weapons = (classified["fixed_ranged"] or classified["fixed_melee"]
                                   or classified["ranged_choices"] or classified["melee_choices"])
                    if has_weapons:
                        builds.append({"name": "default", **classified})

                if builds:
                    result[name] = {"builds": builds}

        # Squad model-composition units (no Wargear group — e.g. Dark Reapers,
        # Howling Banshees) are parsed from their sibling-SEG structure into
        # per-model builds with per-model slots. These are complete and MUST
        # not be clobbered by the merged-data augment below.
        composition = self._extract_squad_composition(roots, entry_index)
        for cname, cdata in composition.items():
            if cname not in result:
                result[cname] = cdata

        # Augment BSData constraints with the merged-data FIXED weapon lists.
        # BSData wargear groups miss many fixed weapons (model profiles / shared
        # entryLinks); merged data carries the fully-resolved weapon list.
        self._augment_from_merged(result, self._load_merged_weapon_map(faction_name))

        return result

    def extract_squad_composition(self, faction_name: str) -> dict[str, dict]:
        """Public: squad model-composition builds for a faction (unit -> builds).

        See _extract_squad_composition for the output shape. Mirrors what
        NewRecruit consumes: per-model-type entries with fixed weapons and
        per-model choose-one slots.
        """
        cat = self._resolve_faction_catalogue(faction_name)
        if cat is None:
            return {}
        roots = self._load_catalogue_roots(cat, include_linked=True)
        entry_index = self._build_entry_index(roots)
        return self._extract_squad_composition(roots, entry_index)

    def _extract_squad_composition(self, roots: list[dict],
                                   entry_index: dict[str, dict]) -> dict[str, dict]:
        """Extract squad model-composition builds for units with the sibling-SEG
        pattern: top-level selectionEntryGroups that nest type=model SEs.

        Returns: {
            "Dark Reapers": {"builds": [{
                "name": "Default",
                "models": [
                    {"name": "Dark Reaper", "count": 1, "min": 4, "max": 9,
                     "ranged": "Reaper Launcher", "melee": "Close combat weapon",
                     "slots": []},
                    {"name": "Dark Reaper Exarch", "count": 1, "min": 1, "max": 1,
                     "melee": "Close combat weapon",
                     "slots": [{"name": "Weapon", "choices": [
                         {"name": "Reaper Launcher", "ranged": "Reaper Launcher"},
                         {"name": "Shuriken Cannon", "ranged": "Shuriken Cannon"}]}]}
                ]
            }]}
        }
        Counts are placeholders (1 per model type); the generator derives the
        concrete per-type counts from the squad size n.
        """
        result: dict[str, dict] = {}
        for root in roots:
            for entry in root.get("sharedSelectionEntries", []):
                if entry.get("type") != "unit":
                    continue
                name = entry.get("name", "")
                if entry.get("hidden") == "true" or not name:
                    continue
                # Composition pattern: top-level SEGs that nest type=model SEs
                # (Dark Reapers) OR direct type=model SEs on the unit entry
                # (Rangers). Both mean "this unit is a squad of model types".
                # Model pools may sit one SEG deeper (Corsair Voidscarred: the
                # '4-9 Voidscarred' SEG nests a 'Voidscarred' SEG holding the
                # base variants); recurse to collect them.
                model_seg = []
                seg_min_owners: dict[str, int] = {}
                seg_max_owners: dict[str, int] = {}
                dup_strip_owners: set[str] = set()

                def _collect_models(seg_list: list[dict], depth: int = 0) -> None:
                    for seg in seg_list:
                        if seg.get("hidden") == "true":
                            continue
                        seg_min = None
                        seg_max = None
                        for c in seg.get("constraints", []):
                            if c.get("field") == "selections":
                                if c.get("type") == "min":
                                    seg_min = c.get("value")
                                elif c.get("type") == "max":
                                    seg_max = c.get("value")
                        for se in seg.get("selectionEntries", []):
                            if se.get("hidden") != "true" and se.get("type") == "model":
                                # A NESTED SEG's min is a per-pool constraint
                                # (at least N models from this pool), not the
                                # squad size — remember it for the alloc model.
                                if depth > 0 and seg_min is not None:
                                    seg_min_owners[se.get("id", "")] = seg_min
                                # A nested SEG's max is a SHARED cap across its
                                # variants (e.g. Purgation 'Heavy Weapons'
                                # max=4: at most 4 special weapons total, mixed
                                # freely), NOT a per-variant max. The engine
                                # enforces it as a combined budget.
                                if depth > 0 and seg_max is not None:
                                    seg_max_owners[se.get("id", "")] = seg_max
                                # Duplicate constraint: the base model entry
                                # copies the group's min/max (BSData pattern,
                                # e.g. Purgation 'Purgator' min=4/max=9 == the
                                # '4-9 Purgators' group). Strip it — the group
                                # constraint is the pool, not a forced base
                                # count (at n=5 that would force 4 plain
                                # models and hide the special weapons).
                                # Leaders (min == max == 1) are exempt.
                                # Only strip when the base SE is the group's
                                # ONLY direct model (specials nested deeper,
                                # e.g. Purgation) — when specials are direct
                                # siblings (e.g. Ynnari Reavers Blaster/Heat
                                # Lance), the base min is a real per-variant
                                # minimum and must survive.
                                if depth == 0 and seg_min is not None and seg_max is not None:
                                    direct_models = [s for s in seg.get("selectionEntries", [])
                                                     if isinstance(s, dict)
                                                     and s.get("hidden") != "true"
                                                     and s.get("type") == "model"]
                                    se_min = None
                                    se_max = None
                                    for c in se.get("constraints", []):
                                        if c.get("field") != "selections":
                                            continue
                                        if c.get("type") == "min":
                                            se_min = c.get("value")
                                        elif c.get("type") == "max":
                                            se_max = c.get("value")
                                    if (se_min == seg_min and se_max == seg_max
                                            and not (se_min == 1 and se_max == 1)
                                            and len(direct_models) == 1):
                                        dup_strip_owners.add(se.get("id", ""))
                                model_seg.append(se)
                        _collect_models(seg.get("selectionEntryGroups", []),
                                        depth + 1)

                _collect_models(entry.get("selectionEntryGroups", []))
                for se in entry.get("selectionEntries", []):
                    if se.get("hidden") != "true" and se.get("type") == "model":
                        model_seg.append(se)
                if not model_seg:
                    continue
                models = []
                for se in model_seg:
                    m = self._parse_composition_model(
                        se, entry_index,
                        seg_min_owners.get(se.get("id", "")),
                        seg_max_owners.get(se.get("id", "")),
                        se.get("id", "") in dup_strip_owners)
                    if m is not None:
                        models.append(m)
                if not models:
                    continue
                result[name] = {"builds": [{"name": "Default", "models": models}]}
        return result

    def _parse_composition_model(self, se: dict, entry_index: dict[str, dict],
                                 pool_min: int | None = None,
                                 group_max: int | None = None,
                                 dup_strip: bool = False) -> dict | None:
        """Parse one type=model SE into a per-model entry.

        Fixed weapons come from own selectionEntries (upgrade SEs with weapon
        profiles, e.g. Dark Reaper: Reaper Launcher + Close combat weapon) and
        own entryLinks (e.g. Dire Avenger: Avenger shuriken catapult). Slots
        come from own selectionEntryGroups — each nested group is one
        choose-one slot on that model type (e.g. Exarch "Weapon(s)").

        Multiple fixed weapons per type are kept as a LIST on ranged/melee
        (e.g. Warlock: Shuriken Pistol + Destructor; Voidscarred base:
        Shuriken Pistol + Fusion pistol); single weapons stay a string. The
        engine sums all ranged and reduces melee to the best per model.

        pool_min: a nested SEG's min constraint (at least N models must come
        from this pool, e.g. Voidscarred's base pool min=4). Recorded on the
        model so the generator can carry it into the alloc payload.

        group_max: a nested SEG's max constraint shared across its variants
        (at most N combined, e.g. Purgation's 'Heavy Weapons' max=4). The
        engine caps the SUM of the tagged variants, not each individually.

        dup_strip: the base entry duplicated the group's min/max (BSData
        pattern); drop the per-entry constraint so it does not force plain
        models when the group min is satisfiable by special variants.
        """
        model: dict = {"name": se.get("name", ""), "count": 1}
        min_c = None
        max_c = None
        for c in se.get("constraints", []):
            if c.get("field") != "selections":
                continue
            if c.get("type") == "min":
                min_c = c.get("value")
            elif c.get("type") == "max":
                max_c = c.get("value")
        if dup_strip:
            # Group constraint duplicated on the base entry — skip; the pool
            # carries it. Avoids forcing N plain models at squad size N.
            min_c = None
            max_c = None
        if min_c is not None:
            model["min"] = min_c
        if max_c is not None:
            model["max"] = max_c
        if pool_min is not None:
            model["pool_min"] = pool_min
        if group_max is not None:
            model["group_max"] = group_max

        fixed_r: list[str] = []
        fixed_m: list[str] = []
        # Own upgrade SEs (inline weapon profiles, or infoLink profile refs)
        for sub in se.get("selectionEntries", []):
            if sub.get("hidden") == "true":
                continue
            cats = self._resolve_entry_categories(sub, entry_index)
            sname = self._strip_arrow(sub.get("name", ""))
            if "ranged" in cats:
                fixed_r.append(sname)
            if "melee" in cats:
                fixed_m.append(sname)
        # Own entryLinks (shared weapon SEs)
        for el in se.get("entryLinks", []):
            if el.get("hidden") == "true":
                continue
            if self._resolve_shared_group_target(el, entry_index) is not None:
                continue
            cats = set()
            tid = el.get("targetId", "")
            if tid:
                target = entry_index.get(tid)
                if target is not None:
                    cats = self._resolve_entry_categories(target, entry_index)
            if not cats:
                cats = self._resolve_entry_categories(el, entry_index)
            ename = self._strip_arrow(el.get("name", ""))
            if "ranged" in cats:
                fixed_r.append(ename)
            if "melee" in cats:
                fixed_m.append(ename)
        fixed_r = list(dict.fromkeys(x for x in fixed_r if x))
        fixed_m = list(dict.fromkeys(x for x in fixed_m if x))
        # Single weapon per type stays a string (existing schema); multiple
        # fixed weapons per type become a list — the engine sums ranged and
        # reduces melee to the best per model.
        if fixed_r:
            model["ranged"] = fixed_r[0] if len(fixed_r) == 1 else fixed_r
        if fixed_m:
            model["melee"] = fixed_m[0] if len(fixed_m) == 1 else fixed_m

        slots: list[dict] = []
        for group in se.get("selectionEntryGroups", []):
            if group.get("hidden") == "true":
                continue
            default_id = group.get("defaultSelectionEntryId", "")
            choices: list[dict] = []
            for el in group.get("entryLinks", []):
                if el.get("hidden") == "true":
                    continue
                if self._resolve_shared_group_target(el, entry_index) is not None:
                    continue
                choice = self._resolve_model_choice_payload(el, entry_index,
                                                            is_entry_link=True)
                if choice:
                    if default_id and el.get("targetId") == default_id:
                        choice["default"] = True
                    choices.append(choice)
            for ch in group.get("selectionEntries", []):
                if ch.get("hidden") == "true":
                    continue
                choice = self._resolve_model_choice_payload(ch, entry_index,
                                                            is_entry_link=False)
                if choice:
                    if default_id and ch.get("id") == default_id:
                        choice["default"] = True
                    choices.append(choice)
            if choices:
                slots.append({"name": group.get("name", ""), "choices": choices})
        if slots:
            model["slots"] = slots

        # A model with no fixed weapons AND no slots carries nothing (e.g. a
        # pure-ability wrapper) — skip it rather than emit a dead entry.
        if not fixed_r and not fixed_m and not slots:
            return None
        return model

    def _resolve_model_choice_payload(self, choice: dict, entry_index: dict[str, dict],
                                      is_entry_link: bool = False) -> dict | None:
        """Resolve one model-slot choice option into a bundle payload.

        A choice may be a single weapon (entryLink to a shared weapon SE, or an
        upgrade SE with a weapon profile) or a bundle (entryLinks + own SEs,
        e.g. 'Banshee Blade and Shuriken Pistol'). The payload is the resolved
        weapon package: {"name", "ranged"?, "melee"?, "ranged_count"?,
        "melee_count"?}. Ability-only choices (e.g. Shimmershield alone) return
        None. Counts come from constraints min>1 (e.g. 2x Avenger shuriken
        catapult).
        """
        ranged: list[str] = []
        melee: list[str] = []
        ranged_count = 1
        melee_count = 1
        # A dual-profile weapon name (BSData artifact, e.g. Chainsabres and
        # Singing Spear carry Melee + Ranged profiles with the same name)
        # lands in BOTH the ranged and melee lists — the engine loads the
        # matching profile per list context (loader `category` param).
        seen_categories: dict[str, set] = {}

        def add_weapon(name: str, cat: str, cnt: int) -> None:
            nonlocal ranged_count, melee_count
            if not name or cat not in ("ranged", "melee"):
                return
            name = self._strip_mode_suffix(self._strip_arrow(name))
            cats = seen_categories.setdefault(name, set())
            cats.add(cat)
            if "ranged" in cats and name not in ranged:
                ranged.append(name)
                if cnt > ranged_count:
                    ranged_count = cnt
            if "melee" in cats and name not in melee:
                melee.append(name)
                if cnt > melee_count:
                    melee_count = cnt

        # Own profiles (e.g. Mirrorswords profile on the choice SE itself)
        for p in choice.get("profiles", []):
            ptype = p.get("typeName", "")
            pname = p.get("name", "")
            if "Ranged" in ptype:
                add_weapon(pname, "ranged", 1)
            elif "Melee" in ptype:
                add_weapon(pname, "melee", 1)

        # Own selectionEntries (upgrade SEs with profiles)
        for sub in choice.get("selectionEntries", []):
            if sub.get("hidden") == "true":
                continue
            cats = self._resolve_entry_categories(sub, entry_index)
            sname = self._strip_arrow(sub.get("name", ""))
            cnt = self._get_selection_count(sub)
            if "ranged" in cats:
                add_weapon(sname, "ranged", cnt)
            if "melee" in cats:
                add_weapon(sname, "melee", cnt)

        # entryLinks — either the choice IS an entryLink, or it nests them
        sources = [choice] if is_entry_link else choice.get("entryLinks", [])
        for el in sources:
            if el.get("hidden") == "true":
                continue
            if self._resolve_shared_group_target(el, entry_index) is not None:
                continue
            cats = set()
            tid = el.get("targetId", "")
            if tid:
                target = entry_index.get(tid)
                if target is not None:
                    cats = self._resolve_entry_categories(target, entry_index)
            if not cats:
                cats = self._resolve_entry_categories(el, entry_index)
            ename = self._strip_arrow(el.get("name", ""))
            cnt = self._get_selection_count(el)
            if "ranged" in cats:
                add_weapon(ename, "ranged", cnt)
            if "melee" in cats:
                add_weapon(ename, "melee", cnt)

        if not ranged and not melee:
            return None

        payload: dict = {"name": self._strip_arrow(choice.get("name", ""))}
        if ranged:
            payload["ranged"] = ranged[0]
            if ranged_count > 1:
                payload["ranged_count"] = ranged_count
        if melee:
            payload["melee"] = melee[0]
            if melee_count > 1:
                payload["melee_count"] = melee_count
        return payload

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
                # Deduplicate pass 1: truly identical entries (same name + same stats)
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
                # Deduplicate pass 2: same name, prefer more complete entry
                # (handles stale main-catalogue duplicates alongside updated library entries,
                #  e.g. Bloodletters OC=1 from World Eaters + OC=2 from Daemons Library)
                name_groups: dict[str, list[dict]] = {}
                for u in deduped:
                    n = u['name'].lower().strip()
                    name_groups.setdefault(n, []).append(u)
                units = []
                for n, group in name_groups.items():
                    if len(group) == 1:
                        units.append(group[0])
                    else:
                        # Prefer entry with stats first, then most completeness
                        def sort_key(u):
                            has_stats = 1 if u.get('stats') else 0
                            completeness = (len(u.get('abilities', [])) +
                                            len(u.get('rules', [])) +
                                            len(u.get('weapons', [])))
                            return (has_stats, completeness)
                        group.sort(key=sort_key, reverse=True)
                        units.append(group[0])
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
