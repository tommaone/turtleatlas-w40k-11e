#!/usr/bin/env python3
"""Regenerate squad builds from BSData model-composition structure.

Squads like Dark Reapers are encoded in BSData as sibling selectionEntryGroups
nesting type=model SEs ('4-9 Dark Reapers' + 'Dark Reaper Exarch'). This script
rewrites each squad's builds to that per-model structure (models[] with
per-model fixed weapons + per-model slots), mirroring what NewRecruit consumes.

Preserves n/pts/info/innate from the existing squads.json; only the builds
array is replaced.

Count allocation from squad size n:
  - leader models (min == 1, e.g. Exarch, Felarch, Lead Player) get 1 each
  - the remaining budget goes to the model pool: a single pool type becomes
    a flat model entry (count = n - #leaders); multiple pool types (Troupe
    players, Windriders, Storm Guardians) become ONE 'alloc' model whose
    choices the engine distributes across the squad, respecting per-variant
    min/max (parallel-variant units — previously skipped).

Skipped (data gap, not expressible): units whose pool lacks the base model
type so the squad count cannot be reached. Nested pool minimums (at least N
models from a base pool, e.g. Corsair Voidscarred's 'Voidscarred' SEG min=4)
are carried into the alloc payload as pool_min; the engine enforces them.
Curated builds are kept untouched for skipped units.

Usage:
    python3 scripts/gen_squad_composition.py --dry-run
    python3 scripts/gen_squad_composition.py --force
    python3 scripts/gen_squad_composition.py --faction aeldari --force
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from adapter.bsdata_parser_11e import BSDataParser11e

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "data" / "config"


def fuzzy_find_composition(composition: dict, unit_name: str) -> dict | None:
    """Find composition entry by exact name, then substring match."""
    if unit_name in composition:
        return composition[unit_name]
    for bs_name, bs_data in composition.items():
        if unit_name.lower() in bs_name.lower() or bs_name.lower() in unit_name.lower():
            return bs_data
    return None


def _alloc_model_name(names: list[str]) -> str:
    """Derive a generic model label from parallel-variant names.

    Strips mode suffixes ('with X', 'w/ X') from every variant and takes the
    modal base name ('Player with Harlequin's Blade' + '... Special Weapon'
    → 'Player'; 'Voidscarred w/ rifle' + 'Voidscarred with Faolchú' →
    'Voidscarred'). Falls back to the common prefix when no mode exists.
    """
    import re
    stripped: list[str] = []
    for n in names:
        n = n.strip()
        if n:
            stripped.append(re.split(r"\s+with\b|\sw/", n, maxsplit=1)[0])
    if not stripped:
        return "Model"
    mode = max(set(stripped), key=stripped.count)
    if mode:
        return mode
    prefix = stripped[0]
    for n in stripped[1:]:
        i = 0
        while i < min(len(prefix), len(n)) and prefix[i] == n[i]:
            i += 1
        prefix = prefix[:i]
    return prefix.strip().rstrip(" with") or "Model"


def _variant_payload(m: dict) -> dict:
    """Emit one alloc choice payload from a parsed composition model entry."""
    out: dict = {"name": m.get("name", "")}
    if m.get("min") is not None:
        out["min"] = m["min"]
    else:
        out["min"] = 0
    if m.get("max") is not None:
        out["max"] = m["max"]
    if m.get("pool_min") is not None:
        out["pool_min"] = m["pool_min"]
    if m.get("ranged"):
        out["ranged"] = m["ranged"]
    if m.get("melee"):
        out["melee"] = m["melee"]
    if m.get("slots"):
        out["slots"] = m["slots"]
    return out


def make_build(unit_cfg: dict, comp: dict) -> dict | None:
    """Allocate model counts from squad size n and emit one composition build.

    Leader entries (min == 1, e.g. Exarch, Felarch, Lead Player) get fixed
    count 1. The remaining budget is allocated across the model pool:

    - pool of one type → flat model entry with count = budget
      (Dark Reapers: n - 1 exarch)
    - pool of several types → one 'alloc' model: the engine distributes the
      budget across the variant choices (respecting per-variant min/max),
      e.g. Troupe players, Windriders, Storm Guardians.

    Returns None only when the budget cannot be expressed at all
    (more leaders than models, or the pool cannot reach the squad count —
    either the base type is missing or a nested pool min exceeds the budget).
    """
    n = unit_cfg.get("n", 1)
    models = comp["builds"][0]["models"]

    leaders = [m for m in models if m.get("min") == 1]
    pool = [m for m in models if m.get("min") != 1]
    budget = n - len(leaders)
    if budget < 0:
        return None

    if pool:
        # The pool must be able to hold the whole budget — otherwise the squad
        # size cannot be reached (e.g. Corsair Voidscarred before the nested
        # pool fix: '4-9 Voidscarred' SEG held only the capped specials, no
        # base model, so budget 4 could never be filled by cap-1 choices).
        pool_capacity = sum(m.get("max", budget) or budget for m in pool)
        pool_mandatory = sum(m.get("min", 0) or 0 for m in pool)
        # Nested pool min (e.g. Voidscarred: at least 4 models must come from
        # the base pool) is a mandatory contribution to the budget too.
        pool_mandatory = max(pool_mandatory,
                             max((m.get("pool_min") or 0) for m in pool) if pool else 0)
        if pool_capacity < budget or pool_mandatory > budget:
            return None

    models_out = []
    if pool:
        if len(pool) == 1:
            m = pool[0]
            if budget > 0:
                out = {"name": m.get("name", ""), "count": budget}
                if m.get("ranged"):
                    out["ranged"] = m["ranged"]
                if m.get("melee"):
                    out["melee"] = m["melee"]
                if m.get("slots"):
                    out["slots"] = m["slots"]
                models_out.append(out)
        else:
            # Parallel variants share the squad budget — emit an alloc model.
            alloc = [_variant_payload(m) for m in pool]
            models_out.append({
                "name": _alloc_model_name([m.get("name", "") for m in pool]),
                "count": budget,
                "alloc": alloc,
            })
    for e in leaders:
        out = {"name": e.get("name", ""), "count": 1}
        if e.get("ranged"):
            out["ranged"] = e["ranged"]
        if e.get("melee"):
            out["melee"] = e["melee"]
        if e.get("slots"):
            out["slots"] = e["slots"]
        models_out.append(out)

    if not models_out:
        return None
    return {"name": "Default", "models": models_out}


def main():
    parser = argparse.ArgumentParser(description="Regenerate squad builds from BSData composition")
    parser.add_argument("--faction", default="aeldari", help="Config folder slug (default: aeldari)")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing")
    parser.add_argument("--force", action="store_true", help="Write changes (dry-run default)")
    args = parser.parse_args()

    bsdata_parser = BSDataParser11e(str(REPO_ROOT / "bsdata"))
    composition = bsdata_parser.extract_squad_composition(args.faction)
    if not composition:
        print(f"No composition for faction '{args.faction}'")
        sys.exit(1)

    cfg_path = CONFIG_DIR / args.faction / "squads.json"
    if not cfg_path.exists():
        print(f"Config not found: {cfg_path}")
        sys.exit(1)
    squads = json.loads(cfg_path.read_text())

    replaced = 0
    skipped = 0
    kept = 0
    for unit_name, unit_cfg in squads.items():
        if unit_name.startswith("_"):
            continue
        comp = fuzzy_find_composition(composition, unit_name)
        if not comp:
            kept += 1
            continue
        build = make_build(unit_cfg, comp)
        if build is None:
            skipped += 1
            continue
        unit_cfg["builds"] = [build]
        replaced += 1

    print(f"replaced: {replaced} | skipped (parallel variants): {skipped} | kept (no composition): {kept}")

    if args.dry_run or not args.force:
        print("Dry run — no files written. Use --force to apply.")
        return

    cfg_path.write_text(json.dumps(squads, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {cfg_path}")


if __name__ == "__main__":
    main()
