"""
turtleatlas-w40k-11e adapter: merges 10e BSData profiles + 11e MFM points.

Architecture:
  bsdata/  (git submodule -> wh40k-10e)       -> XML catalogue files (.cat)
  mfm/     (git submodule -> wh40k-11e-mfm)   -> YAML faction files

  merge.py reads both and produces unified JSON per faction:
    units (profile + pricing) + detachments + enhancements

Usage:
  python3 adapter/merge.py --faction grey-knights
  python3 adapter/merge.py --all --output data/merged/
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MFM_DIR = REPO_ROOT / "mfm"

# Ensure repo root is on the path for imports
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from adapter.bsdata_parser_11e import BSDataParser11e


# -- MFM (11e points / detachments) -----------------------------------------

def load_mfm_faction(slug: str) -> dict | None:
    """Load 11e points/detachments from the MFM YAML file."""
    path = MFM_DIR / "data" / f"{slug}.yaml"
    if not path.exists():
        print(f"  [MFM] NOT FOUND: {path}", file=sys.stderr)
        return None

    import yaml
    with open(path) as f:
        return yaml.safe_load(f)


# -- Merge ------------------------------------------------------------------

def merge_faction(slug: str, mfm_data: dict, bsdata_parser: BSDataParser,
                  with_legends: bool = False) -> dict:
    """Merge MFM points onto BSData profiles for one faction."""
    faction_name = bsdata_parser.slug_to_faction(slug)
    bsdata = bsdata_parser.query_faction(faction_name, include_legends=with_legends) if faction_name else None

    def norm(name: str) -> str:
        # Normalize Unicode apostrophes to ASCII for matching
        return name.lower().strip().replace('\u2019', "'")

    # -- BSData profiles --
    bsdata_unit_map: dict[str, dict] = {}
    bsdata_orig_names: dict[str, str] = {}
    if bsdata:
        for u in bsdata["units"]:
            n = norm(u["name"])
            bsdata_unit_map[n] = u
            bsdata_orig_names[n] = u["name"]

    # -- MFM points (filter out legends unless requested) --
    mfm_unit_map: dict[str, dict] = {}
    mfm_orig_names: dict[str, str] = {}
    for u in mfm_data.get("units", []):
        if u.get("legends") and not with_legends:
            continue
        n = norm(u["name"])
        mfm_unit_map[n] = u
        mfm_orig_names[n] = u["name"]

    # Union of names
    all_names = sorted(set(bsdata_unit_map.keys()) | set(mfm_unit_map.keys()))

    merged_units = []
    for n in all_names:
        bs_u = bsdata_unit_map.get(n)
        mfm_u = mfm_unit_map.get(n)

        # Extract deep_strike from BSData rules
        ds = False
        if bs_u:
            for rule in (bs_u.get("rules") or []):
                if "DEEP STRIKE" in rule.upper():
                    ds = True
                    break

        merged_units.append({
            "name": mfm_orig_names.get(n) or bsdata_orig_names.get(n) or n,
            "in_bsdata": bs_u is not None,
            "in_mfm": mfm_u is not None,
            "deep_strike": ds,
            "profile": bs_u,
            "pricing": mfm_u.get("pricing") if mfm_u else None,
            "role": mfm_u.get("role") if mfm_u else None,
            "attachTo": mfm_u.get("attachTo") if mfm_u else None,
            "wargear_options": mfm_u.get("wargear") if mfm_u else None,
        })

    return {
        "faction": mfm_data.get("name", slug),
        "slug": slug,
        "version": mfm_data.get("version"),
        "firstSeen": mfm_data.get("firstSeen"),
        "detachments": mfm_data.get("detachments", []),
        "units": merged_units,
        "_meta": {
            "bsdata_faction": faction_name,
            "bsdata_revision": bsdata["revision"] if bsdata else None,
            "bsdata_units": len(bsdata_unit_map),
            "mfm_units": len(mfm_unit_map),
            "merged_units": len(merged_units),
        },
    }


# -- CLI --------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Merge 10e BSData + 11e MFM")
    ap.add_argument("--faction", type=str, help="Faction slug (e.g. grey-knights)")
    ap.add_argument("--all", action="store_true", help="Merge all factions")
    ap.add_argument("--output", type=str, default="data/merged",
                    help="Output directory for JSON files")
    ap.add_argument("--with-legends", action="store_true",
                    help="Include Legends units in BSData output")
    args = ap.parse_args()

    if not args.faction and not args.all:
        ap.print_help()
        return

    # Init BSData 11e parser
    bsdata = BSDataParser11e()
    print(f"BSData 11e factions found: {len(bsdata.list_factions())}", file=sys.stderr)

    slugs = []
    if args.faction:
        slugs = [args.faction]
    else:
        for f in sorted((MFM_DIR / "data").glob("*.yaml")):
            if f.stem != "meta":
                slugs.append(f.stem)

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    for slug in slugs:
        print(f"\n=== {slug} ===", file=sys.stderr)

        mfm = load_mfm_faction(slug)
        if not mfm:
            continue

        merged = merge_faction(slug, mfm, bsdata, with_legends=args.with_legends)
        meta = merged["_meta"]
        print(f"  BSData: {meta['bsdata_faction'] or 'NOT FOUND'} "
              f"({meta['bsdata_units']} units)", file=sys.stderr)
        print(f"  MFM:    {meta['mfm_units']} units, "
              f"{len(merged['detachments'])} detachments", file=sys.stderr)
        print(f"  Merge:  {meta['merged_units']} total units", file=sys.stderr)

        out_path = out_dir / f"{slug}.json"
        with open(out_path, "w") as f:
            json.dump(merged, f, indent=2, ensure_ascii=False, default=str)
        print(f"  -> {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
