#!/usr/bin/env python3
"""Fail when committed derived artifacts are out of date.

`data/merged/` and `findings/` are committed build output. They go stale the
moment the engine, a parser, or the BSData/MFM submodules change — and nothing
else notices, because the test suite reads the committed files back. A stale
artifact therefore makes the suite pass against outdated data, which is worse
than a failing test: it is a green build that proves nothing.

Regenerate everything, then report any tracked file that differs from HEAD.

Exit codes: 0 clean, 1 drift (re-run the generators and commit), 2 setup
problem (submodules not initialised).
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
WATCHED = ('data/merged', 'findings')
SUBMODULES = ('bsdata', 'mfm')


def run(*cmd):
    print(f'$ {" ".join(cmd)}', flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)


def _head_version(rel):
    blob = subprocess.run(['git', 'show', f'HEAD:{rel}'], cwd=ROOT,
                          check=True, capture_output=True, text=True)
    return blob.stdout


def classify(stale):
    """Split stale files into real content drift vs a timestamp-only bump.

    After regeneration a genuine fix and a changed clock can both leave the tree
    dirty, and they call for opposite actions: commit the first, revert the
    second. Without this split the operator has to diff each file by hand and
    guess. The mask is imported rather than duplicated so the two scripts can
    never disagree about what counts as a timestamp.
    """
    from gen_findings_html import _mask_ts

    content, ts_only = [], []
    for rel in stale:
        try:
            with open(os.path.join(ROOT, rel), encoding='utf-8') as f:
                work = f.read()
            head = _head_version(rel)
        except (OSError, subprocess.CalledProcessError):
            content.append(rel)   # unreadable or untracked: treat as real
            continue
        (ts_only if _mask_ts(work) == _mask_ts(head) else content).append(rel)
    return content, ts_only


def _populated(path):
    """True when a submodule directory has been initialised (non-empty)."""
    return os.path.isdir(path) and bool(os.listdir(path))


def main():
    missing = [name for name in SUBMODULES
               if not _populated(os.path.join(ROOT, name))]
    if missing:
        print('ERROR: submodule(s) not initialised: ' + ', '.join(missing),
              file=sys.stderr)
        print('  fix: git submodule update --init --recursive', file=sys.stderr)
        return 2

    run(sys.executable, 'adapter/merge.py', '--all')
    run(sys.executable, 'scripts/gen_findings_html.py', '--all')

    diff = subprocess.run(
        ['git', 'diff', '--name-only', 'HEAD', '--', *WATCHED],
        cwd=ROOT, check=True, capture_output=True, text=True).stdout
    stale = [line for line in diff.splitlines() if line.strip()]

    if not stale:
        print(f'\nOK: {len(WATCHED)} artifact trees match HEAD.')
        return 0

    content, ts_only = classify(stale)

    print(f'\nSTALE: {len(stale)} committed artifact(s) do not match the '
          f'current code and data.', file=sys.stderr)
    if content:
        print(f'\n  Real content drift ({len(content)}) — the working tree now '
              f'holds the regenerated output. Commit it; the generators are '
              f'the source of truth:', file=sys.stderr)
        for path in content:
            print(f'    {path}', file=sys.stderr)
    if ts_only:
        print(f'\n  Timestamp-only ({len(ts_only)}) — identical apart from the '
              f'generation clock, so nothing actually changed. Revert these; '
              f'committing them would be churn:', file=sys.stderr)
        for path in ts_only:
            print(f'    {path}', file=sys.stderr)
    print('\nDo not hand-edit these files.', file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main())
