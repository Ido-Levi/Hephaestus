#!/usr/bin/env bash
set -euo pipefail

# Safe upstream update helper
# - Creates safety tag and git bundle
# - Ensures `upstream` remote exists and fetches it
# - Resets main to upstream/main
# - Rebases local/customizations on top of main

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

echo "[update] Repo root: $repo_root"

current_branch=$(git rev-parse --abbrev-ref HEAD)
echo "[update] Current branch: $current_branch"

# 1) Safety snapshots
ts=$(date +%Y%m%d-%H%M%S)
tag="pre-upstream-setup-${ts}"
bundle_path="${repo_root}/../hephaestus-backup-${ts}.bundle"

echo "[update] Creating safety tag: $tag"
git tag -a "$tag" -m "Safety snapshot before upstream update" || true

echo "[update] Creating git bundle: $bundle_path"
git bundle create "$bundle_path" --all
echo "[update] Bundle created at: $bundle_path"

# 2) Ensure upstream remote
if git remote get-url upstream >/dev/null 2>&1; then
  echo "[update] upstream remote exists: $(git remote get-url upstream)"
else
  echo "[update] Adding upstream remote"
  git remote add upstream https://github.com/Ido-Levi/Hephaestus.git
fi

echo "[update] Fetching upstream"
git fetch upstream

# 3) Reset main to upstream/main
echo "[update] Resetting main to upstream/main"
git checkout main
git reset --hard upstream/main

# 4) Rebase local/customizations on main
echo "[update] Rebasing local/customizations on top of main"
if git show-ref --verify --quiet refs/heads/local/customizations; then
  git checkout local/customizations
  if ! git rebase main; then
    echo "[update] Rebase conflict encountered; aborting to keep repo stable."
    git rebase --abort || true
    echo "[update] Please resolve conflicts manually and rerun."
    exit 1
  fi
else
  echo "[update] Branch local/customizations not found; creating it off current state"
  git checkout -b local/customizations
fi

echo "[update] Done. Current branch: $(git rev-parse --abbrev-ref HEAD)"
git status -sb
