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
                "dp_cost": 3,  # 11e: 3DP (powerful detachment)
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

    # Add 5 codex detachments (not in Faction Pack PDF — rules from codex, DP costs from MFM v1.0)
    _add_codex_detachments(result)

    return result


# ---------------------------------------------------------------------------
# Codex detachments (not in Faction Pack PDF — rules from Wahapedia, DP costs from MFM v1.0)
# ---------------------------------------------------------------------------

def _add_codex_detachments(result: dict):
    """Append the 5 codex detachments to result['detachments']."""

    codex_dets = [
        {
            "name": "AUGURIUM TASK FORCE",
            "description": "",
            "dp_cost": 2,
            "rules": [{"name": "PRESCIENT REDEPLOYMENT", "description": "From the second battle round onwards, at the start of your Movement phase, if you did not select the maximum number of GREY KNIGHTS units from your army using the Gate of Infinity ability at the end of your opponent's previous turn, you can select one GREY KNIGHTS unit from your army that is on the battlefield that could have been selected using the Gate of Infinity ability. Remove that unit from the battlefield and place it into Strategic Reserves."}],
            "enhancements": [
                {"name": "Doomseer's Amulet", "cp_cost": None, "description": "GREY KNIGHTS model only. Each time the bearer's unit is set up in your Reinforcements step, the bearer can use this Enhancement. If it does, select one enemy unit within 12\" of and visible to the bearer. That enemy unit must take a Battle-shock test, subtracting 1 from that test."},
                {"name": "Grimoire of Conjunctions", "cp_cost": None, "description": "GREY KNIGHTS model only. Once per battle, at the start of the Fight phase, the bearer can use this Enhancement. If it does, until the end of the phase, add 4 to the Strength characteristic of melee weapons equipped by the bearer."},
                {"name": "One Foot in the Future", "cp_cost": None, "description": "GREY KNIGHTS model only. Each time the bearer's unit is set up in your Reinforcements step, the bearer can use this Enhancement. If it does, the bearer's unit can make a Normal move of up to D6\", and until the end of the turn, the bearer's unit is not eligible to declare a Charge."},
                {"name": "Shield of Prophecy", "cp_cost": None, "description": "GREY KNIGHTS model only. Once per battle, at the start of the battle round, the bearer can use this Enhancement. If it does, until the end of the battle round, add 2 to the Toughness characteristic of models in the bearer's unit."},
            ],
            "stratagems": [
                {"name": "AGGRESSIVE ANTICIPATION", "cp_cost": 1, "when": "Your Shooting phase or the Fight phase.", "target": "One GREY KNIGHTS PSYKER unit from your army that has not been selected to shoot or fight this phase.", "effect": "Until the end of the phase, each time a model in your unit makes an attack, you can ignore any or all modifiers to that attack's Weapon Skill or Ballistic Skill characteristics and/or any or all modifiers to the Hit roll."},
                {"name": "APPOINTED HOUR", "cp_cost": 1, "when": "Your Shooting phase or the Fight phase.", "target": "One GREY KNIGHTS PSYKER unit from your army that has not been selected to shoot or fight this phase.", "effect": "Until the end of the phase, each time a model in your unit makes an attack, an unmodified Hit roll of 5+ scores a Critical Hit."},
                {"name": "FOREWARNED EVASION", "cp_cost": 1, "when": "Your opponent's Shooting phase or the Fight phase, just after an enemy unit has selected its targets.", "target": "One GREY KNIGHTS WALKER unit from your army that was selected as the target of one or more of the attacking unit's attacks.", "effect": "Until the end of the phase, each time an attack targets your unit, subtract 1 from the Hit roll."},
                {"name": "NECESSARY END", "cp_cost": 1, "when": "Fight phase, just after an enemy unit has selected its targets.", "target": "One GREY KNIGHTS INFANTRY unit from your army that was selected as the target of one or more of the attacking unit's attacks.", "effect": "Until the end of the phase, each time a model in your unit is destroyed, if that model has not fought this phase, roll one D6. If the result is greater than the current battle round number, do not remove the destroyed model from play; it can fight after the attacking unit has finished making its attacks, and is then removed from play."},
                {"name": "REDIRECTED STRIKE", "cp_cost": 1, "when": "End of your Command phase.", "target": "One GREY KNIGHTS PSYKER unit from your army that is not within Engagement Range of one or more enemy units.", "effect": "If your unit has the Deep Strike ability, it can be placed into Strategic Reserves."},
                {"name": "MIRAGE OF ECHOES", "cp_cost": 1, "when": "The Reinforcements step of your opponent's Movement phase, just after an enemy unit is set up.", "target": "One GREY KNIGHTS PSYKER unit from your army that is within 12\" of that enemy unit and is not within Engagement Range of one or more enemy units.", "effect": "If your unit has the Deep Strike ability, it can be placed into Strategic Reserves."},
            ],
        },
        {
            "name": "BANISHERS",
            "description": "",
            "dp_cost": 2,
            "rules": [{"name": "CHANNELLED FORCE", "description": "Each time a GREY KNIGHTS unit from your army is selected to fight, that unit can take a Leadership test. If that test is passed, select one of the following rules until the end of the phase: (a) Melee weapons equipped by models in this unit with the [psychic] ability also have the [SUSTAINED HITS 1] ability; (b) Melee weapons equipped by models in this unit with the [psychic] ability also have the [LETHAL HITS] ability."}],
            "enhancements": [
                {"name": "Sigil of the Hunt", "cp_cost": None, "description": "GREY KNIGHTS model only. In your Shooting phase, each time a model in the bearer's unit makes an attack, re-roll a Hit roll of 1."},
                {"name": "Ephemeral Tome", "cp_cost": None, "description": "GREY KNIGHTS INFANTRY model only. At the start of your Shooting phase, if the bearer's unit is not within Engagement Range of one or more enemy units, the bearer can use this Enhancement. If it does, the bearer's unit can make a Normal move of up to D6\", and until the end of the turn, the bearer's unit is not eligible to declare a charge."},
                {"name": "Sixty-sixth Seal", "cp_cost": None, "description": "GREY KNIGHTS model only. In your Shooting phase, each time a model in the bearer's unit makes an attack, improve the Armour Penetration characteristic of that attack by 1."},
                {"name": "Pyresoul", "cp_cost": None, "description": "GREY KNIGHTS model only. At the start of your Shooting phase, the bearer can use this Enhancement. If it does, select one enemy unit within 24\" of and visible to the bearer; that unit suffers D3 mortal wounds."},
            ],
            "stratagems": [
                {"name": "HEXWROUGHT REPRISAL", "cp_cost": 1, "when": "End of any phase.", "target": "One GREY KNIGHTS PSYKER unit from your army that is on the battlefield and suffered one or more mortal wounds this phase.", "effect": "Select one enemy unit which inflicted one or more mortal wounds on your unit this phase, then roll a number of dice equal to the number of mortal wounds your unit suffered this phase: for each 2+, that enemy unit suffers one mortal wound (to a maximum of 6 mortal wounds). These mortal wounds are Psychic Attacks."},
                {"name": "WARDING CHANT", "cp_cost": 1, "when": "Your opponent's Shooting phase or the Fight phase, just after an enemy unit has selected its targets.", "target": "One GREY KNIGHTS PSYKER unit from your army that was selected as the target of one or more of the attacking unit's attacks.", "effect": "Until the end of the phase, models in your unit have the Feel No Pain 5+ ability against attacks with an unmodified Damage characteristic of 1."},
                {"name": "CHAOS BANE", "cp_cost": 1, "when": "Your Shooting phase.", "target": "One GREY KNIGHTS PSYKER unit from your army that has not been selected to shoot this phase.", "effect": "Until the end of the phase, ranged weapons equipped by models in your unit have the [ANTI-CHAOS 4+] ability."},
                {"name": "CELERITY", "cp_cost": 1, "when": "Your Charge phase.", "target": "One GREY KNIGHTS PSYKER INFANTRY unit from your army.", "effect": "Until the end of the turn, your unit is eligible to declare a charge in a turn in which it Advanced."},
                {"name": "CIRCLE OF SANCTUARY", "cp_cost": 1, "when": "Start of your opponent's Movement phase.", "target": "One GREY KNIGHTS CHARACTER model from your army.", "effect": "Until the end of the phase, enemy units that are set up on the battlefield as Reinforcements cannot be set up within 12\" horizontally of your model."},
                {"name": "SHADOW OF ANARCH", "cp_cost": 1, "when": "Your opponent's Movement phase, just after an enemy unit ends a Normal, Advance or Fall Back move.", "target": "One GREY KNIGHTS PSYKER unit from your army that is within 9\" of that enemy unit and is not within Engagement Range of one or more enemy units.", "effect": "Your unit can make a Normal move of up to 6\" or, if it has the Deep Strike ability, it can be placed into Strategic Reserves."},
            ],
        },
        {
            "name": "BROTHERHOOD STRIKE",
            "description": "",
            "dp_cost": 2,
            "rules": [{"name": "FURY OF TITAN", "description": "Each time a unit from your army is set up using the Deep Strike ability, until the end of the turn, each time a model in that unit makes an attack, re-roll a Hit roll of 1 and re-roll a Wound roll of 1."}],
            "enhancements": [
                {"name": "Banishing Wave", "cp_cost": None, "description": "GREY KNIGHTS model only. Each time the bearer's unit is set up using the Deep Strike ability, roll one D6 for each enemy unit within 12\" of the bearer: on a 2-5, that unit suffers 1 mortal wound; on a 6, that unit suffers D3 mortal wounds."},
                {"name": "Blinding Aura", "cp_cost": None, "description": "GREY KNIGHTS model only. Each time the bearer's unit is set up using the Deep Strike ability, until the end of the turn, enemy units cannot use the Fire Overwatch Stratagem to shoot at the bearer's unit."},
                {"name": "Purity of Purpose", "cp_cost": None, "description": "GREY KNIGHTS model only. Each time the bearer's unit is set up using the Deep Strike ability, until the end of the turn, you can re-roll Charge rolls made for the bearer's unit."},
                {"name": "Tome of Forbidden Ways", "cp_cost": None, "description": "GREY KNIGHTS model only. While the bearer is on the battlefield or in Strategic Reserves, add 1 to the number of units from your army that you can select for the Gate of Infinity rule."},
            ],
            "stratagems": [
                {"name": "TRUESILVER CHANNELLING", "cp_cost": 2, "when": "Fight phase.", "target": "One GREY KNIGHTS INFANTRY unit from your army that has not been selected to fight this phase.", "effect": "Until the end of the phase, Psychic weapons equipped by models in your unit have the [DEVASTATING WOUNDS] ability."},
                {"name": "COMBAT MANIFESTATION", "cp_cost": 1, "when": "Your Movement phase.", "target": "One GREY KNIGHTS unit from your army that is arriving using the Deep Strike ability this phase.", "effect": "Set your unit up anywhere on the battlefield that is more than 6\" horizontally away from all enemy units, but until the end of the turn, it is not eligible to declare a charge."},
                {"name": "PURGATION PATTERN", "cp_cost": 1, "when": "Your Shooting phase.", "target": "One GREY KNIGHTS unit from your army that was set up using the Deep Strike ability this turn and has not been selected to shoot this phase.", "effect": "Until the end of the phase, weapons equipped by models in your unit have the [SUSTAINED HITS 1] ability."},
                {"name": "DUTY UNENDING", "cp_cost": 1, "when": "Your opponent's Movement phase, just after an enemy unit within Engagement Range of one or more GREY KNIGHTS units from your army Falls Back.", "target": "One of those GREY KNIGHTS units that is not within Engagement Range of one or more enemy units.", "effect": "If your unit has the Deep Strike ability, it can be placed into Strategic Reserves."},
                {"name": "SHINING VEIL", "cp_cost": 1, "when": "Your opponent's Shooting phase, just after an enemy unit has selected its targets.", "target": "One GREY KNIGHTS unit that was selected as the target of one or more of the attacking unit's attacks.", "effect": "Until the end of the phase, your unit has the Stealth ability."},
                {"name": "EXPEDITIOUS EXIT", "cp_cost": 2, "when": "End of your opponent's Fight phase.", "target": "One GREY KNIGHTS PSYKER INFANTRY unit from your army.", "effect": "If every model in your unit has the Deep Strike ability, remove your unit from the battlefield and place it into Strategic Reserves. This allows you to remove a unit in addition to those removed using the Gate of Infinity rule, including a unit within Engagement Range of one or more enemy units."},
            ],
        },
        {
            "name": "HALLOWED CONCLAVE",
            "description": "",
            "dp_cost": 2,
            "rules": [{"name": "DUTY BEFORE ALL", "description": "GREY KNIGHTS TERMINATOR units from your army are eligible to shoot and declare a charge in a turn in which they Fell Back."}],
            "enhancements": [
                {"name": "Eye of the Augurium", "cp_cost": None, "description": "GREY KNIGHTS model only. Once per battle round, the bearer can use this Enhancement. If it does, you can target the bearer's unit with the Fire Overwatch or Heroic Intervention Stratagem for 0CP, and can do so even if you have already targeted a different unit with that Stratagem this turn."},
                {"name": "Inescapable Judgement", "cp_cost": None, "description": "GREY KNIGHTS model only. Each time an enemy unit within Engagement Range of the bearer's unit Falls Back, the bearer can use this Enhancement. If it does, roll one D6: on a 2-5, that enemy unit suffers D3 mortal wounds; on a 6, that enemy unit suffers D3+3 mortal wounds. These mortal wounds are Psychic Attacks."},
                {"name": "Sanctic Reaper", "cp_cost": None, "description": "GREY KNIGHTS TERMINATOR model only. Add 3 to the Attacks characteristic of the bearer's melee weapons."},
                {"name": "Nemesis Rounds", "cp_cost": None, "description": "GREY KNIGHTS TERMINATOR model only. Each time you target the bearer's unit with the Fire Overwatch Stratagem, hits are scored on unmodified Hit rolls of 5+ while resolving that Stratagem."},
            ],
            "stratagems": [
                {"name": "GIANTS OF THE BATTLEFIELD", "cp_cost": 1, "when": "Fight phase.", "target": "One GREY KNIGHTS TERMINATOR unit from your army that has not been selected to fight this phase.", "effect": "Until the end of the phase, add 1 to the Attacks characteristic of melee weapons equipped by models in your unit."},
                {"name": "UNENDING FIDELITY", "cp_cost": 1, "when": "Your opponent's Shooting phase or the Fight phase, just after an enemy unit has selected its targets.", "target": "One GREY KNIGHTS INFANTRY unit from your army that was selected as the target of one or more of the attacking unit's attacks.", "effect": "Until the end of the phase, each time a model in your unit is destroyed, if that model has not shot or fought this phase, roll one D6. On a 4+, do not remove the destroyed model from play; it can shoot or fight after the attacking unit has finished making its attacks, and is then removed from play."},
                {"name": "POINT-BLANK PURGATION", "cp_cost": 1, "when": "Your Shooting phase.", "target": "One GREY KNIGHTS INFANTRY unit from your army that has not been selected to shoot this phase.", "effect": "Until the end of the phase, storm bolter weapons equipped by models in your unit have the [PISTOL] and [TWIN-LINKED] abilities."},
                {"name": "GRIND THEM UNDERFOOT", "cp_cost": 1, "when": "Your Charge phase, just after a GREY KNIGHTS TERMINATOR unit from your army ends a Charge move.", "target": "That GREY KNIGHTS unit.", "effect": "Select one enemy unit within Engagement Range of your unit, then roll one D6 for each model in your unit that is within Engagement Range of that enemy unit: for each 4+, that enemy unit suffers 1 mortal wound (to a maximum of 6 mortal wounds)."},
                {"name": "PRECOGNITIVE STRATEGIES", "cp_cost": 1, "when": "Your opponent's Movement phase, just after an enemy unit ends a Normal, Advance or Fall Back move.", "target": "One GREY KNIGHTS INFANTRY unit from your army that is within 9\" of that enemy unit and not within Engagement Range of one or more enemy units.", "effect": "Your unit can make a Normal move of up to D6\"."},
                {"name": "SHINING RESOLVE", "cp_cost": 1, "when": "Your opponent's Shooting phase, just after an enemy unit has selected its targets.", "target": "One GREY KNIGHTS INFANTRY unit from your army that was selected as the target of one or more of the attacking unit's attacks.", "effect": "Until the end of the phase, each time an attack targets your unit, if the Strength characteristic of that attack is greater than the Toughness characteristic of your unit, subtract 1 from the Wound roll."},
            ],
        },
        {
            "name": "SANCTIC SPEARHEAD",
            "description": "",
            "dp_cost": 2,
            "rules": [{"name": "MAILED FIST", "description": "Each time a GREY KNIGHTS VEHICLE unit from your army Advances, do not make an Advance roll for it; until the end of the phase, add 6\" to the Move characteristic of models in that unit, and until the end of the turn, ranged weapons equipped by models in that unit have the [ASSAULT] ability."}],
            "enhancements": [
                {"name": "Driven by Duty", "cp_cost": None, "description": "GREY KNIGHTS WALKER model only. Each time the bearer's unit Piles In or Consolidates, the bearer can move up to 6\" instead of up to 3\"."},
                {"name": "Quickening Foci", "cp_cost": None, "description": "GREY KNIGHTS INFANTRY model only. In your Movement phase, each time the bearer's unit disembarks from a TRANSPORT, until the end of the turn, you can re-roll Charge rolls made for that unit."},
                {"name": "Sigil of Exigence", "cp_cost": None, "description": "GREY KNIGHTS model only. Once per battle, in your opponent's Shooting phase, when the bearer's unit is selected as the target of a ranged attack, you can remove the bearer's unit from the battlefield and then set it back up again anywhere on the battlefield that is more than 9\" horizontally away from all enemy units. If the bearer's unit is no longer an eligible target, your opponent can then select new targets for any attacks that had targeted the bearer's unit."},
                {"name": "Spiritus Machina", "cp_cost": None, "description": "GREY KNIGHTS INFANTRY model only. In your Shooting phase, each time the bearer's unit is selected to shoot, if the bearer's unit disembarked from a TRANSPORT this turn, until the end of the phase, each time a model in the bearer's unit makes an attack, you can re-roll the Wound roll."},
            ],
            "stratagems": [
                {"name": "TRUESILVER WILL", "cp_cost": 1, "when": "Any phase, just after a GREY KNIGHTS PSYKER VEHICLE unit from your army suffers a mortal wound.", "target": "That GREY KNIGHTS PSYKER VEHICLE unit.", "effect": "Until the end of the phase, models in your unit have the Feel No Pain 4+ ability against mortal wounds."},
                {"name": "ABOMINUS-CLASS TARGETS", "cp_cost": 1, "when": "Your Shooting phase or the Fight phase.", "target": "One GREY KNIGHTS unit from your army that has not been selected to shoot or fight this phase.", "effect": "Until the end of the phase, each time a model in your unit makes an attack that targets a MONSTER or VEHICLE unit, add 1 to the Wound roll."},
                {"name": "ARMOURED AEGIS", "cp_cost": 1, "when": "Your Command phase.", "target": "One GREY KNIGHTS PSYKER VEHICLE unit from your army.", "effect": "One model in your unit regains up to 3 lost wounds."},
                {"name": "REDOUBLED ASSAULT", "cp_cost": 1, "when": "Your Movement phase, just after a GREY KNIGHTS VEHICLE unit from your army Falls Back.", "target": "That GREY KNIGHTS VEHICLE unit.", "effect": "Until the end of the turn, your unit is eligible to shoot and declare a charge in a turn in which it Fell Back."},
                {"name": "FORCE WAVE", "cp_cost": 1, "when": "Your Movement phase or your Charge phase.", "target": "One GREY KNIGHTS VEHICLE unit from your army that has not been selected to move or charge this phase.", "effect": "Until the end of the phase, each time your unit makes a Normal, Advance or Charge move, it can move horizontally through terrain features."},
                {"name": "ARGENT WRATH", "cp_cost": 1, "when": "Your Charge phase, just after a GREY KNIGHTS VEHICLE unit from your army ends a Charge move.", "target": "That GREY KNIGHTS VEHICLE unit.", "effect": "Each enemy unit within 3\" of your unit must take a Battle-shock test, subtracting 1 from that test."},
            ],
        },
    ]

    for det in codex_dets:
        if det["name"] not in [d["name"] for d in result["detachments"]]:
            result["detachments"].append(det)


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
