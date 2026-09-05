---
name: wakeup
description: Use when the user asks what they worked on recently across Codex projects, requests a morning recap, or invokes $wakeup with a time window such as 12h, 2d, or "since YYYY-MM-DD".
---

# Wakeup

Create a concise cross-project recap from local Codex session metadata and Git history.

## Workflow

1. Run `python3 scripts/extract.py --since <window>` from this skill directory. The default window is `24h`; accepted forms are `Nh`, `Nd`, `since YYYY-MM-DD`, or an ISO-8601 timestamp.
2. Use the returned session summaries—never dump raw JSONL transcripts into the conversation. Group sessions by `cwd` and inspect `git log --since=<resolved_since>` for existing repositories.
3. Lead with a 2–4 paragraph factual summary of the dominant work, secondary projects, and likely unfinished threads. Then provide compact per-project cards with time range, first request, tool counts, and commits.
4. If there is no activity, say so and do not create a report file.
5. Otherwise save the same report under `~/.codex/wakeup/YYYY-MM-DD-HHMM.md`, adding a numeric suffix if necessary, and report the saved path.

## Boundaries

- Read only `~/.codex/sessions` and Git metadata unless the user expands scope.
- Do not include credentials, full prompts, tool outputs, or raw transcript paths in the report.
- Treat the first user message as a short intent hint, not as proof that the work completed.
- This is the Codex-native successor to the old Claude Code `wakeup` skill; do not read `~/.claude/projects`.
