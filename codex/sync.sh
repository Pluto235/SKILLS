#!/usr/bin/env bash
# Capture safe Codex state into codex/ without copying auth, sessions, or caches.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_DIR="${CODEX_HOME:-$HOME/.codex}"
AGENTS_DIR="$HOME/.agents"
OUT_DIR="$REPO_DIR/codex"

log() { printf "\033[1;36m[codex-sync]\033[0m %s\n" "$*"; }

command -v python3 >/dev/null || { echo "python3 not found in PATH" >&2; exit 1; }

mkdir -p "$OUT_DIR/skills" "$OUT_DIR/agents-skills" "$OUT_DIR/pua-skills"

log "snapshotting Codex user skills"
if [ -d "$CODEX_DIR/skills" ]; then
  for d in "$CODEX_DIR"/skills/*/; do
    [ -d "$d" ] || continue
    name=$(basename "$d")
    [ "$name" = ".system" ] && continue
    case "$name" in
      codex-primary-runtime) continue ;;
    esac
    rm -rf "$OUT_DIR/skills/$name"
    cp -R "$d" "$OUT_DIR/skills/$name"
    log "  · $name"
  done
fi

log "snapshotting ~/.agents skills"
find "$OUT_DIR/agents-skills" -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} +
if [ -d "$AGENTS_DIR/skills" ]; then
  for d in "$AGENTS_DIR"/skills/*/; do
    [ -d "$d" ] || continue
    cp -R "$d" "$OUT_DIR/agents-skills/$(basename "$d")"
    log "  · $(basename "$d")"
  done
fi

log "refreshing safe config.template.toml"
python3 "$REPO_DIR/scripts/write_codex_template.py" "$CODEX_DIR/config.toml" "$OUT_DIR/config.template.toml"

log "refreshing manifest.json"
python3 "$REPO_DIR/scripts/write_codex_manifest.py" "$OUT_DIR"

log "done"
