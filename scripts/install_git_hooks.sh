#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOK_PATH="$REPO_ROOT/.git/hooks/post-commit"

cat > "$HOOK_PATH" <<'EOF'
#!/usr/bin/env bash
if [ "${SKIP_AUTO_PUSH:-0}" = "1" ]; then
  exit 0
fi
if git remote get-url origin >/dev/null 2>&1; then
  echo "[post-commit] Auto-pushing commit to origin/main..."
  git push origin HEAD:main || echo "[post-commit] Warning: push failed; run ./scripts/sync_github.sh"
fi
EOF

chmod +x "$HOOK_PATH"
echo "Installed auto-sync git hook at $HOOK_PATH"
