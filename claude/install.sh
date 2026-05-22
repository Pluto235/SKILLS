#!/usr/bin/env bash
# Restore Claude Code skills + plugins + safe settings from claude/.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_SRC="$REPO_DIR/claude"
CLAUDE_DIR="$HOME/.claude"
PLUGINS_DIR="$CLAUDE_DIR/plugins"
MARKETPLACES_DIR="$PLUGINS_DIR/marketplaces"
PLUGIN_CACHE_DIR="$PLUGINS_DIR/cache"
DRY_RUN=0

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    -h|--help) echo "Usage: bash claude/install.sh [--dry-run]"; exit 0 ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

log() { printf "\033[1;36m[claude-install]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[claude-install]\033[0m %s\n" "$*" >&2; }
run() {
  if [ "$DRY_RUN" = 1 ]; then
    printf '[dry-run] %q ' "$@"
    printf '\n'
  else
    "$@"
  fi
}

command -v git >/dev/null || { echo "git not found in PATH" >&2; exit 1; }
command -v jq >/dev/null || { echo "jq not found in PATH" >&2; exit 1; }

manifest="$CLAUDE_SRC/manifest.json"
[ -f "$manifest" ] || { echo "claude/manifest.json missing" >&2; exit 1; }

run mkdir -p "$CLAUDE_DIR/skills" "$MARKETPLACES_DIR" "$PLUGIN_CACHE_DIR"

