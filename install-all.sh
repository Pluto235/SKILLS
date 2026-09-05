#!/usr/bin/env bash
# Restore the managed Codex App configuration from this repo.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRY_RUN=0

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    -h|--help)
      echo "Usage: bash install-all.sh [--dry-run]"
      exit 0
      ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

command -v python3 >/dev/null || { echo "python3 not found in PATH" >&2; exit 1; }

args=()
if [ "$DRY_RUN" = 1 ]; then
  args+=(--dry-run)
fi

bash "$REPO_DIR/codex/install.sh" "${args[@]}"

echo
echo "Codex App configuration processed."
if [ "$DRY_RUN" = 1 ]; then
  echo "Dry run only; no files were changed."
else
  echo "Restart Codex so new skills/plugins are loaded."
fi
