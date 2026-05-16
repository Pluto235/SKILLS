#!/usr/bin/env bash
# Capture current ~/.claude/ state and write it into this repo.
# Run before `git commit` to push your latest local changes upstream.
#
# Usage: bash sync.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

log() { printf "\033[1;36m[sync]\033[0m %s\n" "$*"; }
die() { printf "\033[1;31m[sync]\033[0m %s\n" "$*" >&2; exit 1; }

command -v jq >/dev/null || die "jq not found in PATH"

# --- 1. skills ---------------------------------------------------------------
log "snapshotting skills/"
mkdir -p "$REPO_DIR/skills"
# Keep a special skill (sync-claude-config) that lives only in the repo and
# is also installed locally. Use rsync semantics via cp -R, but mirror local
# state authoritatively.
# Strategy: remove repo's skill dirs that no longer exist locally, then copy.
for d in "$REPO_DIR"/skills/*/; do
    [ -d "$d" ] || continue
    n=$(basename "$d")
    if [ ! -d "$CLAUDE_DIR/skills/$n" ]; then
        log "  - removing $n (gone from local)"
        rm -rf "$d"
    fi
done
for d in "$CLAUDE_DIR"/skills/*/; do
    [ -d "$d" ] || continue
    n=$(basename "$d")
    rm -rf "$REPO_DIR/skills/$n"
    cp -R "$d" "$REPO_DIR/skills/$n"
    log "  · $n"
done

# --- 2. statusline -----------------------------------------------------------
if [ -f "$CLAUDE_DIR/statusline-command.sh" ]; then
    log "snapshotting statusline-command.sh"
    cp "$CLAUDE_DIR/statusline-command.sh" "$REPO_DIR/statusline-command.sh"
fi

# --- 3. manifest.json (marketplaces + enabled plugins) -----------------------
log "rebuilding manifest.json"
km_file="$CLAUDE_DIR/plugins/known_marketplaces.json"
settings_file="$CLAUDE_DIR/settings.json"

marketplaces='[]'
if [ -f "$km_file" ]; then
    marketplaces=$(jq '[ to_entries[] | { name: .key, source: .value.source } ]' "$km_file")
fi

enabled_plugins='[]'
if [ -f "$settings_file" ]; then
    enabled_plugins=$(jq '[ .enabledPlugins // {} | to_entries[] | select(.value == true) | .key ]' "$settings_file")
fi

jq -n --argjson m "$marketplaces" --argjson p "$enabled_plugins" \
   '{ marketplaces: $m, enabled_plugins: $p }' > "$REPO_DIR/manifest.json"

# --- 4. settings.template.json (managed keys, $HOME-escaped) -----------------
log "rebuilding settings.template.json"
if [ -f "$settings_file" ]; then
    jq --arg home "$HOME" '
      {
        permissions:                       .permissions,
        statusLine:                        .statusLine,
        effortLevel:                       .effortLevel,
        skipDangerousModePermissionPrompt: .skipDangerousModePermissionPrompt,
        skipAutoPermissionPrompt:          .skipAutoPermissionPrompt,
        enabledPlugins:                    .enabledPlugins
      }
      | with_entries(select(.value != null))
      | walk(if type == "string" then gsub($home; "$HOME") else . end)
    ' "$settings_file" > "$REPO_DIR/settings.template.json"
fi

# --- 5. report git diff ------------------------------------------------------
cd "$REPO_DIR"
log "git status:"
git status --short || true
echo
log "git diff stat:"
git --no-pager diff --stat || true
echo
log "snapshot complete. Review the diff above, then commit + push:"
echo "    cd $REPO_DIR"
echo "    git add -A && git commit -m \"sync from \$(hostname)\" && git push"
