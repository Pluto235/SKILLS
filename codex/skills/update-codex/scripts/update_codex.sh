#!/usr/bin/env bash
set -euo pipefail

SCRIPT_NAME="$(basename "$0")"
VERSION="latest"
VERIFY_ONLY=0
KEEP_TEMP=0
SSH_CONNECT_TIMEOUT="${SSH_CONNECT_TIMEOUT:-10}"
TARGETS=()

usage() {
  cat <<USAGE
Usage:
  $SCRIPT_NAME [--version VERSION] [--verify-only] [--keep-temp] TARGET [TARGET...]

Examples:
  $SCRIPT_NAME ETO
  $SCRIPT_NAME ETO PDC
  $SCRIPT_NAME --verify-only ETO PDC
  $SCRIPT_NAME --version 0.144.1 ETO
USAGE
}

log() {
  printf '[update-codex] %s\n' "$*" >&2
}

die() {
  printf '[update-codex] ERROR: %s\n' "$*" >&2
  exit 1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

sha256_file() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | cut -d' ' -f1
  else
    shasum -a 256 "$1" | cut -d' ' -f1
  fi
}

parse_args() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --version)
        [ "$#" -ge 2 ] || die "--version requires a value"
        VERSION="$2"
        shift 2
        ;;
      --verify-only)
        VERIFY_ONLY=1
        shift
        ;;
      --keep-temp)
        KEEP_TEMP=1
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      --)
        shift
        while [ "$#" -gt 0 ]; do
          TARGETS+=("$1")
          shift
        done
        ;;
      -*)
        die "unknown option: $1"
        ;;
      *)
        TARGETS+=("$1")
        shift
        ;;
    esac
  done

  [ "${#TARGETS[@]}" -gt 0 ] || {
    usage >&2
    exit 2
  }
}

ssh_base() {
  ssh \
    -o BatchMode=yes \
    -o RemoteCommand=none \
    -o ConnectTimeout="$SSH_CONNECT_TIMEOUT" \
    "$@"
}

scp_base() {
  scp \
    -o BatchMode=yes \
    -o RemoteCommand=none \
    -o ConnectTimeout="$SSH_CONNECT_TIMEOUT" \
    "$@"
}

resolve_latest_version() {
  if [ "$VERSION" = "latest" ]; then
    need_cmd npm
    VERSION="$(npm view @openai/codex version)"
  fi
  [ -n "$VERSION" ] || die "failed to resolve Codex version"
  log "target Codex version: $VERSION"
}

platform_suffix() {
  case "$1:$2" in
    Linux:x86_64|Linux:amd64)
      printf 'linux-x64'
      ;;
    Linux:aarch64|Linux:arm64)
      printf 'linux-arm64'
      ;;
    *)
      die "unsupported remote platform: $1 $2"
      ;;
  esac
}

LOCAL_TMP=""

cleanup_local_tmp() {
  if [ "$KEEP_TEMP" -eq 0 ] && [ -n "${LOCAL_TMP:-}" ] && [ -d "$LOCAL_TMP" ]; then
    rm -rf "$LOCAL_TMP"
  fi
}

build_bundle() {
  platform="$1"
  need_cmd npm
  need_cmd node
  need_cmd tar

  build_dir="$LOCAL_TMP/build-$platform"
  bundle="$build_dir/codex-$platform-prefix-$VERSION.tgz"
  sha_file="$build_dir/$platform.sha256"

  if [ -f "$bundle" ] && [ -f "$sha_file" ]; then
    printf '%s %s\n' "$bundle" "$(cat "$sha_file")"
    return 0
  fi

  log "building offline package for $platform"
  rm -rf "$build_dir"
  mkdir -p "$build_dir/stage/lib/node_modules/@openai/codex"
  mkdir -p "$build_dir/stage/lib/node_modules/@openai/codex/node_modules/@openai/codex-$platform"
  mkdir -p "$build_dir/stage/bin"

  (
    cd "$build_dir"
    npm pack "@openai/codex@$VERSION" --json >/dev/null
    npm pack "@openai/codex@$VERSION-$platform" --json >/dev/null

    main_tgz="openai-codex-$VERSION.tgz"
    platform_tgz="openai-codex-$VERSION-$platform.tgz"
    [ -f "$main_tgz" ] || die "missing npm pack output: $main_tgz"
    [ -f "$platform_tgz" ] || die "missing npm pack output: $platform_tgz"

    tar -xzf "$main_tgz" -C stage/lib/node_modules/@openai/codex --strip-components=1
    tar -xzf "$platform_tgz" -C "stage/lib/node_modules/@openai/codex/node_modules/@openai/codex-$platform" --strip-components=1
    ln -s ../lib/node_modules/@openai/codex/bin/codex.js stage/bin/codex

    node -e '
const base = process.argv[1];
const version = process.argv[2];
const platform = process.argv[3];
const main = require(`${base}/stage/lib/node_modules/@openai/codex/package.json`);
const plat = require(`${base}/stage/lib/node_modules/@openai/codex/node_modules/@openai/codex-${platform}/package.json`);
if (main.version !== version) throw new Error(`main version mismatch: ${main.version}`);
if (plat.version !== `${version}-${platform}`) throw new Error(`platform version mismatch: ${plat.version}`);
' "$build_dir" "$VERSION" "$platform"

    xattr -cr stage 2>/dev/null || true
    COPYFILE_DISABLE=1 tar -C stage -czf "$bundle" .
  )

  sha="$(sha256_file "$bundle")"
  printf '%s\n' "$sha" > "$sha_file"
  printf '%s %s\n' "$bundle" "$sha"
}

