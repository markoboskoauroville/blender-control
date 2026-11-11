#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

MSG="${1:-chore: sync workspace changes}"

# Fetch & rebase if origin/main exists
if git rev-parse --verify origin/main >/dev/null 2>&1; then
  git pull --rebase --autostash origin main
fi

git add -A
if ! git diff --cached --quiet; then
  git commit -m "$MSG"
fi

git push -u origin main
echo "Synced local and remote (origin/main)."
