#!/usr/bin/env bash
# Restore Claude Code skills + plugins + settings from this repo.
# Idempotent: safe to re-run to pull updates.
#
# Usage: bash install.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
PLUGINS_DIR="$CLAUDE_DIR/plugins"
MARKETPLACES_DIR="$PLUGINS_DIR/marketplaces"
PLUGIN_CACHE_DIR="$PLUGINS_DIR/cache"

log()  { printf "\033[1;36m[install]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[install]\033[0m %s\n" "$*" >&2; }
die()  { printf "\033[1;31m[install]\033[0m %s\n" "$*" >&2; exit 1; }

# --- preflight ---------------------------------------------------------------
command -v git >/dev/null || die "git not found in PATH"
command -v jq  >/dev/null || die "jq not found in PATH (install via apt/brew)"

mkdir -p "$CLAUDE_DIR/skills" "$MARKETPLACES_DIR" "$PLUGIN_CACHE_DIR"

# --- 1. skills ---------------------------------------------------------------
log "syncing skills/ → $CLAUDE_DIR/skills/"
for skill in "$REPO_DIR"/skills/*/; do
    [ -d "$skill" ] || continue
    name=$(basename "$skill")
    rm -rf "$CLAUDE_DIR/skills/$name"
    cp -R "$skill" "$CLAUDE_DIR/skills/$name"
    log "  · $name"
done

# --- 2. statusline -----------------------------------------------------------
if [ -f "$REPO_DIR/statusline-command.sh" ]; then
    log "installing statusline-command.sh"
    cp "$REPO_DIR/statusline-command.sh" "$CLAUDE_DIR/statusline-command.sh"
    chmod +x "$CLAUDE_DIR/statusline-command.sh"
fi

# --- 3. marketplaces ---------------------------------------------------------
manifest="$REPO_DIR/manifest.json"
[ -f "$manifest" ] || die "manifest.json missing"

mp_count=$(jq '.marketplaces | length' "$manifest")
for i in $(seq 0 $((mp_count - 1))); do
    mp_name=$(jq -r ".marketplaces[$i].name" "$manifest")
    mp_type=$(jq -r ".marketplaces[$i].source.source" "$manifest")
    mp_repo=$(jq -r ".marketplaces[$i].source.repo // .marketplaces[$i].source.url" "$manifest")

    case "$mp_type" in
        github)  mp_url="https://github.com/${mp_repo}.git" ;;
        url|git) mp_url="$mp_repo" ;;
        *)       die "unknown marketplace source type: $mp_type" ;;
    esac

    mp_dir="$MARKETPLACES_DIR/$mp_name"
    if [ -d "$mp_dir/.git" ]; then
        log "updating marketplace $mp_name"
        git -C "$mp_dir" fetch --quiet origin
        git -C "$mp_dir" reset --quiet --hard '@{u}'
    else
        log "cloning marketplace $mp_name from $mp_url"
        rm -rf "$mp_dir"
        git clone --quiet --depth 1 "$mp_url" "$mp_dir"
    fi
done

# --- 4. known_marketplaces.json ----------------------------------------------
log "writing known_marketplaces.json"
km_file="$PLUGINS_DIR/known_marketplaces.json"
[ -f "$km_file" ] || echo '{}' > "$km_file"

now=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
new_km=$(jq -n '{}')
for i in $(seq 0 $((mp_count - 1))); do
    mp_name=$(jq -r ".marketplaces[$i].name" "$manifest")
    mp_src=$(jq ".marketplaces[$i].source" "$manifest")
    new_km=$(jq --arg n "$mp_name" \
                --argjson src "$mp_src" \
                --arg loc "$MARKETPLACES_DIR/$mp_name" \
                --arg ts  "$now" \
                '. + { ($n): { source: $src, installLocation: $loc, lastUpdated: $ts } }' \
                <<<"$new_km")
done
jq -s '.[0] * .[1]' "$km_file" <(echo "$new_km") > "$km_file.tmp"
mv "$km_file.tmp" "$km_file"

# --- 5. enabled plugins → fetch entities + installed_plugins.json ------------
log "resolving enabled plugins"
ip_file="$PLUGINS_DIR/installed_plugins.json"
[ -f "$ip_file" ] || echo '{"version":2,"plugins":{}}' > "$ip_file"

new_plugins=$(jq -n '{}')
ep_count=$(jq '.enabled_plugins | length' "$manifest")
for i in $(seq 0 $((ep_count - 1))); do
    full=$(jq -r ".enabled_plugins[$i]" "$manifest")
    plugin_name="${full%@*}"
    mp_name="${full#*@}"
    mp_manifest="$MARKETPLACES_DIR/$mp_name/.claude-plugin/marketplace.json"
    [ -f "$mp_manifest" ] || { warn "marketplace manifest not found for $mp_name, skipping $plugin_name"; continue; }

    src=$(jq --arg n "$plugin_name" '.plugins[] | select(.name == $n) | .source' "$mp_manifest")
    if [ -z "$src" ] || [ "$src" = "null" ]; then
        warn "plugin $plugin_name not found in $mp_name marketplace, skipping"
        continue
    fi

    install_path=""
    if echo "$src" | jq -e 'type == "string"' >/dev/null; then
        # local subdir like "./plugins/<name>"
        rel=$(echo "$src" | jq -r '.')
        install_path="$MARKETPLACES_DIR/$mp_name/${rel#./}"
        log "  · $plugin_name (local in marketplace)"
    else
        src_type=$(echo "$src" | jq -r '.source')
        src_url=$(echo "$src" | jq -r '.url')
        src_ref=$(echo "$src" | jq -r '.ref // "main"')
        cache_path="$PLUGIN_CACHE_DIR/$mp_name/$plugin_name/unknown"
        case "$src_type" in
            git-subdir)
                src_subpath=$(echo "$src" | jq -r '.path')
                tmpdir=$(mktemp -d)
                if ! git clone --quiet --depth 1 --branch "$src_ref" "$src_url" "$tmpdir" 2>/dev/null; then
                    git clone --quiet "$src_url" "$tmpdir"
                    git -C "$tmpdir" checkout --quiet "$src_ref" 2>/dev/null || true
                fi
                rm -rf "$cache_path"
                mkdir -p "$(dirname "$cache_path")"
                cp -R "$tmpdir/$src_subpath" "$cache_path"
                rm -rf "$tmpdir"
                install_path="$cache_path"
                log "  · $plugin_name (git-subdir $src_url:$src_subpath)"
                ;;
            url|git)
                if [ -d "$cache_path/.git" ]; then
                    git -C "$cache_path" fetch --quiet origin
                    git -C "$cache_path" reset --quiet --hard '@{u}' 2>/dev/null || true
                else
                    rm -rf "$cache_path"
                    git clone --quiet --depth 1 "$src_url" "$cache_path" 2>/dev/null \
                        || git clone --quiet "$src_url" "$cache_path"
                fi
                install_path="$cache_path"
                log "  · $plugin_name (external $src_url)"
                ;;
            *)
                warn "unknown plugin source type '$src_type' for $plugin_name, skipping"
                continue
                ;;
        esac
    fi

    entry=$(jq -n --arg ip "$install_path" --arg ts "$now" \
                '[{ scope:"user", installPath:$ip, version:"unknown",
                    installedAt:$ts, lastUpdated:$ts }]')
    new_plugins=$(jq --arg k "$full" --argjson v "$entry" '. + { ($k): $v }' <<<"$new_plugins")
done

# merge into installed_plugins.json
jq --argjson new "$new_plugins" \
   '.version = 2 | .plugins = ((.plugins // {}) * $new)' \
   "$ip_file" > "$ip_file.tmp"
mv "$ip_file.tmp" "$ip_file"

# --- 6. settings.json merge --------------------------------------------------
log "merging settings.json"
settings_file="$CLAUDE_DIR/settings.json"
[ -f "$settings_file" ] || echo '{}' > "$settings_file"

# Expand $HOME literal in template
tmpl=$(jq --arg home "$HOME" '
  walk(if type == "string" then gsub("\\$HOME"; $home) else . end)
' "$REPO_DIR/settings.template.json")

jq -s '.[0] * .[1]' "$settings_file" <(echo "$tmpl") > "$settings_file.tmp"
mv "$settings_file.tmp" "$settings_file"

# --- 7. summary --------------------------------------------------------------
log "done."
echo
echo "Skills installed:"
ls -1 "$CLAUDE_DIR/skills/" | sed 's/^/  · /'
echo
echo "Plugins enabled:"
jq -r '.enabled_plugins[]' "$manifest" | sed 's/^/  · /'
echo
echo "⚠️  Restart Claude Code for plugin/skill changes to take full effect."