probe_target() {
  target="$1"
  ssh_base "$target" 'bash -s' <<'REMOTE'
user_name="$(id -un 2>/dev/null || printf '')"
effective_home="$HOME"
for candidate in "$HOME" "/home/lhaaso/$user_name" "/home/$user_name"; do
  [ -n "$candidate" ] || continue
  if [ -f "$candidate/.local/codex-cli/lib/node_modules/@openai/codex/package.json" ] ||
     [ -f "$candidate/.local/opt/npm-global/lib/node_modules/@openai/codex/package.json" ] ||
     find "$candidate/.nvm/versions" -maxdepth 8 -path '*/lib/node_modules/@openai/codex/package.json' -print -quit 2>/dev/null | grep -q .; then
    effective_home="$candidate"
    break
  fi
done
printf '__UPDATE_CODEX_PROBE_BEGIN__\n'
printf 'HOME=%s\n' "$HOME"
printf 'EFFECTIVE_HOME=%s\n' "$effective_home"
printf 'HOSTNAME=%s\n' "$(hostname 2>/dev/null || printf unknown)"
printf 'UNAME_S=%s\n' "$(uname -s)"
printf 'UNAME_M=%s\n' "$(uname -m)"
printf '__UPDATE_CODEX_PROBE_END__\n'
REMOTE
}

extract_probe_value() {
  key="$1"
  sed -n '/__UPDATE_CODEX_PROBE_BEGIN__/,/__UPDATE_CODEX_PROBE_END__/p' |
    sed -n "s/^$key=//p" |
    tail -n 1
}

remote_verify() {
  target="$1"
  version="$2"
  remote_home="$3"
  ssh_base "$target" 'bash -s' -- "$version" "$remote_home" <<'REMOTE'
set -euo pipefail
VERSION="$1"
EFFECTIVE_HOME="$2"
export HOME="$EFFECTIVE_HOME"

find_package_jsons() {
  for p in \
    "$HOME/.local/opt/npm-global/lib/node_modules/@openai/codex/package.json" \
    "$HOME/.local/codex-cli/lib/node_modules/@openai/codex/package.json"
  do
    [ -f "$p" ] && printf '%s\n' "$p"
  done

  for base in "$HOME/.nvm/versions" "$HOME/.local/node" "$HOME/.local/opt"; do
    [ -d "$base" ] || continue
    find "$base" -maxdepth 8 -path '*/lib/node_modules/@openai/codex/package.json' -print 2>/dev/null
  done
}

node_bin_for_prefix() {
  prefix="$1"
  for n in \
    "$prefix/bin/node" \
    "$HOME/.local/node/bin/node" \
    "$HOME/.local/node-current/bin/node" \
    "$HOME/.local/opt/node-current/bin/node"
  do
    [ -x "$n" ] && { dirname "$n"; return 0; }
  done

  if [ -d "$HOME/.nvm/versions" ]; then
    found="$(find "$HOME/.nvm/versions" -maxdepth 4 -path '*/bin/node' -type f -perm -111 -print 2>/dev/null | sort -Vr | head -n 1 || true)"
    [ -n "$found" ] && { dirname "$found"; return 0; }
  fi

  if command -v node >/dev/null 2>&1; then
    dirname "$(command -v node)"
    return 0
  fi

  return 1
}

mapfile_fallback() {
  tmp_file="$1"
  while IFS= read -r line; do
    [ -n "$line" ] && printf '%s\n' "$line"
  done < "$tmp_file"
}

tmp_list="$(mktemp)"
find_package_jsons | sort -u > "$tmp_list"
if [ ! -s "$tmp_list" ]; then
  rm -f "$tmp_list"
  echo "no user-level Codex package roots found" >&2
  exit 1
fi

status=0
printf 'hostname=%s\n' "$(hostname 2>/dev/null || printf unknown)"
printf 'package_roots:\n'
while IFS= read -r pkg_json; do
  prefix="${pkg_json%/lib/node_modules/@openai/codex/package.json}"
  package_dir="$prefix/lib/node_modules/@openai/codex"
  node_dir="$(node_bin_for_prefix "$prefix" || true)"
  if [ -z "$node_dir" ]; then
    printf '  %s node=MISSING\n' "$package_dir"
    status=1
    continue
  fi
  main_version="$("$node_dir/node" -e 'console.log(require(process.argv[1]).version)' "$pkg_json")"
  platform_json="$package_dir/node_modules/@openai/codex-linux-x64/package.json"
  [ -f "$platform_json" ] || platform_json="$package_dir/node_modules/@openai/codex-linux-arm64/package.json"
  platform_version="MISSING"
  if [ -f "$platform_json" ]; then
    platform_version="$("$node_dir/node" -e 'console.log(require(process.argv[1]).version)' "$platform_json")"
  fi
  printf '  %s main=%s platform=%s\n' "$package_dir" "$main_version" "$platform_version"
  [ "$main_version" = "$VERSION" ] || status=1
  case "$platform_version" in
    "$VERSION"-linux-*) ;;
    *) status=1 ;;
  esac
