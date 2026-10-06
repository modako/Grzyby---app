#!/usr/bin/env bash
# Check out the gh-pages branch (published data) into ./site, creating it if it does not exist yet.
set -euo pipefail
if git ls-remote --exit-code --heads origin gh-pages >/dev/null; then
  git fetch -q origin gh-pages
  git worktree add -q site origin/gh-pages
  git -C site checkout -q -B gh-pages
else
  git worktree add -q --detach site
  git -C site checkout -q --orphan gh-pages
  git -C site rm -rq --cached . || true
  find site -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
fi
touch site/.nojekyll
