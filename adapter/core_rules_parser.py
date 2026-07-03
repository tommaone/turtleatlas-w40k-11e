"""
11e Core Rules PDF parser.

Extracts structured rule data from the free Warhammer 40,000 11th Edition
Core Rules PDF into machine-readable JSON for use in DPP engine + MCP server.

Sources:
  https://assets.warhammer-community.com/eng_01-06_warhammer40k_new40k_core_rules-was6fbu1ix-hfewhmxyiy.pdf
"""

import json
import re
import sys
from pathlib import Path

import fitz  # pymupdf

REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Section detection
# ---------------------------------------------------------------------------

SECTION_MARKERS = {
    "CORE CONCEPTS": "core_concepts",
    "DATASHEETS": "datasheets",
    "CORE ABILITIES": "core_abilities",
    "THE BATTLE ROUND": "battle_round",
    "COMMAND PHASE": "command_phase",
    "MOVEMENT PHASE": "movement_phase",
    "SHOOTING PHASE": "shooting_phase",
    "CHARGE PHASE": "charge_phase",
    "FIGHT PHASE": "fight_phase",
    "TERRAIN": "terrain",
    "USING STRATAGEMS": "stratagems",
    "ADVANCED RULES": "advanced_rules",
    "MONSTERS AND VEHICLES": "monsters_vehicles",
    "STRATEGIC RESERVES": "advanced_rules",
    "AURA ABILITIES": "advanced_rules",
    "PLUNGING FIRE": "advanced_rules",
    "AIRCRAFT": "advanced_rules",
    "TRANSPORT CAPACITY": "transport",
    "DISEMBARK": "transport",
    "EMBARK": "transport",
    "ATTACHED UNITS": "attached_units",
    "KEYWORDS IN ATTACHED": "attached_units",
    "RULES APPENDIX": "rules_appendix",
    "REFERENCE": "reference",
}

# Normalize both regular hyphen and en dash (PDF uses U+2011)
_EN = "\u2011"  # non-breaking hyphen / en dash used in PDF
_HYPHENS = r"[\-\u2011\u2010]"

# Build patterns: each name with hyphen variants
def _name_pattern(name: str) -> str:
    """Replace hyphens with hyphen-variant character class."""
    return _HYPHENS.join(re.escape(part) for part in re.split(r'[\-\u2011\u2010]', name))

RAW_ABILITY_NAMES = [
    "ANTI", "ASSAULT", "BLAST", "CLEAVE", "CLOSE-QUARTERS",
    "DEADLY DEMISE", "DEEP STRIKE", "DEVASTATING WOUNDS", "EXTRA ATTACKS",
    "FEEL NO PAIN", "FIGHTS FIRST", "FIRING DECK", "HAZARDOUS", "HEAVY",
    "HOVER", "IGNORES COVER", "INDIRECT FIRE", "INFILTRATORS", "LANCE",
    "LEADER", "LETHAL HITS", "LONE OPERATIVE", "MELTA", "ONE SHOT",
    "PISTOL", "PRECISION", "PSYCHIC", "RAPID FIRE", "SCOUTS",
    "STEALTH", "SUPPORT", "SUPER-HEAVY WALKER", "SUSTAINED HITS",
    "TORRENT", "TWIN-LINKED",
]
ABILITY_PATTERNS = [(n, _name_pattern(n)) for n in RAW_ABILITY_NAMES]


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def extract_abilities(pages: list) -> list:
    """Extract core abilities/keywords from the reference section."""
    abilities = []
    text = "\n".join(p.get_text() for p in pages)
    text = text.replace("\x08", "")
    lines = text.split("\n")

    # Find ability header lines: "[NAME] XX.YY" or "NAME XX.YY" with hyphen variants
    # Weapon abilities use brackets, core abilities (like DEADLY DEMISE) don't
    ability_names_alt = '|'.join(p for _, p in ABILITY_PATTERNS)
    # Two separate patterns: bracketed and unbracketed
    header_bracket = re.compile(rf'^\[({ability_names_alt})\]\s+(\d+\.\d+)')
    header_unbracket = re.compile(rf'^({ability_names_alt})\s+(\d+\.\d+)')

    i = 0
    def is_header(line: str) -> re.Match | None:
        return header_bracket.match(line) or header_unbracket.match(line)

    while i < len(lines):
        line = lines[i].strip()
        m = is_header(line)
        if m:
            # name could be in group 1 (bracketed) or group 3 (unbracketed)
            name = (m.group(1) or m.group(3)).replace("\u2011", "-").replace("\u2010", "-")
            ref = m.group(2) or m.group(4)

            # Collect body until next header or section break
            body_lines = []
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                if not next_line:
                    i += 1
                    continue
                if is_header(next_line):
                    break
                if next_line in ("CORE ABILITIES", "REFERENCE") or next_line.startswith("ABILITIES"):
                    break
                body_lines.append(next_line)
                i += 1

            body = " ".join(line for line in body_lines if line and not line.isdigit())
            body = re.sub(r'\s+', ' ', body).strip()

            form_match = re.search(r'This ability always takes the form\s+([^\.]+)\.', body)
            form = form_match.group(1).strip() if form_match else None

            abilities.append({
                "name": name,
                "ref": ref,
                "form": form,
                "description": body,
            })
        else:
            i += 1

    return abilities