done < "$tmp_list"
rm -f "$tmp_list"

printf 'active_codex:\n'
first_pkg="$(find_package_jsons | sort -u | head -n 1 || true)"
if [ -n "$first_pkg" ]; then
  first_prefix="${first_pkg%/lib/node_modules/@openai/codex/package.json}"
  first_node_dir="$(node_bin_for_prefix "$first_prefix" || true)"
  if [ -n "$first_node_dir" ] && PATH="$first_node_dir:$HOME/.local/bin:$first_prefix/bin:$PATH" command -v codex >/dev/null 2>&1; then
    PATH="$first_node_dir:$HOME/.local/bin:$first_prefix/bin:$PATH" command -v codex | sed 's/^/  /'
    active_version="$(PATH="$first_node_dir:$HOME/.local/bin:$first_prefix/bin:$PATH" codex --version 2>/dev/null || true)"
    printf '  %s\n' "$active_version"
    printf '%s\n' "$active_version" | grep -q "codex-cli $VERSION" || status=1
  else
    printf '  MISSING\n'
    status=1
  fi
else
  printf '  MISSING\n'
  status=1
fi

printf 'residuals:\n'
find "$HOME/.local" "$HOME/.nvm" "$HOME/.codex/tmp" -maxdepth 8 \
  \( -name 'codex.old.*' -o -name 'update-codex-*' -o -name 'codex-*-prefix-*.tgz' \) \
  -print 2>/dev/null | sort | sed 's/^/  /' || true

exit "$status"
REMOTE
}

