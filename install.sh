#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${CODEX_HOME:-$HOME/.codex}/skills"

WITH_PUA=0
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: bash install.sh [--with-pua] [--all] [--dry-run]

Installs the core Codex skills in ./skills to ~/.codex/skills.

Options:
  --with-pua     Also install optional/pua-debugging/*
  --all          Install core skills plus optional pua-debugging skills
  --dry-run      Print actions without copying files
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-pua)
      WITH_PUA=1
      ;;
    --all)
      WITH_PUA=1
      ;;
    --dry-run)
      DRY_RUN=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

copy_dir() {
  local src="$1"
  local dst="$2"
  if [[ ! -d "$src" ]]; then
    return
  fi
  echo "Install $(basename "$src") -> $dst"
  if [[ "$DRY_RUN" -eq 0 ]]; then
    mkdir -p "$dst"
    rm -rf "$dst/$(basename "$src")"
    cp -R "$src" "$dst/"
  fi
}

install_group() {
  local dir="$1"
  if [[ ! -d "$dir" ]]; then
    return
  fi
  for skill in "$dir"/*; do
    [[ -d "$skill" ]] || continue
    [[ -f "$skill/SKILL.md" ]] || continue
    copy_dir "$skill" "$DEST"
  done
}

echo "Destination: $DEST"
install_group "$ROOT/skills"

if [[ "$WITH_PUA" -eq 1 ]]; then
  install_group "$ROOT/optional/pua-debugging"
fi

if [[ "$DRY_RUN" -eq 0 ]]; then
  echo "Done. Restart Codex to load newly installed skills."
else
  echo "Dry run complete."
fi
