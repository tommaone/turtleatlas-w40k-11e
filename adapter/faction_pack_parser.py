"""
11e Faction Pack PDF parser.

Extracts structured data from Faction Pack PDFs for use in DPP engine + MCP server.
Supports: datasheets, detachments, enhancements, stratagems, rules updates.

Sources:
  https://assets.warhammer-community.com/...-faction-pack.pdf
"""

import json
import re
import sys
from pathlib import Path

import fitz  # pymupdf

REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Datasheet parser
# ---------------------------------------------------------------------------

def parse_datasheet_text(text: str) -> dict | None:
    """Parse a single datasheet from raw text lines."""
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    if not lines:
        return None

    name = None
    keywords = []
    faction_keywords = []
    weapons = {"ranged": [], "melee": []}
    stats = {}
    abilities = {"core": [], "faction": [], "wargear": []}
    damaged_profile = None
    transport_info = None
    current_section = None

    # Detect section transitions
    section_headers = {
        "RANGED WEAPONS": ("weapons_ranged", False),
        "MELEE WEAPONS": ("weapons_melee", False),
        "ABILITIES": ("abilities", False),
        "CORE:": ("abilities_core", False),
        "WARGEAR ABILITIES": ("abilities_wargear", False),
        "DAMAGED:": ("damaged", False),
        "FACTION KEYWORDS:": ("faction_keywords", False),
        "KEYWORDS:": ("keywords", True),
        "TRANSPORT": ("transport", False),
        "WARGEAR OPTIONS": ("wargear_options", False),
        "UNIT COMPOSITION": ("unit_composition", False),
    }

    # Known stat fields (in order they appear in datasheet blocks)
    stat_fields_ranged = ["RANGE", "A", "BS", "S", "AP", "D"]
    stat_fields_melee = ["RANGE", "A", "WS", "S", "AP", "D"]
    stat_fields_profile = ["T", "SV", "W", "LD", "OC", "M"]

    i = 0
    line_count = len(lines)

    # First non-empty line is usually the datasheet name
    name = lines[0] if lines[0] and not lines[0].startswith(("KEYWORDS:", "WARGEAR", "UNIT")) else None

    # Check if first line looks like a datasheet name (all-caps, no colon)
    if name and ":" not in name and not name.startswith("WARHAMMER"):
        pass  # Use as name
    else:
        name = None

    weapon_mode = None  # "ranged" or "melee"
    current_weapon = None
    stat_idx = 0
    header_fields = []

    for i in range(len(lines)):
        line = lines[i]

        # Skip empty, fluff lines (start with lowercase, long sentences)
        if (line[0].islower() and len(line) > 40) or line.startswith("++"):
            continue

        # Section detection
        found_section = False
        for marker, (sec, keep) in sorted(section_headers.items(), key=lambda x: -len(x[0])):
            if line.upper().startswith(marker):
                current_section = sec
                found_section = True
                if sec == "weapons_ranged":
                    weapon_mode = "ranged"
                    header_fields = stat_fields_ranged
                    stat_idx = -1
                    current_weapon = None
                elif sec == "weapons_melee":
                    weapon_mode = "melee"
                    header_fields = stat_fields_melee
                    stat_idx = -1
                    current_weapon = None
                elif sec == "damaged":
                    # Damaged: 1-10 WOUNDS REMAINING
                    damaged_profile = {"threshold": None, "effect": None}
                break
        if found_section:
            continue

        # Keywords: line
        if line.upper().startswith("KEYWORDS:") or current_section == "keywords":
            if line.upper().startswith("KEYWORDS:"):
                val = line.split(":", 1)[1].strip()
                keywords = [k.strip() for k in val.split(",") if k.strip()]
            current_section = None
            continue

        if line.upper().startswith("FACTION KEYWORDS:"):
            val = line.split(":", 1)[1].strip()
            faction_keywords = [k.strip() for k in val.split(",") if k.strip()]
            continue

        # Transport
        if line.upper().startswith("TRANSPORT"):
            transport_info = line
            continue

        # Weapons parsing — tabular data
        if weapon_mode and header_fields:
            # Check if this line is a stat header
            if line in header_fields:
                stat_idx = 0
                continue

            # Check if this line is a weapon name (not a stat value)
            # Weapon names contain letters, special chars like [ ]
            if not line.replace(".", "").replace('"', "").replace("+", "").replace("-", "").isdigit() and not line.startswith(("Melee", "Range")):
                # Check if this looks like a weapon (contains letters, maybe brackets)
                if any(c.isalpha() for c in line) and not line.startswith(("RANGE", "A ", "BS", "WS", "S ", "AP", "D ")):
                    if current_weapon:
                        weapons[weapon_mode].append(current_weapon)
                    current_weapon = {"name": line, "stats": {}}
                    stat_idx = 0
                    continue

            # This line is a stat value
            if current_weapon and stat_idx < len(header_fields):
                field = header_fields[stat_idx]
                current_weapon["stats"][field] = line
                stat_idx += 1
                continue

        # Abilities
        if current_section and current_section.startswith("abilities"):
            # Core abilities line
            if line.upper().startswith("CORE:") or current_section == "abilities_core":
                if line.upper().startswith("CORE:"):
                    core_text = line.split(":", 1)[1].strip()
                else:
                    core_text = line
                abilities["core"] = [a.strip() for a in re.split(r'[,;]', core_text) if a.strip()]
                continue

            if current_section == "abilities_wargear":
                # Wargear abilities: "Name: description"
                m = re.match(r'^([^:]+):\s*(.*)', line)
                if m:
                    abilities["wargear"].append({"name": m.group(1).strip(), "description": m.group(2).strip()})
                continue

        # Stat profile (T, SV, W, LD, OC, M)
        # These are single values, usually found after abilities section

    # Don't forget last weapon
    if current_weapon and current_weapon.get("name"):
        weapons[weapon_mode].append(current_weapon)

    # --- Profile stat block ---
    # Stats appear at the bottom of the datasheet as a block
    # Look for T, SV, W, LD, OC, M sequence in remaining text
    remaining = "\n".join(lines)
    t_match = re.search(r'(?:^|\n)\s*(\d+)\s*\n\s*(\d+[+]?)\s*\n\s*(\d+)\s*\n\s*(\d+[+]?)\s*\n\s*(\d+)\s*\n\s*(\d+["]?)\s*\n\s*M', remaining)
    if t_match:
        stats = {
            "T": t_match.group(1),
            "SV": t_match.group(2),
            "W": t_match.group(3),
            "LD": t_match.group(4),
            "OC": t_match.group(5),
            "M": t_match.group(6),
        }
    else:
        # Fallback: look for stat values near "T" / "SV" labels
        pass

    if not name:
        return None

    return {
        "name": name,
        "keywords": keywords,
        "faction_keywords": faction_keywords,
        "stats": stats,
        "weapons": weapons,
        "abilities": abilities,
        "damaged_profile": damaged_profile,
        "transport": transport_info,
    }


