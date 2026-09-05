#!/usr/bin/env bash
# Restore canonical Codex App skills, safe settings, and user-selected plugins.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_SRC="$REPO_DIR/codex"
CODEX_DIR="${CODEX_HOME:-$HOME/.codex}"
AGENTS_DIR="${AGENTS_HOME:-$HOME/.agents}"
DRY_RUN=0

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    -h|--help) echo "Usage: bash codex/install.sh [--dry-run]"; exit 0 ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

log() { printf "\033[1;36m[codex-install]\033[0m %s\n" "$*"; }
run() {
  if [ "$DRY_RUN" = 1 ]; then
    printf '[dry-run] %q ' "$@"
    printf '\n'
  else
    "$@"
  fi
}

command -v python3 >/dev/null || { echo "python3 not found in PATH" >&2; exit 1; }
command -v jq >/dev/null || { echo "jq not found in PATH" >&2; exit 1; }
command -v codex >/dev/null || { echo "codex not found in PATH" >&2; exit 1; }

run mkdir -p "$AGENTS_DIR/skills"

install_skill_dir() {
  local src="$1"
  local dest_root="$2"
  [ -d "$src" ] || return 0
  for skill in "$src"/*/; do
    [ -d "$skill" ] || continue
    local name
    name=$(basename "$skill")
    log "installing skill $name -> $dest_root"
    run rm -rf "$dest_root/$name"
    run cp -R "$skill" "$dest_root/$name"
  done
}

install_skill_dir "$CODEX_SRC/skills" "$AGENTS_DIR/skills"

log "merging safe Codex config template"
if [ "$DRY_RUN" = 1 ]; then
  echo "[dry-run] merge $CODEX_SRC/config.template.toml into ~/.codex/config.toml"
else
  python3 "$REPO_DIR/scripts/merge_codex_config.py" "$CODEX_DIR/config.toml" "$CODEX_SRC/config.template.toml"
fi

log "restoring portable Git marketplaces"
manifest="$CODEX_SRC/manifest.json"
if [ -f "$manifest" ]; then
  while IFS=$'\t' read -r marketplace_name marketplace_source; do
    [ -n "$marketplace_name" ] || continue
    [ -n "$marketplace_source" ] || continue
    if [ "$DRY_RUN" = 1 ]; then
      echo "[dry-run] codex plugin marketplace add $marketplace_source  # $marketplace_name"
    elif codex plugin marketplace list --json \
      | jq -e --arg name "$marketplace_name" --arg source "$marketplace_source" \
        '.marketplaces[]? | select(.name == $name and .marketplaceSource.source == $source)' \
        >/dev/null; then
      log "marketplace $marketplace_name already configured"
    else
      codex plugin marketplace add --json "$marketplace_source" >/dev/null || {
        echo "warning: could not add marketplace $marketplace_name from $marketplace_source" >&2
      }
    fi
  done < <(jq -r '.marketplaces[]? | select(.source_type == "git") | [.name, .source] | @tsv' "$manifest")
fi

log "restoring user-selected Codex plugins"
if [ -f "$manifest" ]; then
  while IFS= read -r plugin_id; do
    [ -n "$plugin_id" ] || continue
    if [ "$DRY_RUN" = 1 ]; then
      echo "[dry-run] codex plugin add $plugin_id"
    else
      codex plugin add --json "$plugin_id" >/dev/null || {
        echo "warning: could not install $plugin_id; finish setup in Codex Plugins" >&2
      }
    fi
  done < <(jq -r '.plugins.restore[]? // empty' "$manifest")
fi

log "done"
