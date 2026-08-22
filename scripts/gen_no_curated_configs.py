#!/usr/bin/env python3
"""Generate curated configs for NO_CURATED audit findings.

Fallback path for units that have BSData wargear structure but no curated
config: builds a complete engine-compatible entry (pts + info + builds) from
- merged data (profile.stats -> info, profile.points -> pts)
- BSData wargear_slots (fixed + slots via extract_wargear_slots)

Units covered by squad-schema configs are skipped (already ranked).
[Legends] and hidden entries are ignored.

Usage: python3 scripts/gen_no_curated_configs.py [--dry-run]
"""
import argparse
import json
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJ))
from adapter.bsdata_parser_11e import BSDataParser11e


def _norm(s):
    return (s.lower().replace("'", "").replace("\u2019", "")
            .replace("-", " ").replace("  ", " ").strip())


def load_curated(slug):
    """All unit keys that already have any config, per file."""
    cfg_dir = PROJ / "data" / "config" / slug
    covered = {}
    for fname in ["weapon_options.json", "characters.json",
                  "vehicles.json", "squads.json"]:
        fpath = cfg_dir / fname
        if not fpath.exists():
            continue
        with open(fpath) as f:
            data = json.load(f)
        for key, val in data.items():
            if key.startswith("_") or not isinstance(val, dict):
                continue
            if val.get("builds") or val.get("weapon_options", {}).get("builds"):
                covered.setdefault(_norm(key), (fname, key))
    return covered


def extract_wargear(bp, faction_name):
    """BSData wargear slots for every unit of a faction (legends excluded)."""
    for path in bp._find_json_files():
        data = bp._load_json(path)
        if data is None:
            continue
        cat = bp._get_catalogue(data)
        if cat.get("name", "").lower() != faction_name.lower():
            continue
        roots = bp._load_catalogue_roots(cat, include_linked=True)
        bp._current_entry_index = bp._build_entry_index(roots)
        bp._parent_groups = {}
        for root in roots:
            bp._build_parent_groups(root)
        result = {}
        for entry in cat.get("sharedSelectionEntries", []):
            if entry.get("type") not in ("unit", "model"):
                continue
            name = entry.get("name", "")
            if entry.get("hidden", "false") == "true" or "[Legends]" in name:
                continue
            ws = bp.extract_wargear_slots(entry)
            if ws:
                result[_norm(name)] = ws
        return result
    return {}


def build_info(stats):
    """merged profile.stats dict -> engine info block."""
    def _int(val, default=0):
        s = str(val).replace('"', "").replace("+", "").strip()
        digits = "".join(c for c in s if c.isdigit())
        return int(digits) if digits else default

    info = {
        "M": stats.get("M", '6"'),
        "T": _int(stats.get("T"), 4),
        "SV": _int(stats.get("Sv", stats.get("SV")), 3),
        "W": _int(stats.get("W"), 1),
        "OC": _int(stats.get("OC"), 0),
    }
    insv = str(stats.get("InSv", "")).strip()
    if insv and insv != "-":
        info["invuln"] = _int(insv.replace("+", ""), 0) or None
        if not info["invuln"]:
            del info["invuln"]
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open(PROJ / "audit_findings.json") as f:
        findings = json.load(f)

    no_curated = {(x["slug"], x["unit"]) for x in findings
                  if x["type"] == "NO_CURATED"}
    # Group by slug
    by_slug = {}
    for slug, unit in no_curated:
        by_slug.setdefault(slug, []).append(unit)

    bp = BSDataParser11e()
    created, skipped_legends = [], []

    for slug, unit_names in sorted(by_slug.items()):
        fn = bp.slug_to_faction(slug)
        if not fn:
            continue

        with open(PROJ / "data" / "merged" / f"{slug}.json") as f:
            merged = json.load(f)
        merged_by_name = {_norm(u.get("name", "")): u
                          for u in merged.get("units", [])}

        covered = load_curated(slug)
        bsdata_ws = extract_wargear(bp, fn)

        wo_path = PROJ / "data" / "config" / slug / "weapon_options.json"
        with open(wo_path) as f:
            wo_data = json.load(f)

        for unit_norm in unit_names:
            # Already covered by any config (incl. squad models-schema)? skip.
            if unit_norm in covered:
                print(f"SKIP {slug}/{unit_norm}: already configured "
                      f"({covered[unit_norm][0]})")
                continue
            mu = merged_by_name.get(unit_norm)
            ws = bsdata_ws.get(unit_norm)
            if not mu or not mu.get("profile") or not ws:
                print(f"SKIP {slug}/{unit_norm}: no merged profile/wargear")
                continue
            if "[Legends]" in mu.get("name", ""):
                skipped_legends.append((slug, mu["name"]))
                continue

            profile = mu["profile"]
            info = build_info(profile.get("stats", {}))

            fixed = [{"name": x["name"], "type": x["type"]}
                     for x in ws.get("fixed", [])]
            slots = [{"name": s["name"],
                      "choices": [{"name": c["name"], "type": c["type"]}
                                  for c in s["choices"]]}
                     for s in ws.get("slots", [])]
            build = {"name": "default", "fixed": fixed, "slots": slots}

            entry = {
                "pts": profile.get("points"),
                "info": info,
                "builds": [build],
            }
            # Find real display name from BSData wargear extraction side is
            # not needed; use merged name.
            display_name = mu["name"]
            wo_data[display_name] = entry
            created.append((slug, display_name, entry["pts"]))
            print(f"GEN {slug}/{display_name}: pts={entry['pts']} "
                  f"info={info} fixed={[x['name'] for x in fixed]} "
                  f"slots={[(s['name'], len(s['choices'])) for s in slots]}")

        if not args.dry_run:
            with open(wo_path, "w") as f:
                json.dump(wo_data, f, indent=2)
                f.write("\n")

    print(f"\nCreated {len(created)} configs"
          + (" (DRY RUN - nothing written)" if args.dry_run else ""))
    if skipped_legends:
        print(f"[Legends] ignored: {skipped_legends}")


if __name__ == "__main__":
    main()
