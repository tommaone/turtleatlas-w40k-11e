"""
BSData catalogue XML parser — ported from turtleatlas-w40k/bsdata_query.py.

Parses 10e .cat files to extract unit profiles (stats, weapons, abilities, keywords).
Handles cross-file catalogue linking, Legends filtering, entryLink resolution.

Usage:
    from adapter.bsdata_parser import BSDataParser
    parser = BSDataParser()
    factions = parser.list_factions()
    data = parser.query_faction("Imperium - Grey Knights")
"""

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"bs": "http://www.battlescribe.net/schema/catalogueSchema"}

SKIP_PREFIXES = ["Library -"]
SKIP_FACTIONS = {"Unaligned Forces"}
CRUCIBLE_RE = re.compile(r'\[Crucible\]', re.IGNORECASE)


class BSDataParser:
    """Parses BSData XML catalogue files for unit profiles."""

    def __init__(self, bsdata_dir: str | Path | None = None):
        self.bsdata_dir = Path(bsdata_dir or
                               Path(__file__).resolve().parent.parent / "bsdata")

    def is_playable_faction(self, name: str) -> bool:
        if not name:
            return False
        if CRUCIBLE_RE.search(name):
            return False
        if name in SKIP_FACTIONS:
            return False
        if name.endswith("Library") or name.endswith("Library "):
            return False
        for prefix in SKIP_PREFIXES:
            if name.startswith(prefix):
                return False
        return True

    def find_cat_files(self) -> list[Path]:
        if not self.bsdata_dir.is_dir():
            return []
        return sorted(self.bsdata_dir.glob("*.cat"))

    def load_catalogue(self, path: Path) -> ET.Element | None:
        try:
            tree = ET.parse(path)
            return tree.getroot()
        except Exception as e:
            print(f"Error parsing {path}: {e}", file=sys.stderr)
            return None

    def get_attr(self, elem: ET.Element, key: str, default: str = "") -> str:
        return elem.get(key, default)

    def find_cat_file_by_name(self, name: str) -> Path | None:
        for path in self.find_cat_files():
            root = self.load_catalogue(path)
            if root is not None:
                cat_name = self.get_attr(root, "name")
                if cat_name and cat_name.lower() == name.lower():
                    return path
        return None

    def load_linked_roots(self, root: ET.Element) -> list[tuple[str | None, ET.Element]]:
        """Load linked catalogues with importRootEntries='true'."""
        linked: list[tuple[str | None, ET.Element]] = []
        for link in root.findall("bs:catalogueLinks/bs:catalogueLink", NS):
            name = self.get_attr(link, "name")
            import_root = self.get_attr(link, "importRootEntries", "false")
            if import_root != "true" or not name:
                continue
            path = self.find_cat_file_by_name(name)
            if path:
                linked_root = self.load_catalogue(path)
                if linked_root is not None:
                    linked.append((name, linked_root))
        return linked

    def _search_roots_for_entry(self, target_id: str,
                                 roots: list[tuple[str | None, ET.Element]]) -> ET.Element | None:
        for _, r in roots:
            entry = r.find(f".//bs:selectionEntry[@id='{target_id}']", NS)
            if entry is not None:
                return entry
        return None

    def _search_roots(self, roots: list[tuple[str | None, ET.Element]], xpath: str):
        for _, r in roots:
            for elem in r.findall(xpath, NS):
                yield elem

    def _resolve_weapon_profiles(self, root: ET.Element, target_id: str,
                                  extra_roots: list[tuple[str | None, ET.Element]] | None = None) -> list[dict]:
        """Find a selectionEntry by target_id and return weapon profiles."""
        all_roots: list[tuple[str | None, ET.Element]] = [(None, root)] + (extra_roots or [])
        entry = self._search_roots_for_entry(target_id, all_roots)
        profiles: list[dict] = []
        if entry is not None:
            for profile in entry.findall(".//bs:profile", NS):
                type_name = self.get_attr(profile, "typeName", "")
                if "Weapon" in type_name:
                    chars = {}
                    for char in profile.findall(".//bs:characteristic", NS):
                        chars[self.get_attr(char, "name")] = char.text or ""
                    profiles.append({
                        "name": self.get_attr(profile, "name"),
                        "typeName": type_name,
                        "stats": chars,
                    })
        return profiles

    def list_factions(self) -> list[str]:
        """Return sorted playable faction names."""
        factions: list[str] = []
        for path in self.find_cat_files():
            root = self.load_catalogue(path)
            if root is not None:
                name = self.get_attr(root, "name")
                if name and self.is_playable_faction(name):
                    factions.append(name)
        return sorted(factions)

    def extract_units(self, root: ET.Element, faction_name: str,
                       include_legends: bool = False,
                       extra_roots: list[tuple[str | None, ET.Element]] | None = None) -> list[dict]:
        """Extract all units from a catalogue and its linked catalogues."""
        all_roots: list[tuple[str | None, ET.Element]] = [(None, root)] + (extra_roots or [])
        units: list[dict] = []

        for entry in self._search_roots(all_roots, ".//bs:sharedSelectionEntries/bs:selectionEntry"):
            entry_type = self.get_attr(entry, "type", "")
            if entry_type not in ("model", "unit"):
                continue
            name = self.get_attr(entry, "name")
            hidden = self.get_attr(entry, "hidden", "false")
            if hidden == "true":
                continue
            if not include_legends and "[Legends]" in name:
                continue

            # Points cost
            points: int | None = None
            cost = entry.find(".//bs:costs/bs:cost", NS)
            if cost is not None:
                try:
                    points = int(cost.get("value", 0))
                except (ValueError, TypeError):
                    points = None

            # Unit profile (stats)
            stats: dict[str, str] = {}
            profile = entry.find('.//bs:profiles/bs:profile[@typeName="Unit"]', NS)
            if profile is not None:
                for char in profile.findall(".//bs:characteristic", NS):
                    char_name = self.get_attr(char, "name")
                    stats[char_name] = char.text or ""

            # Keywords / categories
            keywords: list[str] = []
            for cat_link in entry.findall(".//bs:categoryLinks/bs:categoryLink", NS):
                cat_name = self.get_attr(cat_link, "name")
                if cat_name and cat_name not in ("Configuration", "No Force Org Slot"):
                    keywords.append(cat_name)

            # Abilities
            abilities: list[dict] = []
            for ab_profile in entry.findall('.//bs:profiles/bs:profile[@typeName="Abilities"]', NS):
                ab_name = self.get_attr(ab_profile, "name")
                ab_desc = ""
                for char in ab_profile.findall(".//bs:characteristic", NS):
                    char_name = self.get_attr(char, "name")
                    if "description" in char_name.lower() or char_name == "Description":
                        ab_desc = char.text or ""
                abilities.append({"name": ab_name, "description": ab_desc})

            # Weapons — two patterns:
            # 1. entryLinks (point to selectionEntry elsewhere)
            # 2. direct selectionEntries (inline weapons)
            weapons: list[dict] = []
            # Pattern 1: entryLinks
            for link in entry.findall(".//bs:entryLinks/bs:entryLink", NS):
                w_name = self.get_attr(link, "name")
                hidden_w = self.get_attr(link, "hidden", "false")
                link_type = self.get_attr(link, "type", "")
                if hidden_w == "true":
                    continue
                if link_type == "selectionEntry":
                    target_id = link.get("targetId", "")
                    profiles = self._resolve_weapon_profiles(root, target_id, extra_roots) if target_id else []
                    weapons.append({"name": w_name, "profiles": profiles})
            # Pattern 2: direct selectionEntry children
            for sel in entry.findall(".//bs:selectionEntries/bs:selectionEntry", NS):
                hidden_sel = self.get_attr(sel, "hidden", "false")
                if hidden_sel == "true":
                    continue
                w_name = self.get_attr(sel, "name")
                profiles: list[dict] = []
                for p in sel.findall(".//bs:profile", NS):
                    type_name = self.get_attr(p, "typeName", "")
                    if "Weapon" in type_name:
                        chars = {}
                        for c in p.findall(".//bs:characteristic", NS):
                            chars[self.get_attr(c, "name")] = c.text or ""
                        profiles.append({"name": self.get_attr(p, "name"), "typeName": type_name, "stats": chars})
                if profiles:
                    weapons.append({"name": w_name, "profiles": profiles})

            # Rules (info links)
            rules: list[str] = []
            for info_link in entry.findall(".//bs:infoLinks/bs:infoLink", NS):
                r_name = self.get_attr(info_link, "name")
                hidden_r = self.get_attr(info_link, "hidden", "false")
                if hidden_r == "true":
                    continue
                rules.append(r_name)

            unit_entry: dict = {
                "name": name,
                "points": points,
                "stats": stats,
                "keywords": keywords,
                "abilities": abilities,
                "weapons": weapons,
                "rules": rules,
            }

            # Find origin for ally tagging
            for origin_name, r in all_roots:
                if r.find(f".//bs:sharedSelectionEntries/bs:selectionEntry[@name='{name}']", NS) is not None:
                    if origin_name and origin_name != faction_name:
                        unit_entry["ally_of"] = origin_name
                    break

            units.append(unit_entry)

        return units

    def query_faction(self, faction_name: str, include_legends: bool = False) -> dict | None:
        """Return full data for a faction, including linked catalogues."""
        for path in self.find_cat_files():
            root = self.load_catalogue(path)
            if root is None:
                continue
            name = self.get_attr(root, "name")
            if name and name.lower() == faction_name.lower():
                extra_roots = self.load_linked_roots(root)
                units = self.extract_units(root, name, include_legends, extra_roots)
                all_units = self.extract_units(root, name, include_legends=True, extra_roots=extra_roots)
                legends_count = len(all_units) - len(units)
                return {
                    "name": name,
                    "id": self.get_attr(root, "id"),
                    "revision": self.get_attr(root, "revision"),
                    "units": units,
                    "legends_count": legends_count,
                }
        return None

    def slug_to_faction(self, slug: str) -> str | None:
        """Convert a MFM-style slug (grey-knights) to BSData faction name."""
        for faction in self.list_factions():
            # BSData names are like "Imperium - Grey Knights"
            if slug.replace("-", " ").lower() in faction.lower() or \
               slug.lower().replace("-", " ") in faction.lower():
                return faction
        return None
