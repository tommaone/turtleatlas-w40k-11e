"""
adversarial/deterministic_check.py — pure Python validation, zero LLM.

Compares merged JSON data against structural expectations and domain rules.
Returns structured findings (not opinions).

Usage:
    python3 -m adversarial.deterministic_check --faction grey-knights
    python3 -m adversarial.deterministic_check --all
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MERGED_DIR = REPO_ROOT / "data" / "merged"
MFM_DIR = REPO_ROOT / "mfm" / "data"

import yaml


# ── FINDINGS DATA CLASS ──────────────────────────────────────────

class Finding:
    """A single deterministic finding — no hallucination, no opinion."""

    def __init__(self, unit: str, category: str, field: str,
                 severity: str, message: str):
        self.unit = unit
        self.category = category    # stat|keyword|weapon|ability|rule|missing|structure
        self.field = field
        self.severity = severity    # CRITICAL|MAJOR|MINOR|INFO
        self.message = message

    def to_dict(self):
        return {
            "unit": self.unit,
            "category": self.category,
            "field": self.field,
            "severity": self.severity,
            "message": self.message,
        }


# ── CHECKS ───────────────────────────────────────────────────────

def check_structure(unit: dict, findings: list[Finding]):
    """Check that the unit has the expected structure."""
    name = unit.get("name", "?")
    profile = unit.get("profile")
    if not profile:
        findings.append(Finding(name, "structure", "profile", "CRITICAL",
                                "Missing profile (no profile key or empty)"))
        return None
    return profile


def check_stats_present(unit: dict, profile: dict, findings: list[Finding]):
    """Check that stats exist and have expected keys."""
    name = unit.get("name", "?")
    stats = profile.get("stats", {})
    if not stats:
        findings.append(Finding(name, "stat", "all", "CRITICAL",
                                "Missing stats dict"))
        return

    expected_keys = ["M", "T", "Sv", "W", "LD", "OC"]
    for key in expected_keys:
        val = stats.get(key)
        if val is None or val == "":
            findings.append(Finding(name, "stat", key, "MAJOR",
                                    f"Empty stat {key}"))
        elif key == "M" and val not in ("-",) and not any(c in str(val) for c in '"'):
            # Most movement values should have " suffix
            pass  # Not a hard rule — "-" is valid for aircraft


def check_keywords(unit: dict, profile: dict, findings: list[Finding]):
    """Check that keywords are present and reasonable for the unit type."""
    name = unit.get("name", "?")
    kws = profile.get("keywords", [])
    stats = profile.get("stats", {})

    if not kws:
        findings.append(Finding(name, "keyword", "all", "CRITICAL",
                                "No keywords"))
        return

    has_vehicle = "Vehicle" in kws
    has_infantry = "Infantry" in kws
    has_monster = "Monster" in kws
    has_aircraft = "Aircraft" in kws
    has_battleline = "Battleline" in kws
    has_character = "Character" in kws
    has_epic_hero = "Epic Hero" in kws
    has_psyker = "Psyker" in kws
    has_fly = "Fly" in kws
    has_transport = "Transport" in kws
    has_walker = "Walker" in kws

    # Key structural rules:
    # — Infantry should not also be Vehicle/Monster (exceptions are few)
    # — Vehicle/Monster implies not Infantry
    # — Battleline should have OC=2
    # — Characters should have OC=1

    if has_infantry and has_vehicle:
        findings.append(Finding(name, "keyword", "Vehicle+Infantry", "INFO",
                                "Both Vehicle and Infantry keywords (verify — rare but possible)"))
    if has_infantry and has_monster:
        findings.append(Finding(name, "keyword", "Monster+Infantry", "INFO",
                                "Both Monster and Infantry keywords (verify)"))

    if has_aircraft:
        # Aircraft typically have M="-"
        m_val = stats.get("M", "")
        if m_val not in ("-", ""):
            findings.append(Finding(name, "stat", "M", "MINOR",
                                    f"Aircraft should have M=\"-\", got \"{m_val}\""))
        oc_val = stats.get("OC", "")
        if oc_val not in ("-", "0", ""):
            findings.append(Finding(name, "stat", "OC", "MINOR",
                                    f"Aircraft typically OC 0 or -, got \"{oc_val}\""))

    if has_battleline:
        oc_val = stats.get("OC", "")
        if oc_val != "2":
            findings.append(Finding(name, "stat", "OC", "MINOR",
                                    f"Battleline with OC={oc_val} (expected 2 — verify)"))

    if has_character and not has_epic_hero:
        oc_val = stats.get("OC", "")
        if oc_val not in ("1", ""):
            # Character+Vehicle/Monster can have OC>1 (Knights, Dreadnoughts)
            is_vehicle_or_monster = has_vehicle or has_monster
            sev = "INFO" if is_vehicle_or_monster else "MINOR"
            findings.append(Finding(name, "stat", "OC", sev,
                                    f"Character with OC={oc_val} (expected 1 for infantry — verify)"))

    # Faction keyword check
    faction_kws = [k for k in kws if k.startswith("Faction:")]
    allies_kws = [k for k in kws if k.startswith("Allies:")]
    if not faction_kws and not allies_kws:
        # Skip units with 'Frame' keyword (shared dedicated transports like Drop Pod)
        has_frame = "Frame" in kws
        if not has_frame:
            findings.append(Finding(name, "keyword", "Faction", "CRITICAL",
                                    "No Faction: keyword found"))

    # Named characters (Epic Hero) should have their name in keywords
    if has_epic_hero:
        name_lower = name.lower()
        name_parts = set(name_lower.split())
        kw_lower = set(k.lower() for k in kws)
        # Check if at least one significant word from the name appears in keywords
        # (e.g., "Castellan Crowe" → keyword should contain "Crowe")
        significant = [w for w in name_parts if len(w) > 2 and w not in ("the", "in")]
        if significant and not any(any(part in kw for part in significant) for kw in kw_lower):
            findings.append(Finding(name, "keyword", "EpicHero", "INFO",
                                    f"Epic Hero name \"{name}\" not in keywords: {kws}"))


def check_weapons(unit: dict, profile: dict, findings: list[Finding]):
    """Check that weapons have required fields."""
    name = unit.get("name", "?")
    weapons = profile.get("weapons", [])

    if not weapons:
        findings.append(Finding(name, "weapon", "all", "INFO",
                                "No weapons (verify — may be correct for transports/terrain)"))
        return

    for w in weapons:
        wname = w.get("name", "?")
        profiles = w.get("profiles", [])
        if not profiles:
            findings.append(Finding(name, "weapon", wname, "MAJOR",
                                    f"Weapon \"{wname}\" has no profiles"))
            continue

        for p in profiles:
            pname = p.get("name", wname)
            stats = p.get("stats", {})
            for key in ["Range", "A", "S", "AP", "D"]:
                val = stats.get(key)
                if val is None or val == "":
                    findings.append(Finding(name, "weapon", f"{pname}/{key}", "MAJOR",
                                            f"Weapon \"{pname}\" missing {key}"))
            # Keywords can legitimately be empty ("-", "", or missing) for simple weapons
            kw_val = stats.get("Keywords")
            if kw_val is None:
                findings.append(Finding(name, "weapon", f"{pname}/Keywords", "INFO",
                                        f"Weapon \"{pname}\" missing Keywords field"))


def check_abilities(unit: dict, profile: dict, findings: list[Finding]):
    """Check that abilities have names."""
    name = unit.get("name", "?")
    abilities = profile.get("abilities", [])
    if not abilities:
        findings.append(Finding(name, "ability", "all", "INFO",
                                "No abilities (verify — may be correct)"))
    else:
        for a in abilities:
            if not a.get("name"):
                findings.append(Finding(name, "ability", "name", "MAJOR",
                                        "Ability missing name"))
            if not a.get("description"):
                findings.append(Finding(name, "ability", a.get("name", "?"), "MINOR",
                                        f"Ability \"{a.get('name', '?')}\" missing description"))


def check_rules(unit: dict, profile: dict, findings: list[Finding]):
    """Check that rules exist if expected."""
    name = unit.get("name", "?")
    rules = profile.get("rules", [])
    stats = profile.get("stats", {})
    kws = profile.get("keywords", [])

    # Every real unit should have at least some rules
    # (legitimate exceptions: terrain, tokens)
    if not rules:
        vehicle_kws = any(k in kws for k in ("Vehicle", "Monster", "Aircraft"))
        infantry_kws = "Infantry" in kws
        if vehicle_kws or infantry_kws:
            findings.append(Finding(name, "rule", "all", "INFO",
                                    "No rules (verify)"))


# ── RUNNER ───────────────────────────────────────────────────────

def validate_unit(unit: dict) -> list[dict]:
    """Run all checks on a single unit. Returns list of finding dicts."""
    findings: list[Finding] = []

    profile = check_structure(unit, findings)
    if profile is None:
        return [f.to_dict() for f in findings]

    check_stats_present(unit, profile, findings)
    check_keywords(unit, profile, findings)
    check_weapons(unit, profile, findings)
    check_abilities(unit, profile, findings)
    check_rules(unit, profile, findings)

    return [f.to_dict() for f in findings]


def validate_faction(slug: str) -> dict:
    """Validate all MFM units for a faction."""
    merged_path = MERGED_DIR / f"{slug}.json"
    if not merged_path.exists():
        return {"slug": slug, "error": "no merged data", "findings": []}

    with open(merged_path) as f:
        merged = json.load(f)

    # Load MFM unit set
    mfm_path = MFM_DIR / f"{slug}.yaml"
    if not mfm_path.exists():
        return {"slug": slug, "error": "no MFM data", "findings": []}

    with open(mfm_path) as f:
        mfm = yaml.safe_load(f)

    mfm_units = {u["name"].lower().strip()
                 for u in mfm.get("units", [])
                 if not u.get("legends", False)}

    # Build name map
    unit_map = {}
    for u in merged.get("units", []):
        unit_map[u["name"].lower().strip()] = u

    findings = []
    for mfm_name in sorted(mfm_units):
        unit = unit_map.get(mfm_name)
        if not unit:
            findings.append({
                "unit": mfm_name,
                "category": "missing",
                "field": "unit",
                "severity": "CRITICAL",
                "message": "MFM has this unit but it's missing from merged JSON",
            })
        else:
            findings.extend(validate_unit(unit))

    # Categorize
    criticals = [f for f in findings if f["severity"] == "CRITICAL"]
    majors = [f for f in findings if f["severity"] == "MAJOR"]
    minors = [f for f in findings if f["severity"] == "MINOR"]
    infos = [f for f in findings if f["severity"] == "INFO"]

    return {
        "slug": slug,
        "faction_name": merged.get("name", slug),
        "total_units": len(mfm_units),
        "total_findings": len(findings),
        "by_severity": {"CRITICAL": len(criticals), "MAJOR": len(majors),
                        "MINOR": len(minors), "INFO": len(infos)},
        "findings": findings,
    }


# ── CLI ──────────────────────────────────────────────────────────

def print_report(faction_result: dict):
    """Print a human-readable report."""
    s = faction_result
    print(f"\n{'='*60}")
    print(f"DETERMINISTIC VALIDATION: {s.get('faction_name', s.get('slug'))}")
    print(f"{'='*60}")
    if "error" in s:
        print(f"ERROR: {s['error']}")
        return
    print(f"Units: {s['total_units']}")
    print(f"Findings: {s['total_findings']} total")
    print(f"  CRITICAL: {s['by_severity']['CRITICAL']}")
    print(f"  MAJOR: {s['by_severity']['MAJOR']}")
    print(f"  MINOR: {s['by_severity']['MINOR']}")
    print(f"  INFO: {s['by_severity']['INFO']}")

    if s["findings"]:
        print(f"\nFindings:")
        for f in s["findings"]:
            print(f"  [{f['severity']:>8}] {f['unit']}: {f['message']}")


def main():
    ap = argparse.ArgumentParser(description="Deterministic data validation (zero LLM)")
    ap.add_argument("--faction", type=str, help="Faction slug to validate")
    ap.add_argument("--all", action="store_true", help="Validate all factions")
    args = ap.parse_args()

    if not args.faction and not args.all:
        ap.print_help()
        return

    slugs = []
    if args.all:
        for mfm_file in sorted(MFM_DIR.glob("*.yaml")):
            if mfm_file.name == "meta.yaml":
                continue
            slugs.append(mfm_file.stem)
    else:
        slugs = [args.faction]

    for slug in slugs:
        result = validate_faction(slug)
        print_report(result)


if __name__ == "__main__":
    main()
