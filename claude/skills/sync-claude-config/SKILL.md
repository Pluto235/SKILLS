---
name: sync-claude-config
description: Use when the user asks to "sync my Claude config", "同步 Claude 配置", "push my skills/plugins to the SKILLS repo", or any variant about pushing the current ~/.claude state back to the dotfiles repo at ~/.claude/SKILLS. Runs sync.sh, shows the diff, gets confirmation, then commits and pushes.
---

# sync-claude-config

Mirrors the current `~/.claude/` state back into the `~/.claude/SKILLS/` git repo and pushes upstream.

## When to use

User says any of:
- "sync my Claude config"
- "同步 Claude 配置" / "同步一下 skills" / "推到 SKILLS 仓库"
- "push my skills to SKILLS"
- "back up Claude config to git"

## What to do

1. **Verify the repo is cloned**:
   ```bash
   test -d "$HOME/.claude/SKILLS/.git" || echo "MISSING"
   ```
   If missing, tell the user to clone it first:
   `git clone git@github.com:Pluto235/SKILLS.git ~/.claude/SKILLS`

2. **Pull latest first** to avoid push conflicts:
   ```bash
   git -C "$HOME/.claude/SKILLS" pull --rebase --autostash
   ```

3. **Run the snapshot script**:
   ```bash
   bash "$HOME/.claude/SKILLS/sync.sh"
   ```
   This rewrites `skills/`, `manifest.json`, `settings.template.json`, `statusline-command.sh`.

4. **Show the diff** and let the user confirm:
   ```bash
   cd "$HOME/.claude/SKILLS" && git --no-pager diff --stat && git --no-pager diff
   ```

5. **If the user approves**, commit and push:
   ```bash
   cd "$HOME/.claude/SKILLS"
   git add -A
   git commit -m "sync from $(hostname) on $(date -u +%Y-%m-%d)"
   git push
   ```

## Safety

- Never `git push --force` here.
- If `git pull --rebase` shows a conflict, stop and ask the user — do not auto-resolve.
- Do not commit `.credentials.json`, `history.jsonl`, `sessions/`, or anything from `~/.claude/projects/`. The `sync.sh` script intentionally only touches the managed paths; if you find yourself reaching outside those, something is wrong.
