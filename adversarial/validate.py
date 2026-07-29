"""
adversarial/validate.py — Shredder-driven adversarial data validation.

For each unit in a faction's merged JSON:
1. Load unit data + faction expert knowledge
2. Build an adversarial prompt (Shredder mindset + expert injection)
3. Call Ollama (or any OpenAI-compatible API) to evaluate
4. Collect discrepancies, generate report

Usage:
    python3 -m adversarial.validate --faction grey-knights
    python3 -m adversarial.validate --faction grey-knights --unit "Strike Squad"
    python3 -m adversarial.validate --all
    python3 -m adversarial.validate --report           # show last report
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MERGED_DIR = REPO_ROOT / "data" / "merged"
EXPERTS_DIR = REPO_ROOT / "resources" / "experts"
MFM_DIR = REPO_ROOT / "mfm" / "data"
REPORTS_DIR = REPO_ROOT / "adversarial" / "reports"

# Ollama runs on Windows host, accessible from WSL
OLLAMA_BASE = os.environ.get("OLLAMA_BASE_URL", "http://192.168.16.1:11434/v1")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")

# ── SLUG → EXPERT FILE MAP ────────────────────────────────────────
# Experts exist only for factions that have been written.
# For factions without an expert, we use a generic fallback.
AVAILABLE_EXPERTS: dict[str, str] = {}

# Auto-discover expert files
if EXPERTS_DIR.exists():
    for f in sorted(EXPERTS_DIR.glob("*.md")):
        if f.name != "template.md":
            slug = f.stem  # e.g. "grey-knights"
            AVAILABLE_EXPERTS[slug] = str(f)

# ── MFM unit lists (per faction slug) ──────────────────────────────
# We only validate units that are actually in the faction's MFM roster
# (not cross-faction allies that got merged in).
import yaml


def load_mfm_units(slug: str) -> set[str]:
    """Return set of MFM unit names for a faction slug."""
    path = MFM_DIR / f"{slug}.yaml"
    if not path.exists():
        return set()
    with open(path) as f:
        data = yaml.safe_load(f)
    return {u["name"] for u in data.get("units", []) if not u.get("legends", False)}


# ── SHREDDER ADVERSARIAL PROMPT ────────────────────────────────────

SHREDDER_SYSTEM_PROMPT = """You are SHREDDER — a ruthless prosecutor auditing Warhammer 40k game data.

Your ONLY job: compare DATA TO AUDIT against EXPERT KNOWLEDGE and produce a verdict JSON.
Never echo or repeat the data. Only produce the verdict.

MANDATORY CHECKS — do all of these:

1. KEYWORDS: Compare EVERY keyword in the data against what the expert says the unit should have.
   - Flag MISSING keywords (expert says it should have "Terminator" but data doesn't have it)
   - Flag EXTRA keywords that seem wrong
   - Flag wrong Faction keyword (e.g., "Faction: Grey Knights" vs "Faction: Adeptus Astartes")
   - Check "Smoke" on vehicles, "Fly" on jump/air units, "Psyker" on psychic units
   - Check "Character" vs "Epic Hero" on named characters

2. STATS: Check EVERY stat value (M, T, Sv, W, LD, OC, InSv) against expert expectations.
   - Pay special attention to T (toughness) — power armour = T4, terminator = T5, vehicles = T8+
   - Check InSv (invulnerable save) — terminator armour should have 4+, power armour infantry has none
   - Check OC — Battleline should have OC2, most infantry OC1, vehicles OC0-5

3. WEAPONS: Check weapon names, Range, A, BS/WS, S, AP, D, and Keywords.
   - Flag wrong value (e.g., S6 vs S8 for psycannon)
   - Flag missing Keywords (e.g. Nemesis force weapon missing Psychic)
   - Flag wrong BS/WS (Paladins should be 2+, regular terminators 3+)

4. ABILITIES: Check ability names match what the expert expects.
   - Minor description differences are OK, but wrong names are not

5. RULES: Check rules match expert expectations.
   - Missing "Deep Strike", "Gate of Infinity", "Deadly Demise" etc.

Severity scale:
- CRITICAL: wrong stat value, wrong toughness, wrong save, missing required keyword
- MAJOR: missing weapon, missing ability, wrong weapon stat, extra significant keyword
- MINOR: keyword wording difference, minor stat discrepancy
- INFO: formatting only, no gameplay impact

EXAMPLE: If data shows Strike Squad has W=1 but expert says W=2, output:
{"unit": "Strike Squad", "pass": false, "discrepancies": [{"category": "stat", "field": "W", "our_value": "1", "expected": "2", "severity": "CRITICAL", "evidence": "Strike Squad is Power Armour infantry, should have W2 per stat baseline"}]}

If NO discrepancies found, output:
{"unit": "Strike Squad", "pass": true, "discrepancies": []}

REMEMBER: Output ONLY the JSON verdict. No other text. No markdown fences. No commentary."""


def extract_unit_expert(unit_name: str, expert_text: str) -> str:
    """Extract the relevant section of the expert file for a specific unit.

    Returns the unit's section (### header block) plus the generic red flags
    section and weapon profile reference tables.
    """
    lines = expert_text.split("\n")
    unit_header = f"### {unit_name}"
    unit_header_alt = None

    # Some units in the expert use slightly different names
    alt_map = {
        "Grey Knights Thunderhawk Gunship": "Thunderhawk Gunship",
    }
    if unit_name in alt_map:
        unit_header_alt = f"### {alt_map[unit_name]}"

    target_idx = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == unit_header or (unit_header_alt and stripped == unit_header_alt):
            target_idx = i
            break

    if target_idx is None:
        # Try fuzzy match: find any ### header that contains the unit name
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("### "):
                header_name = stripped[4:].strip()
                # Check if unit name appears in header or vice versa
                if (unit_name.lower() in header_name.lower()
                        or header_name.lower() in unit_name.lower()):
                    target_idx = i
                    break

    if target_idx is None:
        # Return just the generics + weapon reference
        return _extract_generic_sections(expert_text)

    # Collect from ### header to next ### header or end of file
    unit_section_lines = [lines[target_idx]]
    for i in range(target_idx + 1, len(lines)):
        if lines[i].strip().startswith("### ") and not lines[i].strip().startswith("####"):
            break
        unit_section_lines.append(lines[i])

    unit_section = "\n".join(unit_section_lines)

    # Also add the generic sections (red flags, weapon reference)
    generic = _extract_generic_sections(expert_text)

    return f"{unit_section}\n\n{generic}"


def _extract_generic_sections(expert_text: str) -> str:
    """Extract generic red flags, weapon reference, and tricky areas."""
    lines = expert_text.split("\n")
    result = []
    capture = False
    for line in lines:
        stripped = line.strip()
        # Capture from "## Generic Red Flags" or "## Weapon Profile Reference"
        # or "## Known Tricky Areas" to end
        if stripped.startswith("## Generic Red Flags"):
            capture = True
        elif stripped.startswith("## Weapon Profile Reference"):
            capture = True
        elif stripped.startswith("## Known Tricky Areas"):
            capture = True
        elif stripped.startswith("## "):
            capture = False
        if capture:
            result.append(line)
    return "\n".join(result)


def build_shredder_prompt(unit_data: dict, unit_name: str, expert_text: str) -> str:
    """Build the adversarial prompt for one unit."""

    # Extract per-unit section from expert
    unit_expert = extract_unit_expert(unit_name, expert_text)

    # Compact the unit data to relevant fields.
    # In merged JSON, keywords are inside the profile dict (the full BSData unit blob).
    profile = unit_data.get("profile") or unit_data
    compact = {
        "name": unit_data.get("name"),
        "stats": profile.get("stats", {}),
        "weapons": [],
        "abilities": profile.get("abilities", []),
        "keywords": profile.get("keywords", []),
        "rules": profile.get("rules", []),
    }

    for w in unit_data.get("profile", {}).get("weapons", []):
        for p in w.get("profiles", []):
            compact["weapons"].append({
                "name": p.get("name", w["name"]),
                "stats": p.get("stats", {}),
            })

    return f"""=== EXPERT KNOWLEDGE FOR {unit_name} ===

{unit_expert}

=== DATA TO AUDIT ===

{json.dumps(compact, indent=2)}

=== END OF DATA ===

Now produce the audit verdict JSON ONLY. No other text. No markdown fences. Just the JSON object."""


def call_llm(prompt: str, system_prompt: str = None) -> str:
    """Call Ollama (OpenAI-compatible API) and return the response text."""
    import requests

    if system_prompt is None:
        system_prompt = SHREDDER_SYSTEM_PROMPT

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,  # low temp for consistent comparison
        "max_tokens": 2000,
    }

    try:
        resp = requests.post(
            f"{OLLAMA_BASE}/chat/completions",
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        result = resp.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.ConnectionError:
        print(f"  [LLM] Connection refused to {OLLAMA_BASE}. Is Ollama running?")
        return json.dumps({"unit": "", "pass": False,
                           "discrepancies": [{"category": "error",
                                              "field": "llm_connection",
                                              "our_value": "could not connect",
                                              "expected": "Ollama running",
                                              "severity": "CRITICAL",
                                              "evidence": f"Connection refused to {OLLAMA_BASE}"}]})
    except Exception as e:
        print(f"  [LLM] Error: {e}")
        return json.dumps({"unit": "", "pass": False,
                           "discrepancies": [{"category": "error",
                                              "field": "llm_error",
                                              "our_value": str(e),
                                              "expected": "no error",
                                              "severity": "CRITICAL",
                                              "evidence": str(e)}]})


# ── VALIDATION ENGINE ──────────────────────────────────────────────

def validate_unit(unit_data: dict, unit_name: str, expert_text: str) -> dict:
    """Validate a single unit against expert knowledge.

    Returns dict with pass/fail + discrepancies.
    """
    prompt = build_shredder_prompt(unit_data, unit_name, expert_text)
    raw = call_llm(prompt)

    # Try to parse JSON from the response
    # The LLM sometimes wraps in markdown ```json blocks or adds text before/after
    try:
        text = raw.strip()

        # Strip markdown code fences if present (```json ... ``` or ``` ... ```)
        if text.startswith("```"):
            # Find first newline after opening fence
            idx = text.find("\n")
            if idx != -1:
                text = text[idx + 1:]
            else:
                text = text[3:]  # single line
        if text.endswith("```"):
            text = text[:-3].strip()

        # Find JSON object: first { to last }
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            text = text[first_brace : last_brace + 1]

        result = json.loads(text)
    except json.JSONDecodeError:
        # If JSON parsing fails, wrap the raw response as an error
        short_raw = raw[:800]
        result = {
            "unit": unit_name,
            "pass": False,
            "discrepancies": [{
                "category": "error",
                "field": "llm_response_parse",
                "our_value": "could not parse LLM response as JSON",
                "expected": "valid JSON",
                "severity": "CRITICAL",
                "evidence": f"Raw response: {short_raw}",
            }],
        }

    # Ensure unit name is set
    if not result.get("unit"):
        result["unit"] = unit_name

    return result


def validate_faction(slug: str, unit_filter: str = None) -> dict:
    """Validate all MFM units for a faction.

    Returns dict with results per unit + summary stats.
    """
    merged_path = MERGED_DIR / f"{slug}.json"
    if not merged_path.exists():
        print(f"  [SKIP] No merged data for '{slug}'")
        return {"slug": slug, "error": "no merged data"}

    # Load merged data
    with open(merged_path) as f:
        merged = json.load(f)

    # Load MFM unit names (what we actually validate)
    mfm_units = load_mfm_units(slug)
    if not mfm_units:
        print(f"  [SKIP] No MFM units for '{slug}'")
        return {"slug": slug, "error": "no MFM data"}

    # Build name → unit map
    def _norm(name):
        n = name.lower().strip().replace("\u2019", "'")
        n = n.replace("armour", "armor").replace("defence", "defense")
        return n

    unit_map = {}
    for u in merged["units"]:
        unit_map[_norm(u["name"])] = u

    # Load expert knowledge
    expert_path = AVAILABLE_EXPERTS.get(slug)
    if expert_path:
        with open(expert_path) as f:
            expert_text = f.read()
        print(f"  [EXPERT] Loaded '{slug}' expert ({len(expert_text)} chars)")
    else:
        expert_text = f"""
        No expert file available for this faction.
        Basic sanity checks:
        - Stats should have plausible values (M 3-20, T 3-14, Sv 2-7+, W 1-30, LD 4-8+)
        - Weapons should have Range, A, BS/WS, S, AP, D, Keywords
        - Abilities should have a name and description
        - Keywords should include "{slug}" faction keyword
        """
        print(f"  [EXPERT] No expert for '{slug}', using generic fallback")

    # Validate each unit
    results = []
    total = len(mfm_units)
    errors = 0
    discrepancies_found = 0

    for i, mfm_name in enumerate(sorted(mfm_units)):
        if unit_filter and unit_filter.lower() not in mfm_name.lower():
            continue

        normed = _norm(mfm_name)
        unit_data = unit_map.get(normed)

        if unit_data is None:
            print(f"  [{i+1}/{total}] {mfm_name} → NOT FOUND IN MERGED")
            results.append({
                "unit": mfm_name,
                "pass": False,
                "discrepancies": [{
                    "category": "missing",
                    "field": "unit",
                    "our_value": "not found in merged data",
                    "expected": mfm_name,
                    "severity": "CRITICAL",
                    "evidence": "MFM lists this unit but it's missing from merged JSON",
                }],
            })
            errors += 1
            discrepancies_found += 1
            continue

        print(f"  [{i+1}/{total}] {mfm_name} → checking...", end=" ", flush=True)
        try:
            result = validate_unit(unit_data, mfm_name, expert_text)
        except Exception as exc:
            result = {
                "unit": mfm_name,
                "pass": False,
                "discrepancies": [{
                    "category": "error",
                    "field": "validation_crash",
                    "our_value": str(exc),
                    "expected": "no error",
                    "severity": "CRITICAL",
                    "evidence": str(exc),
                }],
            }
        results.append(result)

        n_discrepancies = len(result.get("discrepancies", []))
        if n_discrepancies > 0 and result.get("pass") == False:
            errors += 1
            discrepancies_found += n_discrepancies
            print(f"FAIL ({n_discrepancies} issues)")
            for d in result["discrepancies"][:3]:
                sev = d.get("severity", "?")
                cat = d.get("category", "?")
                fld = d.get("field", "?")
                our_val = d.get("our_value", "")
                exp_val = d.get("expected", "")
                if isinstance(our_val, bool):
                    our_val = str(our_val)
                if isinstance(exp_val, bool):
                    exp_val = str(exp_val)
                print(f"         [{sev}] {cat}: {fld}")
                print(f"           our: {str(our_val)[:80]}")
                print(f"           exp: {str(exp_val)[:80]}")
        elif n_discrepancies > 0:
            discrepancies_found += n_discrepancies
            print(f"PASS-warn ({n_discrepancies} minor)")
        else:
            print("PASS")
        
        # Small delay to avoid hammering Ollama
        time.sleep(0.5)

    # Summary
    summary = {
        "slug": slug,
        "faction_name": merged.get("name", slug),
        "total_units": total,
        "units_checked": len(results),
        "errors": errors,
        "total_discrepancies": discrepancies_found,
        "pass_rate": round((total - errors) / max(total, 1) * 100, 1),
    }

    report = {
        "meta": {
            "generated": datetime.now().isoformat(),
            "model": OLLAMA_MODEL,
            "expert_used": bool(expert_path),
        },
        "summary": summary,
        "results": results,
    }

    # Save report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{slug}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"\n{'='*50}")
    print(f"Faction: {summary['faction_name']} ({slug})")
    print(f"Units: {summary['units_checked']}/{summary['total_units']}")
    print(f"Errors: {summary['errors']}")
    print(f"Discrepancies: {summary['total_discrepancies']}")
    print(f"Pass rate: {summary['pass_rate']}%")
    print(f"{'='*50}\n")

    return report


# ── REPORTING ──────────────────────────────────────────────────────

def print_report(slug: str = None):
    """Print the latest validation report."""
    if slug:
        path = REPORTS_DIR / f"{slug}.json"
    else:
        # Find the most recent report
        files = sorted(REPORTS_DIR.glob("*.json"))
        if not files:
            print("No reports found. Run validation first.")
            return
        path = files[-1]

    if not path.exists():
        print(f"No report at {path}")
        return

    with open(path) as f:
        report = json.load(f)

    s = report.get("summary", {})
    print(f"\n{'='*60}")
    print(f"VALIDATION REPORT: {s.get('faction_name', s.get('slug'))}")
    print(f"Generated: {report.get('meta', {}).get('generated', '?')}")
    print(f"Model: {report.get('meta', {}).get('model', '?')}")
    print(f"{'='*60}")
    print(f"Units checked: {s.get('units_checked', 0)}/{s.get('total_units', 0)}")
    print(f"Units with errors: {s.get('errors', 0)}")
    print(f"Total discrepancies: {s.get('total_discrepancies', 0)}")
    print(f"Pass rate: {s.get('pass_rate', 0)}%")
    print(f"{'='*60}")

    # Breakdown by severity
    by_severity: dict[str, int] = {}
    by_category: dict[str, int] = {}
    for r in report.get("results", []):
        for d in r.get("discrepancies", []):
            sev = d.get("severity", "UNKNOWN")
            cat = d.get("category", "UNKNOWN")
            by_severity[sev] = by_severity.get(sev, 0) + 1
            by_category[cat] = by_category.get(cat, 0) + 1

    if by_severity:
        print("\nBy severity:")
        for sev in ["CRITICAL", "MAJOR", "MINOR", "INFO", "UNKNOWN"]:
            if sev in by_severity:
                print(f"  {sev}: {by_severity[sev]}")
    if by_category:
        print("\nBy category:")
        for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count}")

    # List failing units
    failures = [r for r in report.get("results", []) if not r.get("pass", True)]
    if failures:
        print(f"\nFailing units ({len(failures)}):")
        for r in failures:
            print(f"  ❌ {r['unit']}: {len(r.get('discrepancies', []))} discrepancies")
            for d in r.get("discrepancies", [])[:5]:
                print(f"       [{d.get('severity','?')}] {d.get('field','?')}: "
                      f"got '{d.get('our_value','?')}' expected '{d.get('expected','?')}'")


# ── CLI ────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Adversarial data validation via Shredder + Ollama")
    ap.add_argument("--faction", type=str, help="Faction slug to validate")
    ap.add_argument("--unit", type=str, help="Filter to unit name (substring match)")
    ap.add_argument("--all", action="store_true", help="Validate all factions")
    ap.add_argument("--report", type=str, nargs="?", const=None, default=None,
                    help="Show report for a faction (or latest)")
    ap.add_argument("--list-experts", action="store_true", help="List available experts")

    args = ap.parse_args()

    if args.list_experts:
        print(f"Available experts ({len(AVAILABLE_EXPERTS)}):")
        for slug, path in sorted(AVAILABLE_EXPERTS.items()):
            print(f"  {slug} → {path}")
        return

    if args.report is not None:
        print_report(args.report if args.report else None)
        return

    # If no args, show help
    if not args.faction and not args.all:
        ap.print_help()
        return

    factions_to_validate = []
    if args.all:
        # Validate all factions that have MFM data
        for mfm_file in sorted(MFM_DIR.glob("*.yaml")):
            if mfm_file.name == "meta.yaml":
                continue
            slug = mfm_file.stem
            factions_to_validate.append(slug)
    elif args.faction:
        factions_to_validate = [args.faction]

    for slug in factions_to_validate:
        print(f"\n{'#'*60}")
        print(f"# VALIDATING: {slug}")
        print(f"{'#'*60}")
        validate_faction(slug, unit_filter=args.unit)


if __name__ == "__main__":
    main()