def extract_cover_rules(pages: list) -> dict:
    """Extract cover rules from terrain section."""
    text = "\n".join(p.get_text() for p in pages)

    cover_info = {
        "benefit_of_cover": None,
        "cover_modifier": None,
        "plunging_fire": None,
        "ignores_cover": None,
    }

    # Benefit of Cover section — stop at next heading (all-caps + ref)
    next_heading = re.compile(r'^\s*[A-Z][A-Z\s]+\d+\.\d+', re.MULTILINE)
    m = re.search(r'BENEFIT OF COVER\s+13\.08\s*(.*?)(?=\n\s*[A-Z][A-Z\s]*\d+\.\d+|\Z)', text, re.DOTALL)
    if m:
        cover_info["benefit_of_cover"] = re.sub(r'\s+', ' ', m.group(1)).strip()

    # Cover modifier: "worsen the BS characteristic of that attack by 1"
    m = re.search(r'(?i)worsen the BS.*?by 1', text)
    if m:
        cover_info["cover_modifier"] = m.group(0).strip()

    # Plunging Fire — stop at next heading
    m = re.search(r'PLUNGING FIRE\s+22\.\d+\s*(.*?)(?=\n\s*[A-Z][A-Z\s]*\d+\.\d+|\Z)', text, re.DOTALL)
    if m:
        cover_info["plunging_fire"] = re.sub(r'\s+', ' ', m.group(1)).strip()

    return cover_info


def extract_stratagems(pages: list) -> list:
    """Extract core stratagems."""
    text = "\n".join(p.get_text() for p in pages)
    text = text.replace("\x08", "")
    stratagems = []
    seen = set()

    # Stratagem headers are all-caps followed by ref number
    pattern = re.compile(r'^([A-Z][A-Z\s\-]+)\s+(\d+\.\d+)$')
    for line in text.split("\n"):
        line = line.strip()
        m = pattern.match(line)
        if m:
            name = m.group(1).strip()
            ref = m.group(2)
            # Skip generic headings
            if name in ("CORE STRATAGEMS", "USING STRATAGEMS", "STRATAGEMS"):
                continue
            key = (name.title(), ref)
            if key not in seen:
                seen.add(key)
                stratagems.append({"name": name.title(), "ref": ref})

    return stratagems


def extract_field(text: str, field: str) -> str | None:
    """Extract a labelled field like WHEN: ... from text."""
    m = re.search(rf'{re.escape(field)}:\s*(.*?)(?=\n[A-Z]+:|\Z)', text, re.DOTALL)
    if m:
        return re.sub(r'\s+', ' ', m.group(1)).strip()
    return None


def extract_phase_structure(pages: list) -> dict:
    """Extract phase structure — which phases exist and their sub-steps with refs."""
    text = "\n".join(p.get_text() for p in pages)
    text = text.replace("\x08", "")

    structure = {}
    # Phase headings and their sub-step ref patterns
    phase_headers = {
        "THE BATTLE ROUND": "battle_round",
        "COMMAND PHASE": "command_phase",
        "MOVEMENT PHASE": "movement_phase",
        "SHOOTING PHASE": "shooting_phase",
        "CHARGE PHASE": "charge_phase",
        "FIGHT PHASE": "fight_phase",
    }

    lines = text.split("\n")
    current_phase = None
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Detect phase heading
        for header, key in phase_headers.items():
            if stripped == header:
                current_phase = key
                if key not in structure:
                    structure[key] = {"ref": None, "steps": []}
                break
        else:
            # Check for sub-step like "1. START OF COMMAND PHASE 08.01"
            m = re.match(r'^\d+\.\s+(.+?)\s+(\d+\.\d+)$', stripped)
            if m and current_phase:
                structure[current_phase]["steps"].append({
                    "name": m.group(1).strip(),
                    "ref": m.group(2),
                })
                if structure[current_phase]["ref"] is None:
                    structure[current_phase]["ref"] = m.group(2).split(".")[0]

    return structure


def extract_terrain_keywords(pages: list) -> dict:
    """Extract terrain keyword rules."""
    text = "\n".join(p.get_text() for p in pages)

    terrain_types = ["AREA TERRAIN", "DENSE", "OBSCURING", "DEFENSIVE",
                     "HIDDEN AND OBSCURING"]
    result = {}
    for ttype in terrain_types:
        m = re.search(rf'{re.escape(ttype)}\s+\d+\.\d+\s*(.*?)(?=\n[A-Z]+\s+\d+\.\d+|\Z)', text, re.DOTALL)
        if m:
            result[ttype.lower().replace(" ", "_")] = re.sub(r'\s+', ' ', m.group(1)).strip()[:500]

    return result