remote_install() {
  target="$1"
  version="$2"
  bundle="$3"
  expected_sha="$4"
  remote_home="$5"

  bundle_name="$(basename "$bundle")"
  remote_tmp="$remote_home/.codex/tmp/update-codex-$version"
  remote_bundle="$remote_tmp/$bundle_name"

  log "$target: preparing remote temp dir"
  ssh_base "$target" "mkdir -p '$remote_tmp' && rm -f '$remote_tmp'/*.tgz"

  log "$target: transferring $bundle_name"
  scp_base "$bundle" "$target:$remote_bundle" >/dev/null

  log "$target: installing and verifying"
  ssh_base "$target" 'bash -s' -- "$version" "$expected_sha" "$remote_bundle" "$remote_home" <<'REMOTE'
set -euo pipefail
VERSION="$1"
EXPECTED_SHA="$2"
BUNDLE="$3"
EFFECTIVE_HOME="$4"
export HOME="$EFFECTIVE_HOME"
REMOTE_TMP="$(dirname "$BUNDLE")"
STAGE="$REMOTE_TMP/stage"

sha_actual="$(sha256sum "$BUNDLE" | cut -d' ' -f1)"
if [ "$sha_actual" != "$EXPECTED_SHA" ]; then
  echo "sha256 mismatch: $sha_actual" >&2
  exit 1
fi

find_package_jsons() {
  for p in \
    "$HOME/.local/opt/npm-global/lib/node_modules/@openai/codex/package.json" \
    "$HOME/.local/codex-cli/lib/node_modules/@openai/codex/package.json"
  do
    [ -f "$p" ] && printf '%s\n' "$p"
  done

  for base in "$HOME/.nvm/versions" "$HOME/.local/node" "$HOME/.local/opt"; do
    [ -d "$base" ] || continue
    find "$base" -maxdepth 8 -path '*/lib/node_modules/@openai/codex/package.json' -print 2>/dev/null
  done
}

node_bin_for_prefix() {
  prefix="$1"
  for n in \
    "$prefix/bin/node" \
    "$HOME/.local/node/bin/node" \
    "$HOME/.local/node-current/bin/node" \
    "$HOME/.local/opt/node-current/bin/node"
  do
    [ -x "$n" ] && { dirname "$n"; return 0; }
  done

  if [ -d "$HOME/.nvm/versions" ]; then
    found="$(find "$HOME/.nvm/versions" -maxdepth 4 -path '*/bin/node' -type f -perm -111 -print 2>/dev/null | sort -Vr | head -n 1 || true)"
    [ -n "$found" ] && { dirname "$found"; return 0; }
  fi

  if command -v node >/dev/null 2>&1; then
    dirname "$(command -v node)"
    return 0
  fi

  return 1
}

verify_prefix() {
  prefix="$1"
  node_dir="$2"
  PATH="$node_dir:$prefix/bin:$HOME/.local/bin:$PATH" "$prefix/bin/codex" --version | grep -q "codex-cli $VERSION"
}

tmp_list="$(mktemp)"
find_package_jsons | sort -u > "$tmp_list"
if [ ! -s "$tmp_list" ]; then
  rm -f "$tmp_list"
  echo "no existing user-level Codex package roots found; refusing to create a new install automatically" >&2
  exit 1
fi

rm -rf "$STAGE"
mkdir -p "$STAGE"
tar -xzf "$BUNDLE" -C "$STAGE"

first_prefix="$(head -n 1 "$tmp_list")"
first_prefix="${first_prefix%/lib/node_modules/@openai/codex/package.json}"
first_node_dir="$(node_bin_for_prefix "$first_prefix" || true)"
if [ -z "$first_node_dir" ]; then
  rm -f "$tmp_list"
  echo "could not find a usable node binary" >&2
  exit 1
fi

"$first_node_dir/node" -e '
const base = process.argv[1];
const version = process.argv[2];
const main = require(`${base}/lib/node_modules/@openai/codex/package.json`);
const roots = ["codex-linux-x64", "codex-linux-arm64"];
let platform = null;
for (const name of roots) {
  try {
    platform = require(`${base}/lib/node_modules/@openai/codex/node_modules/@openai/${name}/package.json`);
    break;
  } catch {}
}
if (main.version !== version) throw new Error(`main version mismatch: ${main.version}`);
if (!platform || !platform.version.startsWith(`${version}-linux-`)) {
  throw new Error(`platform package mismatch: ${platform && platform.version}`);
}
' "$STAGE" "$VERSION"

PATH="$first_node_dir:$STAGE/bin:$PATH" "$STAGE/bin/codex" --version | grep -q "codex-cli $VERSION"

while IFS= read -r pkg_json; do
  prefix="${pkg_json%/lib/node_modules/@openai/codex/package.json}"
  parent="$prefix/lib/node_modules/@openai"
  package_dir="$parent/codex"
  backup="$parent/codex.old.$(date +%Y%m%d%H%M%S)"
  node_dir="$(node_bin_for_prefix "$prefix" || true)"
  if [ -z "$node_dir" ]; then
    echo "no usable node for prefix: $prefix" >&2
    exit 1
  fi

  mkdir -p "$parent" "$prefix/bin"
  if [ -e "$package_dir" ]; then
    mv "$package_dir" "$backup"
  fi

  if ! cp -a "$STAGE/lib/node_modules/@openai/codex" "$package_dir"; then
    rm -rf "$package_dir"
    [ -e "$backup" ] && mv "$backup" "$package_dir"
    exit 1
  fi
  ln -sfn ../lib/node_modules/@openai/codex/bin/codex.js "$prefix/bin/codex"

  if ! verify_prefix "$prefix" "$node_dir"; then
    echo "verification failed for prefix: $prefix; rolling back" >&2
    rm -rf "$package_dir"
    [ -e "$backup" ] && mv "$backup" "$package_dir"
    ln -sfn ../lib/node_modules/@openai/codex/bin/codex.js "$prefix/bin/codex"
    exit 1
  fi

  rm -rf "$backup"
done < "$tmp_list"
rm -f "$tmp_list"

find "$HOME/.local" "$HOME/.nvm" -maxdepth 8 -name 'codex.old.*' -type d -prune -exec rm -rf {} + 2>/dev/null || true
rm -rf "$HOME/.codex/tmp/arg0"/codex-arg0* 2>/dev/null || true
rm -rf "$REMOTE_TMP"

printf 'hostname=%s\n' "$(hostname 2>/dev/null || printf unknown)"
printf 'active_codex:\n'
first_pkg="$(find_package_jsons | sort -u | head -n 1 || true)"
if [ -n "$first_pkg" ]; then
  first_prefix="${first_pkg%/lib/node_modules/@openai/codex/package.json}"
  first_node_dir="$(node_bin_for_prefix "$first_prefix" || true)"
  if [ -n "$first_node_dir" ]; then
    PATH="$first_node_dir:$HOME/.local/bin:$first_prefix/bin:$PATH" command -v codex 2>/dev/null | sed 's/^/  /' || true
    PATH="$first_node_dir:$HOME/.local/bin:$first_prefix/bin:$PATH" codex --version 2>/dev/null | sed 's/^/  /' || true
  fi
fi
printf 'package_roots:\n'
find_package_jsons | sort -u | while IFS= read -r pkg_json; do
  prefix="${pkg_json%/lib/node_modules/@openai/codex/package.json}"
  node_dir="$(node_bin_for_prefix "$prefix" || true)"
  main_version="$("$node_dir/node" -e 'console.log(require(process.argv[1]).version)' "$pkg_json")"
  package_dir="$prefix/lib/node_modules/@openai/codex"
  platform_json="$package_dir/node_modules/@openai/codex-linux-x64/package.json"
  [ -f "$platform_json" ] || platform_json="$package_dir/node_modules/@openai/codex-linux-arm64/package.json"
  platform_version="$("$node_dir/node" -e 'console.log(require(process.argv[1]).version)' "$platform_json")"
  printf '  %s main=%s platform=%s\n' "$package_dir" "$main_version" "$platform_version"
done
REMOTE
}

