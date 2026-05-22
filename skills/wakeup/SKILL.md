---
name: wakeup
description: Use when the user invokes `/wakeup` (optionally with a window arg like `48h`, `12h`, `2d`, or `since 2026-05-20`). Produces a cross-project recap of Claude Code activity in a rolling time window (default last 24h): a 2-4 paragraph TL;DR prose summary followed by per-project session cards with intent, tool counts, and in-window git commits. The full report is printed to the conversation AND archived to `~/.claude/wakeup/<YYYY-MM-DD-HHMM>.md`. Triggers: `/wakeup`, `/wakeup Nh`, `/wakeup Nd`, `/wakeup since YYYY-MM-DD`. Also natural language: "睡醒看看昨天做了啥", "what did I do yesterday", "morning recap".
---

# wakeup — cross-project morning recap

You scan Claude Code's local transcripts across **all** projects under
`~/.claude/projects/`, summarize activity in a rolling time window, and
emit a markdown report with a prose TL;DR followed by structured per-project
cards.

## When to invoke

User types `/wakeup [arg]`. `arg` is optional:

| arg                          | meaning                                          |
|------------------------------|--------------------------------------------------|
| (none)                       | last 24h                                         |
| `Nh` (e.g. `12h`, `48h`)     | last N hours                                     |
| `Nd` (e.g. `2d`, `7d`)       | last N days                                      |
| `since YYYY-MM-DD`           | from given date 00:00 local time → now           |

Also fire on natural-language equivalents in the trigger description.

## Pipeline

### 1. Parse the window arg → UTC ISO cutoff

In a single bash block, compute `SINCE_ISO` (UTC, ISO 8601, trailing `Z`):

```bash
ARG="${1:-24h}"   # the slash-command arg
case "$ARG" in
  *h) HOURS="${ARG%h}"; SINCE_ISO=$(date -u -d "$HOURS hours ago" '+%Y-%m-%dT%H:%M:%SZ') ;;
  *d) DAYS="${ARG%d}";  SINCE_ISO=$(date -u -d "$DAYS days ago"   '+%Y-%m-%dT%H:%M:%SZ') ;;
  since\ *) DATE="${ARG#since }"; SINCE_ISO=$(date -u -d "$DATE 00:00:00" '+%Y-%m-%dT%H:%M:%SZ') ;;
  *) SINCE_ISO=$(date -u -d "24 hours ago" '+%Y-%m-%dT%H:%M:%SZ') ;;
esac
```

Also capture `WINDOW_LABEL` (e.g. `last 24h`, `last 48h`, `since 2026-05-20`)
for the report header, and `GENERATED_AT_LOCAL` from `date '+%Y-%m-%d %H:%M %Z'`.

### 2. Run extract.py to get per-session JSON

```bash
python3 ~/.claude/skills/wakeup/extract.py --since "$SINCE_ISO"
```

The script outputs a JSON document with a `sessions` array. Each session
has: `session_id`, `jsonl_path`, `cwd`, `git_branch`, `slug`, `ts_first`,
`ts_last`, `first_user_msg` (already truncated to 240 chars),
`tool_counts`, `event_count`, `user_msg_count`. Sessions are pre-sorted
by `(cwd, ts_first)`.

Capture the JSON to a variable (e.g. via Bash with output redirection
to a temp file, then Read it). Don't try to inline-eval thousands of
bytes of JSON — read it as a file.

### 3. Empty-window short-circuit

If `sessions == []`, **also** run `git log --since` across the cwds you
know the user uses. If still nothing, print one line:

```
No Claude Code activity in last <WINDOW_LABEL>.
```

Do NOT write an archive file in this case.

### 4. Pull git commits per unique cwd

For each unique `cwd` in `sessions`:

```bash
if [ -d "$cwd/.git" ] || git -C "$cwd" rev-parse --git-dir >/dev/null 2>&1; then
    git -C "$cwd" log --since="$SINCE_ISO" \
        --format='%h§%ad§%s' --date=format:'%Y-%m-%d %H:%M' 2>/dev/null
fi
```

Collect: `commits_by_cwd: {cwd: [(sha, time, subject), ...]}`. May be
empty for any given cwd.

### 5. Compose the markdown report

The report has exactly this structure. Use it verbatim:

```markdown
# Wakeup — <GENERATED_AT_LOCAL>

**Window**: <WINDOW_LABEL> · scanned <N> projects · <M> sessions · <K> commits

## TL;DR

<2-4 paragraphs of prose. See "Writing the TL;DR" below.>

## By project

### `<cwd>` · <git_branch> · <session_count> sessions

- **<ts_first_local HH:MM>–<ts_last_local HH:MM>** · `<slug-or-"(no slug)">` · <event_count> events
  - Intent: <first_user_msg>
  - Tools: <tool_counts as "Edit×12, Bash×8, ..." sorted by count desc>
- ...

Commits in window:
- `[<sha>]` <subject>
- ...

(or, if no commits in window for this project:)
_No commits in window._

### `<next cwd>` ...
```

Details:
- Timestamp display: convert UTC `ts_first` / `ts_last` to **local time**
  using `date -d "$ts" '+%H:%M'`. If `ts_first` and `ts_last` are on
  different local calendar days, show `MM-DD HH:MM–MM-DD HH:MM` instead.
- `tool_counts`: drop counts of 0; sort descending; format as
  `Edit×12, Bash×8, Agent×3`.
- `first_user_msg`: already truncated by extract.py. If it starts with
  `<system-reminder>` or `<command-name>`, mark intent as
  `(triggered by /<command>)` or `(system-initiated)` and try the
  SECOND user message instead — but extract.py only captures the
  first; for now just show what we have, prefixed with `(system)`.
- `slug == null`: show `(no slug)`.
- `git_branch == "HEAD"`: show as `(detached)`.
- Cwds with NO sessions but WITH commits (rare — user committed
  outside a Claude session): include the cwd section with 0 sessions
  and just the commits list. Header: `### `<cwd>` · (no sessions, N commits)`.

### Writing the TL;DR

After you have the structured data, write **2–4 short paragraphs** of
prose that:

1. **Lead with the dominant theme** — which project absorbed most
   sessions / commits / event_count? What was the main thread of work
   there? Use `first_user_msg` + commit subjects + tool mix as
   evidence. Be concrete (mention specific files, commits, or fixes
   by name when they appear in commit subjects).
2. **Mention secondary projects** — if there's a clear #2 / #3, give
   each one sentence. Don't list every cwd — only the ones where
   meaningful work happened.
3. **Surface unresolved threads** if any — sessions that ended
   recently with a question-shaped last user message, an
   `ExitPlanMode` followed by no commits, or a high event count but
   zero commits (suggests in-progress / blocked work). This is the
   most actionable part of the recap, since unresolved threads are
   what the user most needs to pick back up.

Style: terse, factual, concrete. No filler like "Yesterday you had a
productive day". No emojis. No bullet points inside TL;DR — that's what
the cards below are for. Match the user's prevailing language
(Chinese vs English) based on `first_user_msg` content.

### 6. Dual output

```bash
ARCHIVE_DIR="$HOME/.claude/wakeup"
mkdir -p "$ARCHIVE_DIR"
ARCHIVE_FILE="$ARCHIVE_DIR/$(date '+%Y-%m-%d-%H%M').md"
```

- Write the report to `$ARCHIVE_FILE` (use Write tool).
- ALSO emit the full report as your text response in this turn. Print
  a trailing line `_Archived to: <ARCHIVE_FILE>_` so the user knows
  where the file lives.

If a file at that filename already exists (e.g. user ran `/wakeup`
twice in the same minute), suffix with `-2`, `-3`, etc.

## Failure modes

- `~/.claude/projects/` missing → print `No Claude Code transcripts
  found at ~/.claude/projects/.` and exit.
- `extract.py` returns non-zero or invalid JSON → show stderr to user,
  do not silently proceed.
- Single malformed line in a jsonl → already handled inside
  extract.py (counted in `malformed_lines`); if `malformed_lines > 0`,
  add a footer note: `_<N> malformed lines skipped across transcripts._`
- Some project cwd no longer exists / not a git repo → that project's
  "Commits in window" section becomes `_Not a git repo or path no
  longer exists._` — don't crash.
- All sessions in window are subagent-only (no top-level activity) →
  shouldn't happen since extract.py only walks maxdepth=1 of project
  dirs; if it does, treat as empty window.

## What NOT to do

- Don't read jsonl raw content to write the prose. The structured
  fields (slug, first_user_msg, tool_counts, commits) are enough.
  Reading raw transcripts wastes context and slows wakeup massively.
- Don't auto-fire on every new session. This is manual-invoke only.
- Don't aggregate across multiple `/wakeup` runs — each is independent
  and produces its own dated archive.
- Don't filter by cwd / project. Scope is always all projects (the
  user picked this design — see plan).
- Don't include `Skill` / `ToolSearch` / `Read` / minor tool counts if
  they'd clutter the line — but DO include them if they're in the
  top 5 by count.