log "syncing claude/skills -> ~/.claude/skills"
for skill in "$CLAUDE_SRC"/skills/*/; do
  [ -d "$skill" ] || continue
  name=$(basename "$skill")
  log "  · $name"
  run rm -rf "$CLAUDE_DIR/skills/$name"
  run cp -R "$skill" "$CLAUDE_DIR/skills/$name"
done

if [ -f "$CLAUDE_SRC/statusline-command.sh" ]; then
  log "installing statusline-command.sh"
  run cp "$CLAUDE_SRC/statusline-command.sh" "$CLAUDE_DIR/statusline-command.sh"
  run chmod +x "$CLAUDE_DIR/statusline-command.sh"
fi

mp_count=$(jq '.marketplaces | length' "$manifest")
for i in $(seq 0 $((mp_count - 1))); do
  mp_name=$(jq -r ".marketplaces[$i].name" "$manifest")
  mp_type=$(jq -r ".marketplaces[$i].source.source" "$manifest")
  mp_repo=$(jq -r ".marketplaces[$i].source.repo // .marketplaces[$i].source.url // empty" "$manifest")
  case "$mp_type" in
    github) mp_url="https://github.com/${mp_repo}.git" ;;
    url|git) mp_url="$mp_repo" ;;
    *) warn "unknown marketplace source type: $mp_type"; continue ;;
  esac
  mp_dir="$MARKETPLACES_DIR/$mp_name"
  if [ "$DRY_RUN" = 1 ]; then
    log "would install/update marketplace $mp_name from $mp_url"
  elif [ -d "$mp_dir/.git" ]; then
    log "updating marketplace $mp_name"
    git -C "$mp_dir" fetch --quiet origin
    git -C "$mp_dir" reset --quiet --hard '@{u}' || true
  else
    log "cloning marketplace $mp_name from $mp_url"
    rm -rf "$mp_dir"
    git clone --quiet --depth 1 "$mp_url" "$mp_dir" || git clone --quiet "$mp_url" "$mp_dir"
  fi
done

if [ "$DRY_RUN" = 0 ]; then
  log "writing known_marketplaces.json"
  km_file="$PLUGINS_DIR/known_marketplaces.json"
  [ -f "$km_file" ] || echo '{}' > "$km_file"
  now=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
  new_km=$(jq -n '{}')
  for i in $(seq 0 $((mp_count - 1))); do
    mp_name=$(jq -r ".marketplaces[$i].name" "$manifest")
    mp_src=$(jq ".marketplaces[$i].source" "$manifest")
    new_km=$(jq --arg n "$mp_name" --argjson src "$mp_src" --arg loc "$MARKETPLACES_DIR/$mp_name" --arg ts "$now" \
      '. + {($n): {source: $src, installLocation: $loc, lastUpdated: $ts}}' <<<"$new_km")
  done
  jq -s '.[0] * .[1]' "$km_file" <(echo "$new_km") > "$km_file.tmp"
  mv "$km_file.tmp" "$km_file"
fi

log "resolving enabled Claude plugins"
if [ "$DRY_RUN" = 1 ]; then
  jq -r '.enabled_plugins[]' "$manifest" | sed 's/^/[dry-run] enable plugin /'
else
  ip_file="$PLUGINS_DIR/installed_plugins.json"
  [ -f "$ip_file" ] || echo '{"version":2,"plugins":{}}' > "$ip_file"
  new_plugins=$(jq -n '{}')
  ep_count=$(jq '.enabled_plugins | length' "$manifest")
  now=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
  for i in $(seq 0 $((ep_count - 1))); do
    full=$(jq -r ".enabled_plugins[$i]" "$manifest")
    plugin_name="${full%@*}"
    mp_name="${full#*@}"
    mp_manifest="$MARKETPLACES_DIR/$mp_name/.claude-plugin/marketplace.json"
    [ -f "$mp_manifest" ] || { warn "marketplace manifest not found for $mp_name, skipping $plugin_name"; continue; }
    src=$(jq --arg n "$plugin_name" '.plugins[] | select(.name == $n) | .source' "$mp_manifest")
    [ -n "$src" ] && [ "$src" != "null" ] || { warn "plugin $plugin_name not found in $mp_name, skipping"; continue; }
    install_path=""
    if echo "$src" | jq -e 'type == "string"' >/dev/null; then
      rel=$(echo "$src" | jq -r '.')
      install_path="$MARKETPLACES_DIR/$mp_name/${rel#./}"
    else
      src_type=$(echo "$src" | jq -r '.source')
      src_url=$(echo "$src" | jq -r '.url')
      src_ref=$(echo "$src" | jq -r '.ref // "main"')
      cache_path="$PLUGIN_CACHE_DIR/$mp_name/$plugin_name/unknown"
      case "$src_type" in
        git-subdir)
          src_subpath=$(echo "$src" | jq -r '.path')
          tmpdir=$(mktemp -d)
          git clone --quiet --depth 1 --branch "$src_ref" "$src_url" "$tmpdir" 2>/dev/null || git clone --quiet "$src_url" "$tmpdir"
          git -C "$tmpdir" checkout --quiet "$src_ref" 2>/dev/null || true
          rm -rf "$cache_path"
          mkdir -p "$(dirname "$cache_path")"
          cp -R "$tmpdir/$src_subpath" "$cache_path"
          rm -rf "$tmpdir"
          install_path="$cache_path"
          ;;
        url|git)
          rm -rf "$cache_path"
          git clone --quiet --depth 1 "$src_url" "$cache_path" 2>/dev/null || git clone --quiet "$src_url" "$cache_path"
          install_path="$cache_path"
          ;;
        *) warn "unknown plugin source type '$src_type' for $plugin_name"; continue ;;
      esac
    fi
    entry=$(jq -n --arg ip "$install_path" --arg ts "$now" \
      '[{scope:"user", installPath:$ip, version:"unknown", installedAt:$ts, lastUpdated:$ts}]')
    new_plugins=$(jq --arg k "$full" --argjson v "$entry" '. + {($k): $v}' <<<"$new_plugins")
  done
  jq --argjson new "$new_plugins" '.version = 2 | .plugins = ((.plugins // {}) * $new)' "$ip_file" > "$ip_file.tmp"
  mv "$ip_file.tmp" "$ip_file"
fi

log "merging safe settings"
if [ "$DRY_RUN" = 1 ]; then
  echo "[dry-run] merge $CLAUDE_SRC/settings.template.json into ~/.claude/settings.json"
else
  settings_file="$CLAUDE_DIR/settings.json"
  [ -f "$settings_file" ] || echo '{}' > "$settings_file"
  tmpl=$(jq --arg home "$HOME" 'walk(if type == "string" then gsub("\\$HOME"; $home) else . end)' "$CLAUDE_SRC/settings.template.json")
  jq -s '.[0] * .[1]' "$settings_file" <(echo "$tmpl") > "$settings_file.tmp"
  mv "$settings_file.tmp" "$settings_file"
fi

log "done"