main() {
  parse_args "$@"
  need_cmd ssh
  need_cmd scp
  need_cmd sed

  resolve_latest_version

  if [ "$VERIFY_ONLY" -eq 0 ]; then
    LOCAL_TMP="$(mktemp -d /tmp/update-codex.XXXXXX)"
    trap cleanup_local_tmp EXIT
  fi

  failures=0
  for target in "${TARGETS[@]}"; do
    log "$target: probing"
    probe="$(probe_target "$target")" || {
      printf '%s\n' "$probe" >&2 || true
      log "$target: probe failed"
      failures=$((failures + 1))
      continue
    }

    remote_home="$(printf '%s\n' "$probe" | extract_probe_value EFFECTIVE_HOME)"
    [ -n "$remote_home" ] || remote_home="$(printf '%s\n' "$probe" | extract_probe_value HOME)"
    remote_host="$(printf '%s\n' "$probe" | extract_probe_value HOSTNAME)"
    uname_s="$(printf '%s\n' "$probe" | extract_probe_value UNAME_S)"
    uname_m="$(printf '%s\n' "$probe" | extract_probe_value UNAME_M)"
    [ -n "$remote_home" ] || {
      log "$target: could not parse remote HOME"
      failures=$((failures + 1))
      continue
    }
    log "$target: $remote_host $uname_s $uname_m home=$remote_home"

    if [ "$VERIFY_ONLY" -eq 1 ]; then
      if remote_verify "$target" "$VERSION" "$remote_home"; then
        log "$target: verify-only passed"
      else
        log "$target: verify-only failed"
        failures=$((failures + 1))
      fi
      continue
    fi

    platform="$(platform_suffix "$uname_s" "$uname_m")"
    bundle_info="$(build_bundle "$platform")"
    bundle="$(printf '%s\n' "$bundle_info" | tail -n 1 | awk '{print $1}')"
    bundle_sha="$(printf '%s\n' "$bundle_info" | tail -n 1 | awk '{print $2}')"

    if remote_install "$target" "$VERSION" "$bundle" "$bundle_sha" "$remote_home"; then
      log "$target: update completed"
    else
      log "$target: update failed"
      failures=$((failures + 1))
    fi
  done

  if [ "$failures" -gt 0 ]; then
    die "$failures target(s) failed"
  fi

  log "all targets completed"
}

main "$@"
