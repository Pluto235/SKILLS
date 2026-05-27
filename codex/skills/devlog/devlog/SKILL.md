---
name: devlog
description: >-
  Maintain a lightweight `devlog.md` modification log at the git project root.
  Auto-invoke after meaningful code changes in repos that already track
  `devlog.md`, or when the user explicitly asks to update devlog. Bootstraps a
  new `devlog.md` from recent commits when requested.
---

# devlog — modification log convention

You maintain a `devlog.md` file at the git project root. Each entry is a
single Markdown bullet capturing one logical change. The devlog is a
scan-friendly index — detailed design rationale belongs in `docs/`, and
authoritative history is `git log`.

## When to invoke

**Auto-invoke** (no need to ask the user) when ALL of these hold:
- The current working directory is inside a git repository, AND
- Either `devlog.md` already exists at `git rev-parse --show-toplevel`,
  OR the user explicitly asked you to start tracking with `/devlog`, AND
- A meaningful modification just happened — typically a `git commit` you
  authored, or a coherent edit session you just finished.

**Manual invocation**: user types `/devlog [optional summary]`. If they
pass a summary, use it verbatim; otherwise derive one from the latest
commit message or the edits you just performed.

**Do NOT** auto-invoke for:
- Read-only exploration sessions (Read / Grep / Bash inspection only).
- Skill or memory-system meta-changes (the user manages those separately).
- Repos where `devlog.md` is absent AND the user hasn't asked you to
  bootstrap. In that case, ASK before creating it.

## Entry format (exact)

```
- **<version>** · YYYY-MM-DD HH:MM · [<short-sha-or-uncommitted>] <one-line summary>
```

- `<version>`: see "Version detection" below.
- Timestamp: local time, 24-hour. Use `date '+%Y-%m-%d %H:%M'`.
- `<short-sha>`: 7-char abbreviated commit hash from `git rev-parse --short HEAD`
  after the commit you just made. If the modification is uncommitted,
  use the literal `[uncommitted]`.
- Summary: one line, present tense, concise but specific (mention key
  files changed or capability added — not just "fix bug").
- **Newest at top.** New entries are prepended below the header, never appended.

Example entries (do not include in output verbatim — these are reference):

```
- **v4.1** · 2026-05-16 09:15 · [41e160c] Add devlog skill that auto-maintains devlog.md across projects.
- **v4.1** · 2026-05-16 08:35 · [5aee816] Phase 4 — config_advisor preflight subagent + qe_input_lint Rule C/D.
- **main** · 2026-05-14 11:02 · [a1b2c3d] Bump fastapi to 0.136.0 for solver_wrapper compatibility.
```

## Version detection

In priority order:

1. **Git branch** via `git --no-optional-locks branch --show-current`,
   IFF it looks version-like. Treat as version-like any branch whose
   name matches `^v\d` (e.g. `v4`, `v4.1`, `v5.2`) OR matches
   `^[0-9]` (e.g. `2.0`, `0.9.1`). Use the branch name verbatim.
2. Otherwise fall back to the **directory name** of the git root
   (`basename "$(git rev-parse --show-toplevel)"`).
3. If neither yields anything reasonable (rare — empty repo, detached
   HEAD with no branch), use `unknown`.

Concrete examples:
- branch `v4.1` → version `v4.1`
- branch `dev` → directory name `solver/v4.1` → version `v4.1`
- branch `main` in `~/projects/web/` → version `web`
- branch `feat/foo` in `~/projects/dft-bench/` → version `dft-bench`

## Bootstrap (devlog.md missing)

When invoked and `devlog.md` does not exist at the git root:

1. Confirm the user wants this if they didn't explicitly type `/devlog`
   (skip the confirmation when they did).
2. Create `devlog.md` at the git root with this header:
   ```markdown
   # <version> devlog

   Lightweight running log of Claude-mediated modifications.
   Newest at top. Format: `- **<version>** · YYYY-MM-DD HH:MM · [<sha>] <summary>`.
   Detailed design rationale → `docs/`. Authoritative history → `git log`.

   ---

   ```
3. Backfill the last **10 commits** (or all commits if fewer than 10) using:
   ```bash
   git log -10 --format='%h %ad§%s' --date=format:'%Y-%m-%d %H:%M'
   ```
   For each row, emit an entry. Use the first line of each commit's
   subject as the summary; truncate at ~120 chars if needed.
4. Append the entry for the current change at the top, as usual.
5. **Commit the bootstrap separately** with message
   `chore(<version>): add devlog.md (auto-backfilled from git log)` —
   so the bootstrap doesn't get tangled with the user's substantive
   change. Then proceed to commit / log the actual change.

## Updating `CLAUDE.md` (optional)

If the project already has a `CLAUDE.md` and the user is using this
skill globally (i.e., it lives in `~/.claude/skills/`), the per-repo
"Modification log convention" section is redundant. Do NOT trim it
without asking — some users want explicit per-repo notes. If asked
to clean up, replace it with one line:

```markdown
## Modification log

This repo uses the global `/devlog` skill — see `devlog.md`.
```

## Process flow

```
Did a modification just happen?
  └─ Yes → cwd inside a git repo?
            └─ Yes → devlog.md exists at git root?
                       ├─ Yes → derive version → append entry at top → done
                       └─ No  → user explicitly asked for /devlog?
                                  ├─ Yes → bootstrap then append → done
                                  └─ No  → silently skip (no devlog opt-in)
            └─ No  → silently skip (not a git repo)
  └─ No  → not applicable
```

## Step-by-step write recipe

```bash
# 1. Locate root
ROOT=$(git rev-parse --show-toplevel)
DEVLOG="$ROOT/devlog.md"

# 2. Derive version
BRANCH=$(git --no-optional-locks branch --show-current)
if [[ "$BRANCH" =~ ^(v[0-9]|[0-9]) ]]; then
    VERSION="$BRANCH"
else
    VERSION=$(basename "$ROOT")
fi

# 3. Get timestamp + sha
TS=$(date '+%Y-%m-%d %H:%M')
SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "uncommitted")
# Use [uncommitted] if there are unstaged/uncommitted edits relevant to
# this change, OR if no commits exist yet.
```

Then use the `Edit` tool to prepend the new bullet **after** the `---`
separator near the top of `devlog.md`. Do NOT just append at end of file
(format requires reverse-chronological).

## Failure modes to handle gracefully

- Not in a git repo: silently no-op (don't error).
- `devlog.md` exists but has malformed structure (no `---` separator,
  no header): prepend after first blank line; warn user briefly.
- Multiple modifications in one session: write ONE entry summarizing
  them all, unless they are clearly distinct logical changes (then
  one per commit makes sense).
- Bootstrap in a repo with > 200 commits: still backfill only 10. The
  devlog is for forward-going tracking, not full history archive.

## What NOT to do

- Don't write multi-line entries. One bullet, one line.
- Don't include emojis (the user can add them post-hoc if desired).
- Don't include file lists in the summary — that's what `git show` is for.
- Don't reword the user's manual `/devlog <summary>` text; preserve it.
- Don't trigger on read-only sessions where no files were modified.