# ---------------------------------------------------------------------------
# Detachment parser
# ---------------------------------------------------------------------------

def parse_detachment(lines: list, start_idx: int) -> tuple[dict | None, int]:
    """Parse a detachment block starting at start_idx. Returns (detachment, next_idx)."""
    name = lines[start_idx].strip()
    i = start_idx + 1
    detachment = {
        "name": name,
        "description": "",
        "rules": [],
        "enhancements": [],
        "stratagems": [],
        "dp_cost": 1,  # default: 1 DP per detachment
    }
    current_section = None
    current_enhancement = None
    current_stratagem = None

    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        # Detect section transitions
        if line == "DETACHMENT RULES" or line == "DETACHMENT RULE":
            current_section = "rules"
            i += 1
            continue
        elif line == "ENHANCEMENTS":
            current_section = "enhancements"
            i += 1
            continue
        elif line == "STRATAGEMS":
            current_section = "stratagems"
            i += 1
            continue

        # Stop at next detachment or known section end
        if line in ("ARGENT ASSAULT", "FIRES OF PURGATION", "IMMATERIAL INTERDICTION",
                    "WARPBANE TASK FORCE", "WARGEAR OPTIONS", "RULES UPDATES",
                    "WARHAMMER L E G E N D S", "GREY KNIGHTS"):
            if line != name:  # Don't stop on our own name
                break

        if current_section == "rules":
            # Skip fluff (long lowercase sentences)
            if line[0].islower() and len(line) > 30:
                i += 1
                continue
            # Check if this is a rule name (all caps)
            if line.isupper() and not line.startswith("WHEN:") and not line.startswith("TARGET:") and not line.startswith("EFFECT:"):
                detachment["rules"].append({"name": line, "description": ""})
            elif detachment["rules"]:
                detachment["rules"][-1]["description"] += " " + line
            else:
                # Description before first rule name
                pass
            i += 1

        elif current_section == "enhancements":
            # After ENHANCEMENTS, we have a mix of enhancements and stratagems.
            # Each item starts with an all-caps name. Peek ahead to distinguish:
            #   - Followed by "XCP" → stratagem
            #   - Followed by fluff text → enhancement
            # Skip fluff lines
            if line[0].islower() and len(line) > 30:
                i += 1
                continue

            # CP cost line — handle BEFORE name detection
            cp_match = re.match(r'^(\d+)CP', line)
            if cp_match:
                if current_stratagem:
                    current_stratagem["cp_cost"] = int(cp_match.group(1))
                i += 1
                continue

            # Bullet point — append to current description (before name detection,
            # because bullet lines can look like uppercase names)
            if line.startswith(("▪", "■", "•", "●")):
                if current_enhancement:
                    current_enhancement["description"] += " " + line
                elif current_stratagem and current_stratagem.get("effect"):
                    current_stratagem["effect"] += " " + line
                i += 1
                continue

            if line.isupper() and len(line) > 2 and not line.startswith("WHEN:") and not re.match(r'^\d+CP', line) and "STRATAGEM" not in line.upper() and len(line) < 60:
                # Peek ahead: check if next non-empty line is CP cost
                next_line = ""
                for k in range(i + 1, min(i + 5, len(lines))):
                    candidate = lines[k].strip()
                    if candidate and not (candidate[0].islower() and len(candidate) > 30):
                        next_line = candidate
                        break
                cp_match = re.match(r'^(\d+)CP', next_line) if next_line else None
                if cp_match or "STRATAGEM" in (next_line or "").upper():
                    # ── This is a stratagem ──
                    if current_stratagem and current_stratagem.get("name"):
                        detachment["stratagems"].append(current_stratagem)
                    current_stratagem = {"name": line, "cp_cost": None, "when": "", "target": "", "effect": ""}
                    i += 1
                    continue
                else:
                    # ── This is an enhancement ──
                    if current_enhancement and current_enhancement["name"]:
                        detachment["enhancements"].append(current_enhancement)
                    current_enhancement = {"name": line, "cp_cost": None, "description": ""}
                    i += 1
                    continue

            # Stratagem type line
            if "STRATAGEM" in line.upper() and current_stratagem:
                i += 1
                continue

            # WHEN / TARGET / EFFECT for stratagems within enhancements section
            if line.startswith("WHEN:") and current_stratagem:
                current_stratagem["when"] = line[5:].strip()
                i += 1
                continue
            if line.startswith("TARGET:") and current_stratagem:
                current_stratagem["target"] = line[7:].strip()
                i += 1
                continue
            if line.startswith("EFFECT:") and current_stratagem:
                current_stratagem["effect"] = line[7:].strip()
                i += 1
                continue

            # Description text for enhancement or stratagem continuation
            if current_enhancement:
                current_enhancement["description"] += " " + line
            elif current_stratagem:
                # Append to the most recently filled field
                if current_stratagem.get("effect"):
                    current_stratagem["effect"] += " " + line
                elif current_stratagem.get("target"):
                    current_stratagem["target"] += " " + line
                elif current_stratagem.get("when"):
                    current_stratagem["when"] += " " + line
            i += 1

        else:
            i += 1

    # Finalize last enhancement/stratagem
    if current_enhancement and current_enhancement["name"]:
        detachment["enhancements"].append(current_enhancement)
    if current_stratagem and current_stratagem["name"]:
        detachment["stratagems"].append(current_stratagem)

    # Clean up descriptions
    for rule in detachment["rules"]:
        rule["description"] = ' '.join(rule["description"].split()).strip()
    for enh in detachment["enhancements"]:
        enh["description"] = ' '.join(enh["description"].split()).strip()
    for strat in detachment["stratagems"]:
        for field in ["when", "target", "effect"]:
            strat[field] = ' '.join(strat[field].split()).strip()

    return detachment, i


