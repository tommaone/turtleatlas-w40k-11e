"""Generate heuristic `detachments.json` L2 scaffold for every faction.

Decision 2026-08-27: mechanical detachment modifiers are retired; detachment
strength is a heuristic (expert file), never an engine number. This generator
produces the L2 scaffold from VERIFIED L0 data only:

  - name / dp_cost / objective   ← MFM merged detachments[] (data/merged/<f>.json)
  - disposition                  ← supported.json `dispositions` map, else
                                    derived from the merged `objective` string
                                    (objective → one of the 5 disposition IDs)
  - source                       ← points at the L0 file

Every field is traceable to L0 — no expert strength ratings here. `strength`,
`best_for`, `strength_notes`, `limitations` are intentionally OMITTED until a
human/expert review pass (L2 enrichment) adds them with Wahapedia/NewRecruit
sources. Files carry `human_reviewed: false`.

Deterministic output: entries sorted by slug, JSON written with
ensure_ascii=True indent=2 (matches other generated config files).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MERGED_DIR = REPO_ROOT / "data" / "merged"
CONFIG_DIR = REPO_ROOT / "data" / "config"

VALID_DISPOSITIONS = {
    "purge-the-foe", "take-and-hold", "reconnaissance", "priority-assets", "disruption",
}

# objective string -> disposition id (normalised: strip, lower, spaces -> '-')
OBJECTIVE_TO_DISPOSITION = {d.replace("-", " "): d for d in VALID_DISPOSITIONS}


def slugify(name: str) -> str:
    """Merged detachment name -> kebab slug (matches test_detachment_validation)."""
    return (
        name.strip().lower().replace(" ", "-").replace("'", "").replace("\u2019", "")
    )


def disposition_of(faction: str, slug: str, objective: str | None,
                   supported: dict) -> str:
    """disposition: supported.json map wins; else derive from objective."""
    disp = (supported.get(faction) or {}).get("dispositions", {}).get(slug)
    if disp:
        return disp
    obj = (objective or "").strip().lower()
    if obj in OBJECTIVE_TO_DISPOSITION:
        return OBJECTIVE_TO_DISPOSITION[obj]
    raise ValueError(f"{faction}/{slug}: no disposition from map or objective {objective!r}")


def main() -> None:
    supported = {}
    for sup_path in CONFIG_DIR.glob("*/supported.json"):
        supported[sup_path.parent.name] = json.loads(sup_path.read_text())

    written = 0
    for merged_path in sorted(MERGED_DIR.glob("*.json")):
        faction = merged_path.stem
        data = json.loads(merged_path.read_text())
        detachments = data.get("detachments", [])
        if not detachments:
            continue

        entries = {}
        for det in detachments:
            name = det.get("name")
            if not name:
                continue
            slug = slugify(name)
            dp = det.get("dp")
            objective = det.get("objective")
            disposition = disposition_of(faction, slug, objective, supported)
            entries[slug] = {
                "_id": slug,
                "_slug": slug,
                "name": name,
                "dp_cost": int(dp) if dp is not None else None,
                "disposition": disposition,
                "objective": objective,
                "source": f"MFM (data/merged/{faction}.json, verified L0)",
            }

        if not entries:
            continue

        out = {
            "_meta": {
                "faction": faction,
                "layer": "L2-detachment",
                "generated_from": ["mfm", "supported.json"],
                "generated": "2026-08-28",
                "human_reviewed": False,
            },
            "detachments": {k: entries[k] for k in sorted(entries)},
        }
        out_path = CONFIG_DIR / faction / "detachments.json"
        out_path.write_text(json.dumps(out, indent=2, ensure_ascii=True) + "\n")
        written += 1
        print(f"{faction:28s} {len(entries):3d} detachments -> {out_path.name}")

    print(f"\n{written} factions written")


if __name__ == "__main__":
    main()