# ---------------------------------------------------------------------------
# Main parse
# ---------------------------------------------------------------------------

def parse_core_rules(pdf_path: str | Path) -> dict:
    """Parse the 11e Core Rules PDF into structured data."""
    doc = fitz.open(str(pdf_path))

    # Group pages by section for targeted extraction
    pages_by_section = {}
    current_section = "preamble"
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text()

        # Detect section changes: a section starts when the marker is a
        # heading line (not just a running header). Headings are all-caps
        # lines containing the marker, possibly prefixed by a page number.
        lines = text.strip().split("\n")
        # Find first non-empty, non-numeric line (skip page numbers)
        first_meaningful = ""
        for ln in lines:
            s = ln.strip()
            if s and not s.isdigit() and not s.startswith("++"):
                first_meaningful = s
                break
        first_upper = first_meaningful.upper()
        for marker, section in sorted(SECTION_MARKERS.items(), key=lambda x: -len(x[0])):
            if first_upper.startswith(marker) or first_upper == marker:
                    current_section = section
                    break

        pages_by_section.setdefault(current_section, []).append(page)

    # Parse each section
    result = {
        "version": "11.0",
        "source": "Warhammer 40,000 11th Edition Core Rules PDF",
        "abilities": [],
        "cover_rules": {},
        "stratagems": [],
        "phases": {},
        "terrain_keywords": {},
        "_meta": {"total_pages": len(doc)},
    }

    # Core abilities from reference pages
    if "core_abilities" in pages_by_section:
        result["abilities"] = extract_abilities(pages_by_section["core_abilities"])

    # Cover rules from terrain pages
    if "terrain" in pages_by_section:
        result["cover_rules"] = extract_cover_rules(pages_by_section["terrain"])

    # Also check advanced_rules for Plunging Fire
    if "advanced_rules" in pages_by_section:
        plunge = extract_cover_rules(pages_by_section["advanced_rules"])
        if plunge.get("plunging_fire"):
            result["cover_rules"]["plunging_fire"] = plunge["plunging_fire"]

    # Stratagems
    if "stratagems" in pages_by_section:
        result["stratagems"] = extract_stratagems(pages_by_section["stratagems"])

    # Phase rules
    phase_sections = ["battle_round", "command_phase", "movement_phase",
                      "shooting_phase", "charge_phase", "fight_phase"]
    phase_pages = []
    for s in phase_sections:
        if s in pages_by_section:
            phase_pages.extend(pages_by_section[s])
    if phase_pages:
        result["phases"] = extract_phase_structure(phase_pages)

    # Terrain keywords
    if "terrain" in pages_by_section:
        result["terrain_keywords"] = extract_terrain_keywords(pages_by_section["terrain"])

    # Index abilities by name for easy lookup
    result["abilities_index"] = {a["name"]: a for a in result["abilities"]}

    # ── Catch rules that span sections ──────────────────────────────
    # Re-read all pages for rules that might be in unexpected sections
    all_text = "\n".join(doc[i].get_text().replace("\x08", "") for i in range(len(doc)))

    if not result["cover_rules"].get("plunging_fire"):
        m = re.search(r'PLUNGING FIRE\s+22\.05\s*(.*?)(?=\n\s*[A-Z][A-Z\s]*\d+\.\d+|\Z)', all_text, re.DOTALL)
        if m:
            result["cover_rules"]["plunging_fire"] = re.sub(r'\s+', ' ', m.group(1)).strip()

    # Copy ability descriptions into cover_rules for convenience
    ability_index = {a["name"]: a for a in result["abilities"]}
    if not result["cover_rules"].get("ignores_cover") and "IGNORES COVER" in ability_index:
        result["cover_rules"]["ignores_cover"] = ability_index["IGNORES COVER"]["description"]

    doc.close()
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    pdf_path = REPO_ROOT / "data" / "core-rules-11e.pdf"
    if not pdf_path.exists():
        print(f"Core rules PDF not found at {pdf_path}", file=sys.stderr)
        print("Download from: https://assets.warhammer-community.com/eng_01-06_warhammer40k_new40k_core_rules-was6fbu1ix-hfewhmxyiy.pdf",
              file=sys.stderr)
        sys.exit(1)

    print(f"Parsing {pdf_path}...", file=sys.stderr)
    data = parse_core_rules(pdf_path)

    out_path = REPO_ROOT / "data" / "core-rules-11e.json"
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f" -> {out_path}", file=sys.stderr)
    print(f"    abilities: {len(data['abilities'])}", file=sys.stderr)
    print(f"    stratagems: {len(data['stratagems'])}", file=sys.stderr)
    print(f"    phases: {list(data['phases'].keys())}", file=sys.stderr)


if __name__ == "__main__":
    main()
