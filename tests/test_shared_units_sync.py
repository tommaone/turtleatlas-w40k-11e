"""Guard: shared god-marine squad entries must stay in sync with their origin.

God-marines (Noise/Plague/Rubric/Berzerkers) are priced under their god
faction's MFM and legally fielded by Chaos Space Marines. The consumer's
squad entry must be byte-identical to the origin's — otherwise the consumer
is stale (the original bug: CSM Noise Marines drifted to n=5 while EC
updated to n=6).

If this test fails, run:
    python3 scripts/sync_shared_units.py

The sharing map (SHARED_UNITS) lives in scripts/sync_shared_units.py and is
imported here so there is a single source of truth for what is shared.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.sync_shared_units import SHARED_UNITS

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "data" / "config"


def _load_squads(fid: str) -> dict:
    return json.load(open(CONFIG / fid / "squads.json"))


@pytest.mark.parametrize(
    "unit, origin, consumer",
    [(u, s["origin"], c) for u, s in SHARED_UNITS.items() for c in s["consumers"]],
    ids=lambda x: x if isinstance(x, str) else "",
)
def test_shared_squad_in_sync(unit: str, origin: str, consumer: str):
    """Consumer's copy of a shared unit must equal the origin's entry."""
    origin_entry = _load_squads(origin).get(unit)
    if origin_entry is None:
        pytest.fail(f"{origin}/{unit}: origin entry missing — fix the origin config")
    consumer_entry = _load_squads(consumer).get(unit)
    if consumer_entry is None:
        pytest.fail(
            f"{consumer}/{unit}: missing (should be synced from {origin}). "
            f"Run: python3 scripts/sync_shared_units.py"
        )
    if consumer_entry != origin_entry:
        # Show the drifted fields for quick diagnosis
        drift = []
        all_keys = set(consumer_entry) | set(origin_entry)
        for k in sorted(all_keys):
            if consumer_entry.get(k) != origin_entry.get(k):
                drift.append(f"  {k}: consumer={consumer_entry.get(k)!r}  origin={origin_entry.get(k)!r}")
        pytest.fail(
            f"{consumer}/{unit}: drifted from origin {origin}. "
            f"Run: python3 scripts/sync_shared_units.py\n" + "\n".join(drift)
        )
