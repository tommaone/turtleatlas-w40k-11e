"""Guard: config info blocks must match merged BSData statlines.

Preparedness for fleet-wide statline changes: config `info` blocks are
copies of datasheet stats and silently rot when GW updates statlines
(the engine's merged-data fallback masks the rot). This test runs
sync_config_info.py --check and fails on any drift.

Fix is mechanical: python3 scripts/sync_config_info.py
"""
import subprocess
import sys
from pathlib import Path


def test_config_info_matches_merged():
    r = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent.parent
                             / "scripts" / "sync_config_info.py"), "--check"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, (
        f"config info blocks drifted from merged BSData stats:\n{r.stdout}\n"
        "Fix: python3 scripts/sync_config_info.py"
    )
