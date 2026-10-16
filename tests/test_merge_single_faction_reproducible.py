"""Guard: one `merge.py --faction` run reproduces its committed artifact.

`memory/reference.md` used to claim a single `--faction` regeneration drops
abilities on cross-faction fallback units, leaving `--all` as the only correct
path. That was written before commit 5725a9c moved the global cross-faction
index build into `main()` for both paths, and it is false at HEAD: the CLI
builds the index first whatever the selector, so a single-faction run is
byte-identical to the committed file.

This runs the real CLI into a temp dir rather than calling `merge_faction()`
in-process — the in-process call takes no `global_index`, which is exactly the
regression this guards (a caller that forgets it gets fallback units with no
abilities).

space-marines is the faction under test: 17 of its 87 units take their profile
from another catalogue, so it is the one faction where a lost index shows up
in the output at all.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
MERGED = REPO / "data" / "merged"

# The cross-faction fallback faction — see module docstring.
SLUG = "space-marines"


def test_single_faction_cli_matches_committed_artifact(tmp_path):
    """`--faction <slug>` output must be byte-identical to data/merged/<slug>.json."""
    if not (list((REPO / "bsdata").glob("*.json"))
            and list((REPO / "mfm" / "data").glob("*.yaml"))):
        pytest.skip("bsdata/mfm submodule(s) not populated")

    committed = MERGED / f"{SLUG}.json"
    assert committed.exists(), f"no committed merged file for {SLUG}"

    subprocess.run(
        [sys.executable, "adapter/merge.py", "--faction", SLUG,
         "--output", str(tmp_path)],
        cwd=REPO, check=True, capture_output=True, text=True, timeout=900,
    )

    produced = tmp_path / f"{SLUG}.json"
    assert produced.exists(), "merge.py produced no output file"
    assert produced.read_bytes() == committed.read_bytes(), (
        f"adapter/merge.py --faction {SLUG} is not byte-identical to the "
        f"committed artifact — regenerate with adapter/merge.py --all, or the "
        f"bsdata/mfm submodule pins moved under a stale artifact"
    )


def test_cross_faction_units_keep_their_abilities():
    """The claim the byte-identity test pins: fallback units carry abilities.

    Reads the committed artifact (cheap) so the invariant stays visible even
    when the subprocess run above is skipped for an unpopulated submodule.
    """
    data = json.loads((MERGED / f"{SLUG}.json").read_text(encoding="utf-8"))
    cross = [u for u in data["units"]
             if not u.get("in_bsdata") and u.get("profile")]
    assert cross, "space-marines has no cross-faction fallback units — fixture is stale"
    empty = [u["name"] for u in cross
             if not ((u.get("profile") or {}).get("abilities"))]
    assert not empty, f"fallback units with no abilities: {empty}"
