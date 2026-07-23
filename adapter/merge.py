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
                  with_legends: bool = False,
                  global_index: dict | None = None) -> dict:
    """Merge MFM points onto BSData profiles for one faction."""
    faction_name = bsdata_parser.slug_to_faction(slug)
    bsdata = bsdata_parser.query_faction(faction_name, include_legends=with_legends) if faction_name else None

    def norm(name: str) -> str:
        # Normalize Unicode apostrophes to ASCII for matching
        return name.lower().strip().replace('\u2019', "'")

    def _fuzzy_match_mfm(bs_name: str, mfm_map: dict) -> str | None:
        """Try fuzzy matching for unit names that didn't match literally.
        Returns the matched MFM key or None."""
        n = norm(bs_name)
        # Strategy 1: strip trailing 's'/'es' (plural → singular)
        for variant in [n.rstrip('s'), n.rstrip('es')]:
            if variant in mfm_map:
                return variant
        # Strategy 2: MFM name stripped matches BSData
        for mk in mfm_map:
            if mk.rstrip('s') == n or mk.rstrip('es') == n:
                return mk
        # Strategy 3: one is prefix of the other (min 4 chars)
        for mk in mfm_map:
            if len(mk) >= 4 and len(n) >= 4:
                if mk.startswith(n) or n.startswith(mk):
                    return mk
        # Strategy 4: word overlap — check if core words match
        bs_words = set(n.split())
        for mk in mfm_map:
            mfm_words = set(mk.split())
            if bs_words & mfm_words and len(bs_words & mfm_words) >= 1:
                # At least one shared word, and lengths are close
                if abs(len(mk) - len(n)) <= 4:
                    return mk
        return None

    # -- BSData profiles --
    bsdata_unit_map: dict[str, dict] = {}
    bsdata_orig_names: dict[str, str] = {}
    if bsdata:
        for u in bsdata["units"]:
            n = norm(u["name"])
            bsdata_unit_map[n] = u
            bsdata_orig_names[n] = u["name"]

    # -- Weapon multiplicity index (e.g. "2 Lascannons" → count=2) --
    multiplicity_index: dict[str, list[dict]] = {}
    if bsdata:
        for path in bsdata_parser._find_json_files():
            data = bsdata_parser._load_json(path)
            if data is None:
                continue
            cat = bsdata_parser._get_catalogue(data)
            if cat.get("name", "").lower() == faction_name.lower():
                roots = bsdata_parser._load_catalogue_roots(cat, include_linked=True)
                entry_index = bsdata_parser._build_entry_index(roots)
                multiplicity_index = bsdata_parser.build_multiplicity_index(cat, entry_index)
                break

    # -- MFM points (filter out legends unless requested) --
    mfm_unit_map: dict[str, dict] = {}
    mfm_orig_names: dict[str, str] = {}
    for u in mfm_data.get("units", []):
        if u.get("legends") and not with_legends:
            continue
        n = norm(u["name"])
        mfm_unit_map[n] = u
        mfm_orig_names[n] = u["name"]

    # -- Apply weapon multiplicities to BSData units --
    if multiplicity_index:
        def _weapon_matches(mult_name: str, weapon: dict) -> bool:
            """Check if a multiplicity entry matches a weapon, handling plurals."""
            mn = mult_name.lower().rstrip('s')  # "Lascannons" → "lascannon"
            wn = weapon.get("name", "").lower()
            if mn in wn or wn in mn:
                return True
            # Check profile names too
            for p in weapon.get("profiles", []):
                pname = p.get("name", "").lower()
                if mn in pname or pname in mn:
                    return True
            return False

        for unit_name, mult_entries in multiplicity_index.items():
            un = norm(unit_name)
            bs_u = bsdata_unit_map.get(un)
            if not bs_u:
                continue
            weapons = bs_u.get("weapons") or bs_u.get("profile", {}).get("weapons", [])
            if not weapons:
                continue
            for mult in mult_entries:
                count = mult["count"]
                for w in weapons:
                    if _weapon_matches(mult["weapon_name"], w) and w.get("count", 1) == 1:
                        w["count"] = count

    # Union of names
    all_names = sorted(set(bsdata_unit_map.keys()) | set(mfm_unit_map.keys()))

    # -- Cross-faction fallback: find stats for MFM-only units in parent catalogues --
    def _find_cross_faction_profile(unit_name: str) -> dict | None:
        """Look up a unit's stats in other BSData catalogues."""
        if not global_index:
            return None
        u = global_index.get(norm(unit_name))
        if u and u.get('stats'):
            return u
        return None

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

        # Cross-faction fallback: if no BSData profile, look in other catalogues
        profile = bs_u
        in_bsdata = bs_u is not None
        if not profile and mfm_u:
            cross = _find_cross_faction_profile(mfm_u.get("name", n))
            if cross:
                profile = cross
                # Still mark as not-in-native-bsdata, but use the profile
                in_bsdata = False
                if not ds:
                    for rule in (cross.get("rules") or []):
                        if "DEEP STRIKE" in rule.upper():
                            ds = True
                            break

        merged_units.append({
            "name": mfm_orig_names.get(n) or bsdata_orig_names.get(n) or n,
            "in_bsdata": in_bsdata,
            "in_mfm": mfm_u is not None,
            "deep_strike": ds,
            "profile": profile,
            "pricing": mfm_u.get("pricing") if mfm_u else None,
            "role": mfm_u.get("role") if mfm_u else None,
            "attachTo": mfm_u.get("attachTo") if mfm_u else None,
            "wargear_options": mfm_u.get("wargear") if mfm_u else None,
        })

    # -- Step 2: Fuzzy match fixup for 0-point units --
    unmatched_mfm = {norm(u["name"]): u for u in mfm_data.get("units", [])
                     if not (u.get("legends") and not with_legends)}
    # Remove already-matched names
    for mu in merged_units:
        if mu.get("in_mfm") and mu["name"] in unmatched_mfm:
            del unmatched_mfm[norm(mu["name"])]

    fuzzy_fixed = 0
    for mu in merged_units:
        # Only fix units with 0 points or no pricing
        pts = None
        if mu.get("pricing"):
            costs = mu["pricing"][0].get("costs", [])
            if costs:
                pts = costs[0].get("points")
        if pts and pts > 0:
            continue

        matched_key = _fuzzy_match_mfm(mu["name"], unmatched_mfm)
        if matched_key:
            mfm_u = unmatched_mfm[matched_key]
            mu["pricing"] = mfm_u.get("pricing")
            mu["in_mfm"] = True
            # Do NOT overwrite name — keep BSData canonical name
            # Different datasheets (e.g. "Gretchin" vs "Gretchin (Armageddon)")
            del unmatched_mfm[matched_key]
            fuzzy_fixed += 1
            print(f"  [FUZZY] {mu['name']} ← '{matched_key}' ({mfm_u['pricing'][0]['costs'][0]['points']}pts)", file=sys.stderr)

    if unmatched_mfm:
        print(f"  [WARN] {len(unmatched_mfm)} MFM units unmatched:", file=sys.stderr)
        for k, v in list(unmatched_mfm.items())[:5]:
            print(f"    '{k}' ({v['name']})", file=sys.stderr)

    # -- Step 3: Dedup — only truly identical (same name + same stats) --
    def _unit_signature(mu: dict) -> str:
        """Create a dedup signature: normalized name + stats hash."""
        name = norm(mu["name"])
        profile = mu.get("profile") or {}
        stats = profile.get("stats") or {}
        stats_str = str(sorted(stats.items()))
        weps = profile.get("weapons") or []
        wep_names = sorted(w.get("name", "") for w in weps)
        return f"{name}|{stats_str}|{wep_names}"

    seen_sigs = {}
    deduped = []
    removed = 0
    for mu in merged_units:
        sig = _unit_signature(mu)
        if sig in seen_sigs:
            # Truly identical — keep the one with pricing
            prev_idx = seen_sigs[sig]
            prev = deduped[prev_idx]
            if mu.get("pricing") and not prev.get("pricing"):
                deduped[prev_idx] = mu
            removed += 1
        else:
            seen_sigs[sig] = len(deduped)
            deduped.append(mu)
    if removed:
        print(f"  [DEDUP] Removed {removed} identical duplicate(s)", file=sys.stderr)
    merged_units = deduped

    # -- Step 4: Sync profile.points from pricing (fix stale BSData 0) --
    for mu in merged_units:
        if mu.get("pricing") and mu.get("profile"):
            costs = mu["pricing"][0].get("costs", [])
            if costs:
                pricing_pts = costs[0].get("points")
                if pricing_pts and pricing_pts > 0:
                    mu["profile"]["points"] = pricing_pts

    # -- Step 4: Validate — flag any units still at 0 points --
    zero_units = []
    for mu in merged_units:
        pts = None
        if mu.get("pricing"):
            costs = mu["pricing"][0].get("costs", [])
            if costs:
                pts = costs[0].get("points")
        if pts is not None and pts == 0:
            zero_units.append(mu["name"])
    if zero_units:
        print(f"  [ERROR] {len(zero_units)} units still at 0pts after fuzzy match:", file=sys.stderr)
        for name in zero_units:
            print(f"    {name} — needs manual price from Warhammer Community faction pack", file=sys.stderr)

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

    # Build global unit index for cross-faction lookup
    print("Building global BSData unit index...", file=sys.stderr, end=" ")
    global_index: dict[str, dict] = {}
    for faction in bsdata.list_factions():
        faction_data = bsdata.query_faction(faction, include_legends=False)
        if not faction_data:
            continue
        for u in faction_data['units']:
            n = u['name'].lower().strip().replace('\u2019', "'")
            existing = global_index.get(n)
            if not existing or (not existing.get('stats') and u.get('stats')):
                global_index[n] = u
    print(f"{len(global_index)} units indexed", file=sys.stderr)

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

        merged = merge_faction(slug, mfm, bsdata, with_legends=args.with_legends,
                              global_index=global_index)
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