# ---------------------------------------------------------------------------
# Rules updates parser
# ---------------------------------------------------------------------------

def parse_rules_updates(lines: list, start_idx: int) -> list:
    """Parse the rules updates section."""
    updates = []
    i = start_idx
    current_update = None

    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        # Stop at next major section
        if line in ("WARHAMMER L E G E N D S", "GREY KNIGHTS") and i > start_idx + 1:
            break

        # Detect update target (datasheet name in all-caps)
        # Skip section headers like UPDATES, DATASHEETS
        if line in ("UPDATES", "DATASHEETS"):
            i += 1
            continue
        if line.isupper() and len(line) > 5 and not line.startswith("USING"):
            if current_update:
                updates.append(current_update)
            current_update = {"target": line, "changes": []}
            i += 1
            continue

        # Change description
        if current_update and line.startswith(("▪", "Change", "Add", "Remove", "Core", "Profile", "Keywords")):
            current_update["changes"].append(line)
            i += 1
            continue

        # Continuation of previous change
        if current_update and current_update["changes"] and not line.isupper():
            current_update["changes"][-1] += " " + line
            i += 1
            continue

        i += 1

    if current_update:
        updates.append(current_update)

    return updates


# ---------------------------------------------------------------------------
# Main parse
# ---------------------------------------------------------------------------

