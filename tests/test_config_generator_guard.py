"""Guard the curated-config overwrite in generate_configs_from_bsdata.py.

`data/config/` is curated by hand, and the generator cannot rebuild curated
content: a prior measured `--all` run changed 96 files (+18,158/-32,769 lines)
and can delete curated units outright when pruning stale entries. Nothing but a
doc comment stopped that from being run casually.

These tests run the real CLI against a throwaway repo in tmp_path and assert the
files are byte-identical after a refused run. The sandbox links (not copies) the
48MB bsdata submodule and copies the one merged file the generator reads, so
tests are cheap but still reach the actual write path.

Mutation checks that must fail if the guard is weakened:
  - delete the pre-flight in main()          -> tests fail
  - drop `--force` from the pre-flight       -> tests fail (no escape hatch)
  - stop forwarding `--force`                -> tests fail
  - count an uncountable file as empty       -> tests fail
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "generate_configs_from_bsdata.py"

sys.path.insert(0, str(REPO_ROOT))
from scripts.generate_configs_from_bsdata import (  # noqa: E402
    CONFIG_FILES,
    REFUSAL_EXIT,
    curated_units_in,
    populated_units,
    unparseable_files,
)

SLUG = "chaos-space-marines"


@pytest.fixture
def sandbox(tmp_path):
    """A copy of the repo with a populated curated config dir.

    Copies the script and adapter (they are small), symlinks the bsdata
    submodule, and copies the one merged file the generator reads. This is
    enough for `generate_configs_for_faction` to reach its write block, so the
    `--force` tests exercise a real overwrite rather than an early return.
    """
    root = tmp_path / "repo"
    (root / "scripts").mkdir(parents=True)
    (root / "data" / "config" / SLUG).mkdir(parents=True)
    (root / "data" / "merged").mkdir(parents=True)
    shutil.copy(SCRIPT, root / "scripts" / SCRIPT.name)
    shutil.copytree(
        REPO_ROOT / "adapter", root / "adapter",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    # bsdata is a ~48MB submodule. BSDataParser11e only stores the path, so a
    # symlink is equivalent to a copy and keeps the fixture fast.
    os.symlink(REPO_ROOT / "bsdata", root / "bsdata", target_is_directory=True)
    merged = REPO_ROOT / "data" / "merged" / f"{SLUG}.json"
    if not merged.exists():
        pytest.skip(f"merged data missing for {SLUG}")
    shutil.copy(merged, root / "data" / "merged" / f"{SLUG}.json")
    for fname in CONFIG_FILES:
        src = REPO_ROOT / "data" / "config" / SLUG / fname
        if src.exists():
            shutil.copy(src, root / "data" / "config" / SLUG / fname)
    assert (root / "data" / "config" / SLUG).glob("*.json"), "fixture has no config to protect"
    return root


def _run(root, *args, expect=None):
    out = subprocess.run(
        [sys.executable, str(root / "scripts" / SCRIPT.name), *args],
        cwd=root, capture_output=True, text=True, timeout=600,
    )
    if expect is not None:
        assert out.returncode == expect, (
            f"exit {out.returncode} != {expect}\n--- stdout ---\n{out.stdout}\n"
            f"--- stderr ---\n{out.stderr}"
        )
    return out


def _config_bytes(root):
    """Every file in the config dir, not just CONFIG_FILES.

    Walking the directory means a newly created file cannot hide from the check.
    """
    d = root / "data" / "config" / SLUG
    return {f.name: f.read_bytes() for f in sorted(d.iterdir()) if f.is_file()}


# ---------------------------------------------------------------------------
# The counting helpers
# ---------------------------------------------------------------------------


def test_populated_units_counts_units_not_sections(tmp_path):
    # Config files are flat: top-level keys are unit names, "_"-prefixed keys
    # are metadata and must not be counted. Values that are not dicts are not
    # units either — the two filters must be pinned independently, or the suite
    # cannot tell which one is doing the work.
    (tmp_path / "squads.json").write_text(json.dumps({
        "_note": "metadata",                 # dict-ish, but a unit name would not start with _
        "_source": {"catalog": "x"},         # metadata AND a dict: only "_" can exclude it
        "Blood Ravens": {"c": 4},            # a real unit
        "Fangs": {},                         # a real unit, empty config
    }))
    assert populated_units(tmp_path) == {"squads.json": 2}
    assert curated_units_in(tmp_path) == 2


def test_empty_dir_is_not_curated(tmp_path):
    assert curated_units_in(tmp_path) == 0
    (tmp_path / "squads.json").write_text("{}")
    assert curated_units_in(tmp_path) == 0
    (tmp_path / "squads.json").write_text(json.dumps({"_note": "only metadata"}))
    assert curated_units_in(tmp_path) == 0


@pytest.mark.parametrize("body", ["{ this is not json", "[]", '"a bare string"', "null"])
def test_uncountable_file_still_blocks_the_guard(tmp_path, body):
    """A config we cannot count must not be mistaken for an unseeded one.

    "Unparseable" and "wrong shape" are both unknown. Treating unknown as empty
    hands a corrupt config to the generator and destroys the only copy of
    whatever curation it held — the one case where losing data is worst.
    """
    (tmp_path / "squads.json").write_text(body)
    assert populated_units(tmp_path) == {"squads.json": -1}
    assert curated_units_in(tmp_path) == 1, "uncountable file must count as populated"
    assert unparseable_files(tmp_path) == ["squads.json"]


def test_missing_file_is_absent_not_uncountable(tmp_path):
    """Absent is genuinely empty; only unparseable content is unknown."""
    assert unparseable_files(tmp_path) == []
    assert populated_units(tmp_path) == {}


# ---------------------------------------------------------------------------
# The CLI guard: refuse by default
# ---------------------------------------------------------------------------


def test_refuses_to_overwrite_populated_config(sandbox):
    before = _config_bytes(sandbox)

    out = _run(sandbox, "--faction", SLUG, expect=REFUSAL_EXIT)

    assert "REFUSING" in out.stdout
    assert "--force" in out.stdout
    assert _config_bytes(sandbox) == before, "config was modified despite the refusal"


def test_refusal_names_the_faction_and_curated_count(sandbox):
    out = _run(sandbox, "--faction", SLUG, expect=REFUSAL_EXIT)
    assert SLUG in out.stdout
    assert "curated unit" in out.stdout


def test_refusal_states_that_dry_run_shows_no_diff(sandbox):
    """Do not send an operator to a check the tool cannot perform.

    --dry-run prints counts and removals; the write block is skipped, so there
    is no diff to review. The honest instruction is to check `git diff` after
    --force, not to look for a diff the dry-run never produced.
    """
    out = _run(sandbox, "--faction", SLUG, expect=REFUSAL_EXIT)
    assert "NOT a diff" in out.stdout
    assert "git diff" in out.stdout


def test_refusal_happens_before_any_faction_is_written(sandbox):
    """Pre-flight must run first: a refusal mid-loop leaves a half-regen tree.

    `--all` walks every slug and writes as it goes, so a guard implemented
    inside the per-faction writer would already have written the factions it
    visited before refusing on the first populated one.
    """
    out = _run(sandbox, "--all", expect=REFUSAL_EXIT)
    assert "REFUSING" in out.stdout
    assert "GENERATING" not in out.stdout, "generation started despite the refusal"
    assert _config_bytes(sandbox), "config vanished"


def test_dry_run_is_allowed_and_writes_nothing(sandbox):
    before = _config_bytes(sandbox)
    out = _run(sandbox, "--faction", SLUG, "--dry-run", expect=0)
    assert out.stderr == "", f"dry-run should not warn on stderr:\n{out.stderr}"
    assert "REFUSING" not in out.stdout
    assert _config_bytes(sandbox) == before


# ---------------------------------------------------------------------------
# The escape hatch: --force. This is the half that does the damage, so it is
# tested at least as hard as the refusal.
# ---------------------------------------------------------------------------


def test_force_bypasses_the_refusal(sandbox):
    out = _run(sandbox, "--faction", SLUG, "--force", expect=0)
    assert "REFUSING" not in out.stdout
    assert "GENERATING" in out.stdout


def test_force_actually_writes(sandbox):
    """--force must reach a real write, not an early return that looks like success.

    Guards against the "silent no-op reports success" failure: if the generator
    bailed out before writing (missing merged data, no constraints, wrong slug
    mapping), this test would see no change and fail.
    """
    before = _config_bytes(sandbox)
    out = _run(sandbox, "--faction", SLUG, "--force", expect=0)
    assert "Wrote:" in out.stdout, f"--force wrote nothing:\n{out.stdout}"
    assert _config_bytes(sandbox) != before, \
        "--force overwrote nothing, so this is not exercising the write path"


def test_force_overwrites_curated_content(sandbox):
    """The warning says curated entries get replaced by emptier ones. Prove it.

    A refusal that is merely inconvenient would be fine, but this is the whole
    hazard: the generator's output must actually differ from hand-curation, or
    the guard is protecting data that regenerates losslessly.
    """
    before = _config_bytes(sandbox)
    _run(sandbox, "--faction", SLUG, "--force", expect=0)
    after = _config_bytes(sandbox)
    assert after != before, "regeneration was lossless; guard protects nothing"


def test_force_plus_dry_run_writes_nothing(sandbox):
    """--force must not turn --dry-run into a write; dry-run wins."""
    before = _config_bytes(sandbox)
    out = _run(sandbox, "--faction", SLUG, "--force", "--dry-run", expect=0)
    assert "Wrote:" not in out.stdout
    assert _config_bytes(sandbox) == before
