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
WATCHED = ('data/merged', 'findings')
SUBMODULES = ('bsdata', 'mfm')


def run(*cmd):
    print(f'$ {" ".join(cmd)}', flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)


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

    print(f'\nSTALE: {len(stale)} committed artifact(s) do not match the '
          f'current code and data:\n', file=sys.stderr)
    for path in stale:
        print(f'  {path}', file=sys.stderr)
    print('\nThe working tree now holds the regenerated output. Either commit '
          'it (the generators are the source of truth) or revert it if the '
          'change is unintended. Do not hand-edit these files.',
          file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main())
