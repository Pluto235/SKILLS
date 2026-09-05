---
name: update-codex
description: Update Codex CLI on one or more remote SSH servers that cannot reach the internet. Use when the user says "update codex", "更新 codex", or asks to update Codex on SSH aliases such as ETO, PDC, or IHEP. The workflow downloads the latest package locally, transfers an offline Linux package through the local machine, replaces the remote user install, removes old versions and temp files, verifies the latest version, and reports completion.
---

# update-codex

Update remote Codex CLI installations when the remote server has no direct internet access.

## When to use

Use this skill when the user asks to update Codex on remote SSH servers, for example:

- `update codex on ETO`
- `ETO PDC 更新 codex`
- `update Codex`
- `把服务器上的 codex 更新一下`

If the user does not name a target server or SSH alias, inspect the immediate conversation context first. If the target is still ambiguous, ask a concise clarification before running anything.

## Workflow

1. Resolve the requested targets as SSH aliases or `user@host` values. Prefer aliases from `~/.ssh/config`.
2. Run the bundled script from the local machine:

```bash
bash /Users/luoji/.agents/skills/update-codex/scripts/update_codex.sh TARGET [TARGET...]
```

3. The script will:
   - query the latest `@openai/codex` version from npm locally
   - download the main package and the matching Linux platform package locally
   - build an offline prefix tarball locally
   - connect to each target with `ssh -o RemoteCommand=none -o BatchMode=yes`
   - transfer the tarball to `~/.codex/tmp/update-codex-VERSION`
   - replace the remote user-level `@openai/codex` package directory
   - preserve existing wrapper scripts and npm-style `bin/codex` symlinks
   - verify `codex --version` on the remote host
   - delete old backup directories, transfer tarballs, staging directories, and local temp files

## Commands

Update one host:

```bash
bash /Users/luoji/.agents/skills/update-codex/scripts/update_codex.sh ETO
```

Update multiple hosts:

```bash
bash /Users/luoji/.agents/skills/update-codex/scripts/update_codex.sh ETO PDC
```

Verify only, without modifying remote files:

```bash
bash /Users/luoji/.agents/skills/update-codex/scripts/update_codex.sh --verify-only ETO PDC
```

Pin a specific version instead of npm latest:

```bash
bash /Users/luoji/.agents/skills/update-codex/scripts/update_codex.sh --version 0.144.1 ETO
```

## Operating Rules

- Do not run `npm install` on the remote host. The remote host may not have internet access.
- Do not remove `~/.codex`, auth files, sessions, logs, or config files.
- Do not edit the user's SSH config unless explicitly asked.
- Preserve remote wrapper scripts such as `~/.local/bin/codex`; update the package directory they point to.
- Treat a failed verification as a failed update. The script attempts rollback before exiting non-zero.
- After running, report target, hostname, active `codex` path, final version, and cleanup status.

## Resource

`scripts/update_codex.sh` is the source of truth for the transfer, replacement, verification, rollback, and cleanup behavior.
