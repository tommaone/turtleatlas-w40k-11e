"""Tests for idempotent findings generation.

`data/merged/` and `findings/` are committed build output guarded by
scripts/check_artifacts_current.py. That guard is only meaningful if a
regeneration that produces identical content leaves the working tree clean --
otherwise every page is rewritten with a fresh timestamp, the drift check
drowns in noise, and a real change is indistinguishable from the clock.
"""
import os
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import scripts.gen_findings_html as gen  # noqa: E402


FOOTER = ('<span class="gen-time">generated 2026-09-28 19:39 UTC</span>')
OTHER = ('<span class="gen-time">generated 2030-01-01 00:00 UTC</span>')


def test_mask_ts_ignores_only_the_timestamp():
    assert gen._mask_ts(FOOTER) == gen._mask_ts(OTHER)
    assert gen._mask_ts(FOOTER) != gen._mask_ts(FOOTER.replace('span', 'div'))


def test_write_skips_file_when_only_the_clock_moved(tmp_path):
    path = tmp_path / 'findings.html'
    path.write_text(FOOTER, encoding='utf-8')

    assert gen._write_if_changed(str(path), OTHER) is False
    assert path.read_text(encoding='utf-8') == FOOTER, 'timestamp must survive'


def test_write_applies_when_content_differs(tmp_path):
    path = tmp_path / 'findings.html'
    path.write_text(FOOTER, encoding='utf-8')

    assert gen._write_if_changed(str(path), OTHER + '<p>Boomstikks</p>') is True
    assert 'Boomstikks' in path.read_text(encoding='utf-8')


def test_write_creates_missing_file(tmp_path):
    path = tmp_path / 'new.html'
    assert gen._write_if_changed(str(path), FOOTER) is True
    assert path.read_text(encoding='utf-8') == FOOTER
