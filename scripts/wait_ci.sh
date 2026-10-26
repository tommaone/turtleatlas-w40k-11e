#!/usr/bin/env bash
# Block until the ci run for a commit settles, then exit with its status.
#
#   scripts/wait_ci.sh            # latest commit on HEAD
#   scripts/wait_ci.sh <sha>      # a specific commit
#
# Exit codes: 0 ci green, 1 ci failed, 2 no run found for that commit.
set -euo pipefail

sha=${1:-$(git rev-parse HEAD)}

# Give GitHub a moment to register the run after a push.
for _ in 1 2 3 4 5 6 7 8 9 10; do
  run=$(gh run list --workflow ci --commit "$sha" --limit 1 \
    --json databaseId --jq '.[0].databaseId // empty')
  [ -n "$run" ] && break
  sleep 6
done

if [ -z "${run:-}" ]; then
  echo "no ci run found for $sha" >&2
  exit 2
fi

echo "watching ci run $run for ${sha:0:7}"
gh run watch "$run" --exit-status --interval 15
