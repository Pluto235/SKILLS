---
name: sync-codex-config
description: Safely snapshot the current Codex App skills, settings, and plugin inventory into the user's SKILLS repository, then review, commit, and push when explicitly requested.
---

# Sync Codex Config

Use `/Users/luoji/Documents/SKILLS` as the configuration repository.

## Workflow

1. Confirm the repository and remote, then update without discarding local changes:

   ```bash
   git -C /Users/luoji/Documents/SKILLS pull --rebase --autostash
   ```

2. Generate the safe Codex snapshot:

   ```bash
   bash /Users/luoji/Documents/SKILLS/sync-all.sh
   ```

3. Inspect `git status`, the diff summary, and all configuration/script changes. Run an additional secret scan before staging.

4. Run the restore dry-run and repository validation checks.

5. Commit and push only when the user explicitly requested the remote repository to be updated. Never force-push.

## Safety boundaries

- Never copy `~/.codex/auth.json`, OAuth data, API keys, sessions, history, caches, telemetry, or project trust entries.
- Do not export plugin authentication. Record only plugin identifiers and non-secret metadata.
- Preserve unrelated working-tree changes and include them only when they clearly belong to the requested configuration snapshot.
- Stop on merge conflicts or suspected secrets; do not auto-resolve or push them.
