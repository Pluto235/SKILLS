---
name: sync-agent-config
description: Use when the user asks to sync, back up, or push the current Claude Code and Codex configuration to the SKILLS repo. Runs sync-all.sh, checks for obvious secrets, shows the diff, and leaves commit/push for explicit user approval.
---

# sync-agent-config

Mirror the current safe Claude Code and Codex state back into the `SKILLS` git repo.

## When to use

Use when the user says any of:

- "sync my agent config"
- "同步 Codex 配置"
- "同步 Claude 和 Codex 配置"
- "push my skills/plugins to SKILLS"
- "back up my agent config to git"

## Workflow

1. Verify the repo exists:

   ```bash
   test -d "$HOME/Documents/SKILLS/.git" || test -d "$HOME/.claude/SKILLS/.git" || echo "MISSING"
   ```

2. Pull latest first from the chosen repo path:

   ```bash
   git -C "$REPO" pull --rebase --autostash
   ```

3. Run the safe snapshot:

   ```bash
   bash "$REPO/sync-all.sh"
   ```

4. Show the diff:

   ```bash
   git -C "$REPO" --no-pager diff --stat
   git -C "$REPO" --no-pager diff
   ```

5. Commit and push only after explicit user approval:

   ```bash
   git -C "$REPO" add -A
   git -C "$REPO" commit -m "sync agent config from $(hostname) on $(date -u +%Y-%m-%d)"
   git -C "$REPO" push
   ```

## Safety

- Never commit `~/.claude/settings.json` directly.
- Never commit `~/.codex/auth.json`, sessions, archived sessions, caches, telemetry, shell snapshots, or model caches.
- Never `git push --force`.
- If `sync-all.sh` reports a possible secret, stop and inspect before continuing.
