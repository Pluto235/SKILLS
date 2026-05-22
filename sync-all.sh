#!/usr/bin/env bash
# Snapshot safe Claude Code and Codex configuration into this repo.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

command -v jq >/dev/null || { echo "jq not found in PATH" >&2; exit 1; }
command -v git >/dev/null || { echo "git not found in PATH" >&2; exit 1; }
command -v python3 >/dev/null || { echo "python3 not found in PATH" >&2; exit 1; }

bash "$REPO_DIR/claude/sync.sh"
bash "$REPO_DIR/codex/sync.sh"

echo
echo "[sync-all] checking for obvious secret patterns"
secret_pattern='sk-[A-Za-z0-9_-]{12,}|ghp_[A-Za-z0-9_]{20,}|ANTHROPIC''_AUTH_TOKEN|GITHUB''_PERSONAL_ACCESS_TOKEN'
if (cd "$REPO_DIR" && rg -n --hidden --glob '!.git/**' --glob '!README.md' "$secret_pattern"); then
  echo "[sync-all] possible secret found; refusing to continue" >&2
  exit 1
fi

echo
echo "[sync-all] git status"
git -C "$REPO_DIR" status --short
echo
echo "[sync-all] git diff stat"
git -C "$REPO_DIR" --no-pager diff --stat
echo
echo "Snapshot complete. Review the diff, then commit and push manually:"
echo "  cd $REPO_DIR"
echo "  git add -A && git commit -m \"sync agent config from \$(hostname)\" && git push"
