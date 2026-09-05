#!/usr/bin/env bash
# Capture safe Codex App state without copying auth, sessions, or caches.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_DIR="${CODEX_HOME:-$HOME/.codex}"
AGENTS_DIR="${AGENTS_HOME:-$HOME/.agents}"
OUT_DIR="$REPO_DIR/codex"

log() { printf "\033[1;36m[codex-sync]\033[0m %s\n" "$*"; }

command -v python3 >/dev/null || { echo "python3 not found in PATH" >&2; exit 1; }

mkdir -p "$OUT_DIR/skills"

log "snapshotting canonical ~/.agents/skills"
if [ -d "$AGENTS_DIR/skills" ]; then
  command -v rsync >/dev/null || { echo "rsync not found in PATH" >&2; exit 1; }
  STAGE_DIR=$(mktemp -d)
  trap 'rm -rf "$STAGE_DIR"' EXIT
  for skill in "$AGENTS_DIR"/skills/*; do
    [ -f "$skill/SKILL.md" ] || continue
    name=$(basename "$skill")
    mkdir -p "$STAGE_DIR/$name"
    rsync -aL --exclude='.git/' --exclude='.DS_Store' "$skill/" "$STAGE_DIR/$name/"
    log "  · $name"
  done
  rsync -a --delete "$STAGE_DIR/" "$OUT_DIR/skills/"
  rm -rf "$STAGE_DIR"
  trap - EXIT
else
  find "$OUT_DIR/skills" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
fi

log "refreshing safe config.template.toml"
python3 "$REPO_DIR/scripts/write_codex_template.py" "$CODEX_DIR/config.toml" "$OUT_DIR/config.template.toml"

log "refreshing manifest.json"
python3 "$REPO_DIR/scripts/write_codex_manifest.py" "$OUT_DIR"

log "done"
