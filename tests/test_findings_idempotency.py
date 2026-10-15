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


def test_classify_separates_content_drift_from_timestamp_only(tmp_path,
                                                             monkeypatch):
    """The guard must tell apart 'commit this' from 'revert this'."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        'chk', os.path.join(ROOT, 'scripts', 'check_artifacts_current.py'))
    chk = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(chk)

    head_ts = 'generated 2026-09-28 19:39 UTC'
    work_ts = head_ts.replace('19:39', '20:00')
    head = {
        'real.html': head_ts + '<p>Boomstikks</p>',
        'clock.html': head_ts + '<p>same</p>',
    }
    work = {
        'real.html': work_ts + '<p>Boomstikks removed</p>',  # clock + content
        'clock.html': work_ts + '<p>same</p>',               # clock only
    }
    for rel, text in work.items():
        (tmp_path / rel).write_text(text, encoding='utf-8')

    monkeypatch.setattr(chk, 'ROOT', str(tmp_path))
    monkeypatch.setattr(chk, '_head_version', lambda rel: head[rel])

    content, ts_only = chk.classify(sorted(work))
    assert content == ['real.html'], 'changed content must be flagged as real'
    assert ts_only == ['clock.html'], 'clock-only change must not look like drift'


def test_stale_paths_flags_untracked_artifacts(tmp_path, monkeypatch):
    """A brand-new artifact is untracked, so `git diff` cannot see it. The
    guard must still catch it, or a newly generated file drifts unnoticed."""
    import importlib.util
    import subprocess

    spec = importlib.util.spec_from_file_location(
        'chk', os.path.join(ROOT, 'scripts', 'check_artifacts_current.py'))
    chk = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(chk)

    def git(*a):
        subprocess.run(['git', *a], cwd=tmp_path, check=True,
                       capture_output=True, text=True)

    git('init', '-q')
    git('config', 'user.email', 't@t.t')
    git('config', 'user.name', 't')
    (tmp_path / 'findings').mkdir()
    (tmp_path / 'findings' / 'old.json').write_text('{"a":1}', encoding='utf-8')
    git('add', 'findings/old.json')
    git('commit', '-qm', 'init')
    (tmp_path / 'findings' / 'old.json').write_text('{"a":2}', encoding='utf-8')
    (tmp_path / 'findings' / 'new.json').write_text('{"b":1}', encoding='utf-8')

    monkeypatch.setattr(chk, 'ROOT', str(tmp_path))
    monkeypatch.setattr(chk, 'WATCHED', ('findings',))

    stale = chk._stale_paths()
    assert 'findings/old.json' in stale, 'modified tracked file missed'
    assert 'findings/new.json' in stale, 'untracked artifact must be flagged'

    # classify() must route the untracked file to content drift, not crash:
    # `git show HEAD:findings/new.json` fails, and the OSError/CalledProcessError
    # branch is what keeps a brand-new artifact from being silently dropped.
    content, ts_only = chk.classify(stale)
    assert 'findings/new.json' in content, 'untracked artifact must be content drift'
    assert 'findings/new.json' not in ts_only, 'untracked file is not a timestamp bump'
