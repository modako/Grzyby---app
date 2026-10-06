#!/usr/bin/env bash
# Commit ./site and push it to gh-pages (retries if another workflow pushed in the meantime).
set -euo pipefail
cd site
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git add -A
git commit -q -m "${1:-Update published data}" || { echo "Nothing to publish"; exit 0; }
for i in 1 2 3 4; do
  git push -q origin gh-pages && exit 0
  git pull -q --rebase origin gh-pages || true
  sleep $((i * 5))
done
exit 1
