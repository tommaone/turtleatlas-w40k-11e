#!/usr/bin/env python3
"""Audit curated weapon configs against BSData wargear structure.

Usage: python3 audit_curated_vs_bsdata.py [--faction SLUG]
"""
import json, sys
from pathlib import Path
from collections import defaultdict

PROJ = Path("/home/tomecka/turtleatlas-w40k-11e")
sys.path.insert(0, str(PROJ))
from adapter.bsdata_parser_11e import BSDataParser11e

def _norm(s):
    return s.lower().replace("'", "").replace("\u2019", "").replace("-", " ").replace("  "," ").strip()

def load_curated(slug):
    cfg_dir = PROJ / "data" / "config" / slug
    result = {}
    covered = set()  # units with any curated config, incl. squad models-schema
    for fname in ["weapon_options.json", "characters.json", "vehicles.json", "squads.json"]:
        fpath = cfg_dir / fname
        if not fpath.exists():
            continue
        with open(fpath) as f:
            data = json.load(f)
        for key, val in data.items():
            if key.startswith("_") or not isinstance(val, dict):
                continue
            builds = val.get("builds") or val.get("weapon_options", {}).get("builds", [])
            if not builds:
                continue
            covered.add(_norm(key))
            # Squad-schema builds (models: [{count, ranged, melee}]) use a
            # different schema — not comparable to BSData wargear slots.
            if any("models" in b for b in builds):
                continue
            result[_norm(key)] = {"name": key, "builds": builds, "pts": val.get("pts")}
    return result, covered

def extract_wargear(bp, faction_name):
    """Walk sharedSelectionEntries for units, call extract_wargear_slots on each."""
    for path in bp._find_json_files():
        data = bp._load_json(path)
        if data is None:
            continue
        cat = bp._get_catalogue(data)
        if cat.get("name", "").lower() != faction_name.lower():
            continue
        roots = bp._load_catalogue_roots(cat, include_linked=True)
        entry_index = bp._build_entry_index(roots)
        bp._current_entry_index = entry_index
        # Also build parent_groups for weapon extraction
        bp._parent_groups = {}
        for root in roots:
            bp._build_parent_groups(root)

        result = {}
        for entry in cat.get("sharedSelectionEntries", []):
            if entry.get("type") not in ("unit", "model"):
                continue
            name = entry.get("name", "")
            hidden = entry.get("hidden", "false")
            if hidden == "true" or "[Legends]" in name:
                continue
            ws = bp.extract_wargear_slots(entry)
            pts = None
            for cost in entry.get("costs", []):
                if cost.get("name", "").lower() == "pts":
                    try: pts = int(cost["value"])
                    except: pass
            if ws:
                result[_norm(name)] = {"name": name, "wargear_slots": ws, "pts": pts}
        return result
    return {}

def _fixed_set(builds):
    s = set()
    for b in builds:
        for f in b.get("fixed", []):
            s.add(_norm(f["name"]))
    return s

def _all_choices(builds):
    s = set()
    for b in builds:
        for slot in b.get("slots", []):
            for c in slot.get("choices", []):
                s.add(_norm(c["name"]))
    return s

def _num_slots(builds):
    seen = set()
    for b in builds:
        for slot in b.get("slots", []):
            seen.add(_norm(slot["name"]))
    return len(seen)

def compare(name, curated, bsdata):
    f = []
    if not curated:
        if bsdata:
            ws = bsdata["wargear_slots"]
            nf = len(ws.get("fixed", []))
            ns = len(ws.get("slots", []))
            nc = 1
            for s in ws.get("slots", []):
                nc *= len(s["choices"])
            f.append({"unit": name, "type": "NO_CURATED",
                      "detail": f"BSData wargear ({nf} fixed, {ns} slots, {nc} combos) — no curated config"})
        return f
    if not bsdata:
        return f  # curated only, BSData has no wargear — fine

    cb = curated["builds"]
    bw = bsdata["wargear_slots"]

    # Fixed weapons
    cf = _fixed_set(cb)
    bf = set(_norm(x["name"]) for x in bw.get("fixed", []))
    miss = bf - cf
    if miss:
        f.append({"unit": name, "type": "MISSING_FIXED",
                  "detail": f"BSData fixed not in curated: {sorted(miss)}"})

    # Choice sets
    cc = _all_choices(cb)
    bc = set()
    for s in bw.get("slots", []):
        for c in s.get("choices", []):
            bc.add(_norm(c["name"]))
    miss_c = bc - cc
    if miss_c:
        f.append({"unit": name, "type": "MISSING_CHOICES",
                  "detail": f"BSData choices not in curated: {sorted(miss_c)}"})

    # Slot count
    cs = _num_slots(cb)
    bs = len(bw.get("slots", []))
    if cs != bs:
        f.append({"unit": name, "type": "SLOT_COUNT",
                  "detail": f"Curated {cs} slots, BSData {bs} slots"})

    # Points
    cp = curated.get("pts")
    bp_ = bsdata.get("pts")
    if cp and bp_ and cp != bp_:
        f.append({"unit": name, "type": "POINTS_DRIFT",
                  "detail": f"Curated={cp} pts, BSData={bp_} pts"})

    # Combos
    cc_n = 1
    for b in cb:
        for s in b.get("slots", []):
            cc_n *= len(s["choices"])
    bc_n = 1
    for s in bw.get("slots", []):
        bc_n *= len(s["choices"])
    if cc_n != bc_n:
        f.append({"unit": name, "type": "COMBOS",
                  "detail": f"Curated={cc_n}, BSData={bc_n}"})

    return f

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--faction")
    args = ap.parse_args()

    bp = BSDataParser11e()
    slugs = sorted(d.name for d in (PROJ/"data"/"config").iterdir()
                   if d.is_dir() and not d.name.startswith(("_",".")))
    if args.faction:
        slugs = [args.faction]

    all_f = []
    for slug in slugs:
        fn = bp.slug_to_faction(slug)
        if not fn:
            print(f"⚠ {slug}: no BSData mapping", file=sys.stderr)
            continue
        curated, covered = load_curated(bsdata_slug := slug)
        bsdata = extract_wargear(bp, fn)
        names = set(covered) | set(bsdata)
        for n in sorted(names):
            findings = compare(n, curated.get(n), bsdata.get(n))
            for finding in findings:
                finding["slug"] = slug
                finding["faction"] = fn
            all_f.extend(findings)

    # Report
    guilty = len(set(x["slug"]+"|"+x["unit"] for x in all_f))
    total_finding_rows = len(all_f)
    print(f"\n{'='*70}")
    print(f"AUDIT: {len(slugs)} factions, {total_finding_rows} findings, {guilty} guilty units")
    print(f"{'='*70}")

    by_slug = defaultdict(list)
    for x in all_f:
        by_slug[x["slug"]].append(x)

    for slug in sorted(by_slug):
        fs = by_slug[slug]
        print(f"\n  {slug} ({fs[0]['faction']})")
        by_u = defaultdict(list)
        for x in fs:
            by_u[x["unit"]].append(x)
        for u in sorted(by_u):
            print(f"    {u}")
            for x in by_u[u]:
                print(f"      [{x['type']}] {x['detail']}")

    if not all_f:
        print("\n  ✅ All clean.")

    with open(PROJ/"audit_findings.json","w") as f:
        json.dump(all_f, f, indent=2)

if __name__ == "__main__":
    main()
