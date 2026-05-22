#!/usr/bin/env bash
# Capture safe ~/.claude state into claude/ without copying credentials.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_DIR="$HOME/.claude"
OUT_DIR="$REPO_DIR/claude"

log() { printf "\033[1;36m[claude-sync]\033[0m %s\n" "$*"; }
die() { printf "\033[1;31m[claude-sync]\033[0m %s\n" "$*" >&2; exit 1; }

command -v jq >/dev/null || die "jq not found in PATH"

mkdir -p "$OUT_DIR/skills"

log "snapshotting Claude skills"
if [ -d "$CLAUDE_DIR/skills" ]; then
  for d in "$CLAUDE_DIR"/skills/*/; do
    [ -d "$d" ] || continue
    rm -rf "$OUT_DIR/skills/$(basename "$d")"
    cp -R "$d" "$OUT_DIR/skills/$(basename "$d")"
    log "  · $(basename "$d")"
  done
fi

if [ -f "$CLAUDE_DIR/statusline-command.sh" ]; then
  log "snapshotting statusline-command.sh"
  cp "$CLAUDE_DIR/statusline-command.sh" "$OUT_DIR/statusline-command.sh"
fi

log "rebuilding manifest.json"
km_file="$CLAUDE_DIR/plugins/known_marketplaces.json"
settings_file="$CLAUDE_DIR/settings.json"

marketplaces='[]'
if [ -f "$km_file" ]; then
  marketplaces=$(jq '[to_entries[] | {name: .key, source: .value.source}]' "$km_file")
fi

enabled_plugins='[]'
if [ -f "$settings_file" ]; then
  enabled_plugins=$(jq '[.enabledPlugins // {} | to_entries[] | select(.value == true) | .key] | sort' "$settings_file")
fi

jq -n --argjson m "$marketplaces" --argjson p "$enabled_plugins" \
  '{marketplaces: $m, enabled_plugins: $p}' > "$OUT_DIR/manifest.json"

log "rebuilding settings.template.json without env credentials"
if [ -f "$settings_file" ]; then
  jq --arg home "$HOME" '
    del(.env)
    | {
        model,
        permissions,
        statusLine,
        effortLevel,
        skipDangerousModePermissionPrompt,
        skipAutoPermissionPrompt,
        enabledPlugins,
        extraKnownMarketplaces
      }
    | with_entries(select(.value != null))
    | walk(if type == "string" then gsub($home; "$HOME") else . end)
  ' "$settings_file" > "$OUT_DIR/settings.template.json"
else
  echo '{}' > "$OUT_DIR/settings.template.json"
fi

log "done"
