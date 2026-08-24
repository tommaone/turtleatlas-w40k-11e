#!/usr/bin/env python3
"""Curated-sheet regression audit (#4 war-plan follow-up).

Diffs every faction config against the pre-audit-grind state (5d21b52,
the last commit of hand-verified curated sets) and flags units whose
equipment got FLATTENED or LOST:

- fixed weapons removed
- multi-build units collapsed to fewer builds
- slots removed

Output: docs/curated-regression-report.md — a triage list for golden
verification. Presence on the list is NOT proof of a bug (some edits
were legitimate fixes); each entry needs source verification, which the
golden pipeline (#3 pilot pattern) provides.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE_COMMIT = "5d21b52"
FILES = ["squads.json", "weapon_options.json", "characters.json", "vehicles.json"]


def load_at(commit, path):
    r = subprocess.run(["git", "show", f"{commit}:{path}"],
                       capture_output=True, text=True, cwd=REPO)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def unit_signature(entry):
    """Structural fingerprint: what equipment the unit can field."""
    sig = {"builds": len(entry.get("builds", entry.get("weapon_options", {}).get("builds", []))),
           "fixed": [], "slots": []}
    builds = entry.get("builds") or entry.get("weapon_options", {}).get("builds", [])
    for b in builds:
        for f in b.get("fixed", []):
            sig["fixed"].append(f.get("name"))
        for s in b.get("slots", []):
            sig["slots"].append((s.get("name"), tuple(sorted(c.get("name", "") for c in s.get("choices", [])))))
    sig["fixed"] = sorted(x for x in sig["fixed"] if x)
    return sig


def main():
    findings = []
    cfg_root = REPO / "data" / "config"
    for cfg_dir in sorted(cfg_root.iterdir()):
        fid = cfg_dir.name
        if fid.startswith("_"):
            continue
        for fn in FILES:
            path = f"data/config/{fid}/{fn}"
            old = load_at(BASE_COMMIT, path)
            new_f = cfg_dir / fn
            if not new_f.exists():
                continue
            new = json.load(open(new_f))
            if old is None:
                continue
            for name in set(old) & set(new):
                if name.startswith("_") or not isinstance(old[name], dict):
                    continue
                o, n = unit_signature(old[name]), unit_signature(new[name])
                problems = []
                lost_fixed = [w for w in o["fixed"] if w not in n["fixed"]]
                if lost_fixed:
                    problems.append(f"lost fixed weapons: {lost_fixed}")
                if o["builds"] > n["builds"]:
                    problems.append(f"builds collapsed {o['builds']} -> {n['builds']}")
                lost_slots = [s for s in o["slots"] if s not in n["slots"]]
                if lost_slots:
                    problems.append(f"lost slot choices: {[s[0] for s in lost_slots]}")
                if problems:
                    findings.append((fid, fn, name, "; ".join(problems)))

    out = REPO / "docs" / "curated-regression-report.md"
    lines = [
        "# Curated-sheet regression report",
        "",
        f"Diffs current configs against `{BASE_COMMIT}` (last verified curated state).",
        "Each entry needs source verification before fixing — presence here",
        "flags *change*, not proven damage. Golden-pipeline candidates.",
        "",
        f"**{len(findings)} flagged entries.**",
        "",
    ]
    for fid, fn, name, prob in sorted(findings):
        lines.append(f"- `{fid}`/{fn} **{name}**: {prob}")
    out.write_text("\n".join(lines) + "\n")
    print(f"wrote {out} ({len(findings)} flagged)")


if __name__ == "__main__":
    sys.exit(main())