def parse_faction_pack(pdf_path: str | Path) -> dict:
    """Parse a Faction Pack PDF into structured data."""
    doc = fitz.open(str(pdf_path))

    # Split into sections
    text = []
    for i in range(len(doc)):
        ptext = doc[i].get_text().replace("\x08", "")
        lines = ptext.split("\n")
        for ln in lines:
            s = ln.strip()
            if s:
                text.append(s)

    result = {
        "faction": "",
        "version": "",
        "detachments": [],
        "datasheets": [],
        "rules_updates": [],
        "wargear_options": [],
    }

    # Extract faction name and version from first page
    if text:
        result["faction"] = text[0]  # "GREY KNIGHTS"
    # Find version line
    for line in text[:10]:
        m = re.match(r'FACTION PACK:\s*VERSION\s+([\d.]+)', line)
        if m:
            result["version"] = m.group(1)
            break

    # Parse sections
    i = 0
    while i < len(text):
        line = text[i]

        # Detachments
        if line in ("ARGENT ASSAULT", "FIRES OF PURGATION", "IMMATERIAL INTERDICTION"):
            det, i = parse_detachment(text, i)
            if det:
                result["detachments"].append(det)
            continue

        # Warpbane Task Force (spans 2 pages)
        if line == "WARPBANE TASK FORCE":
            det = {
                "name": "WARPBANE TASK FORCE",
                "description": "",
                "rules": [],
                "enhancements": [],
                "stratagems": [],
                "dp_cost": 2,  # existing detachment from 10e
            }
            j = i + 1
            current_section = None
            current_enh = None
            current_strat = None
            strat_cp_queue = []  # CP costs from end-of-page column

            while j < len(text):
                l2 = text[j]
                if l2 in ("WARGEAR OPTIONS", "RULES UPDATES", "WARHAMMER L E G E N D S"):
                    break
                # Stop when we hit a datasheet (keyword section, weapon table)
                if l2.startswith("RANGED WEAPONS") or l2.startswith("KEYWORDS:") or l2.startswith("MELEE WEAPONS"):
                    break
                # Detect datasheet name: all-caps line followed by KEYWORDS: or RANGED
                if l2.isupper() and len(l2) > 10:
                    found_ds = False
                    for k in range(j + 1, min(j + 5, len(text))):
                        if text[k].startswith("KEYWORDS:") or text[k].startswith("RANGED"):
                            found_ds = True
                            break
                    if found_ds:
                        break

                # Section headers
                if l2 in ("DETACHMENT RULE", "DETACHMENT RULES"):
                    current_section = "rules"
                    j += 1
                    continue
                if l2 == "ENHANCEMENTS":
                    current_section = "enhancements"
                    j += 1
                    continue

                # CP cost column (e.g., "1CP" at bottom of page)
                cp_m = re.match(r'^(\d+)CP$', l2)
                if cp_m:
                    strat_cp_queue.append(int(cp_m.group(1)))
                    j += 1
                    continue

                if current_section == "rules":
                    if l2.isupper() and len(l2) > 3 and l2 not in ("DETACHMENT RULE", "DETACHMENT RULES"):
                        det["rules"].append({"name": l2, "description": ""})
                    elif det["rules"]:
                        det["rules"][-1]["description"] += " " + l2

                elif current_section == "enhancements":
                    # Detect transition to stratagems: if line is all-caps, long-ish,
                    # and peek-ahead doesn't find another enhancement pattern
                    if l2.isupper() and len(l2) > 3 and l2 != "ENHANCEMENTS":
                        # Peek ahead for STRATAGEM type indicator
                        next_nonskip = ""
                        for k in range(j + 1, min(j + 4, len(text))):
                            c = text[k].strip()
                            if c and not (c[0].islower() and len(c) > 30):
                                next_nonskip = c
                                break
                        if "STRATAGEM" in next_nonskip.upper():
                            # ── Stratagem block ──
                            current_section = "stratagems"
                            if current_enh and current_enh.get("name"):
                                det["enhancements"].append(current_enh)
                                current_enh = None
                            if current_strat and current_strat.get("name"):
                                det["stratagems"].append(current_strat)
                            current_strat = {"name": l2, "cp_cost": None, "when": "", "target": "", "effect": ""}
                            j += 1
                            continue
                        else:
                            # Enhancement
                            if current_enh and current_enh.get("name"):
                                det["enhancements"].append(current_enh)
                            current_enh = {"name": l2, "cp_cost": None, "description": ""}
                            j += 1
                            continue

                    # Description for enhancement
                    if current_enh:
                        current_enh["description"] += " " + l2
                    j += 1
                    continue

                elif current_section == "stratagems":
                    # New stratagem name (all caps, not a type label)
                    if l2.isupper() and len(l2) > 3 and "STRATAGEM" not in l2.upper() and not l2.startswith("WHEN:"):
                        # Check it's not a type label
                        next_nonskip = ""
                        for k in range(j + 1, min(j + 4, len(text))):
                            c = text[k].strip()
                            if c and not (c[0].islower() and len(c) > 30):
                                next_nonskip = c
                                break
                        if not next_nonskip.startswith("WHEN:") and not next_nonskip.startswith("TARGET:"):
                            # This is a new stratagem name
                            if current_strat and current_strat.get("name"):
                                det["stratagems"].append(current_strat)
                            current_strat = {"name": l2, "cp_cost": None, "when": "", "target": "", "effect": ""}
                            j += 1
                            continue
                    # Stratagem type label (contains STRATAGEM) — skip
                    if "STRATAGEM" in l2.upper() or l2.isdigit():
                        j += 1
                        continue
                    # Stratagem fields
                    if current_strat:
                        if l2.startswith("WHEN:"):
                            current_strat["when"] = l2[5:].strip()
                        elif l2.startswith("TARGET:"):
                            current_strat["target"] = l2[7:].strip()
                        elif l2.startswith("EFFECT:"):
                            current_strat["effect"] = l2[7:].strip()
                        elif l2.startswith(("▪", "■")) and current_strat.get("effect"):
                            current_strat["effect"] += " " + l2
                        elif current_strat.get("effect"):
                            current_strat["effect"] += " " + l2
                        elif current_strat.get("target"):
                            current_strat["target"] += " " + l2
                        elif current_strat.get("when"):
                            current_strat["when"] += " " + l2
                    j += 1
                    continue

                j += 1

            # Assign CP costs from queue to stratagems (in order)
            for idx, cp in enumerate(strat_cp_queue):
                if idx < len(det["stratagems"]):
                    det["stratagems"][idx]["cp_cost"] = cp

            # Finalize
            if current_enh and current_enh.get("name"):
                det["enhancements"].append(current_enh)
            if current_strat and current_strat.get("name"):
                det["stratagems"].append(current_strat)

            for r in det["rules"]:
                r["description"] = ' '.join(r["description"].split()).strip()
            for e in det["enhancements"]:
                e["description"] = ' '.join(e["description"].split()).strip()
            for s in det["stratagems"]:
                for f in ["when", "target", "effect"]:
                    s[f] = ' '.join(s[f].split()).strip()
            result["detachments"].append(det)
            i = j
            continue

        # Rules updates
        if line == "RULES UPDATES":
            updates = parse_rules_updates(text, i + 1)
            result["rules_updates"] = updates
            # Advance past the updates section
            if updates:
                # Find the end by looking for next major section
                j = i + 1
                while j < len(text):
                    if text[j] in ("WARHAMMER L E G E N D S", "GREY KNIGHTS") and j > i + 2:
                        break
                    j += 1
                i = j
            else:
                i += 1
            continue

        # Datasheets — detect by all-caps name followed by KEYWORDS:
        # Skip Legends datasheets (marked by WARHAMMER header)
        if line.isupper() and len(line) > 10 and ":" not in line and not line.startswith("WARHAMMER"):
            next_keywords = False
            for k in range(i + 1, min(i + 5, len(text))):
                if text[k].startswith("KEYWORDS:") or text[k].startswith("RANGED WEAPONS"):
                    next_keywords = True
                    break
            if next_keywords:
                # Skip Legends (pages 9+)
                is_legends = False
                for k in range(max(0, i - 5), i):
                    line_upper = text[k].upper().replace(" ", "")
                    if "LEGENDS" in line_upper and "WARHAMMER" in line_upper:
                        is_legends = True
                        break
                if is_legends:
                    i += 1
                    continue
                # Parse the datasheet block
                ds_text = "\n".join(text[i:i+90])
                ds = parse_datasheet_text(ds_text)
                if ds:
                    result["datasheets"].append(ds)
                i += 1
                continue

        i += 1

    doc.close()

    # Clean up descriptions
    for det in result["detachments"]:
        det["description"] = ' '.join(det.get("description", "").split()).strip()

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    pdf_path = REPO_ROOT / "data" / "grey-knights-faction-pack.pdf"
    if not pdf_path.exists():
        print(f"Faction Pack PDF not found at {pdf_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing {pdf_path}...", file=sys.stderr)
    data = parse_faction_pack(pdf_path)

    out_path = REPO_ROOT / "data" / "grey-knights-faction-pack.json"
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f" -> {out_path}", file=sys.stderr)
    print(f"    detachments: {len(data['detachments'])}", file=sys.stderr)
    for det in data["detachments"]:
        print(f"      - {det['name']}: {len(det['rules'])} rules, {len(det['enhancements'])} enhancements, {len(det['stratagems'])} stratagems", file=sys.stderr)
    print(f"    datasheets: {len(data['datasheets'])}", file=sys.stderr)
    for ds in data["datasheets"]:
        print(f"      - {ds['name']}", file=sys.stderr)
    print(f"    rules_updates: {len(data.get('rules_updates', []))}", file=sys.stderr)


if __name__ == "__main__":
    main()
