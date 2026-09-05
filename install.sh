#!/usr/bin/env bash
# Backward-compatible entrypoint. Restores Codex App config.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$REPO_DIR/install-all.sh" "$@"
