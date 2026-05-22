#!/usr/bin/env python3
"""Extract Claude Code session metadata within a time window.

Reads ~/.claude/projects/*/*.jsonl (top-level only, no subagent subdirs),
filters events whose timestamp >= --since, and emits one JSON object per
session that had any in-window event.

Output: a single JSON document on stdout:
  {
    "sessions": [
      {
        "session_id":     "ea982491-...",
        "jsonl_path":     "/home/shijie/.claude/projects/.../ea98....jsonl",
        "cwd":            "/srv/shared/science/solver/v4.2",
        "git_branch":     "v4.2",
        "slug":           "v4-2-log-md-agent-log-claude-md-plan-...",
        "ts_first":       "2026-05-22T01:23:45.678Z",
        "ts_last":        "2026-05-22T05:12:34.567Z",
        "first_user_msg": "我希望子啊v4.2下...(truncated 240 chars)",
        "tool_counts":    {"Bash": 12, "Edit": 8, "Agent": 3},
        "event_count":    421,
        "user_msg_count": 17
      },
      ...
    ],
    "skipped_files":      [...paths that failed to parse...],
    "malformed_lines":    int,
    "scanned_files":      int
  }
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _coerce_str(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        # Anthropic content blocks: [{"type":"text","text":"..."}, ...]
        parts = []
        for block in value:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return str(value)


def _extract_first_user_text(event: dict) -> str | None:
    if event.get("type") != "user":
        return None
    msg = event.get("message")
    if isinstance(msg, str):
        # Sometimes stringified python repr — try to recover the content
        # by treating it as opaque text
        return msg
    if isinstance(msg, dict):
        if msg.get("role") != "user":
            return None
        return _coerce_str(msg.get("content", ""))
    return None


def _short(s: str, n: int = 240) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "…"


def _iter_jsonls(root: Path) -> list[Path]:
    out = []
    if not root.exists():
        return out
    for proj in sorted(root.iterdir()):
        if not proj.is_dir():
            continue
        for f in sorted(proj.iterdir()):
            if f.is_file() and f.suffix == ".jsonl":
                out.append(f)
    return out


def process_file(path: Path, since_iso: str) -> dict | None:
    """Return per-session aggregate, or None if no in-window events."""
    cwd = None
    git_branch = None
    slug = None
    ts_first = None
    ts_last = None
    first_user_msg = None
    tool_counts: dict[str, int] = {}
    event_count = 0
    user_msg_count = 0
    malformed = 0

    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
                continue

            ts = ev.get("timestamp")
            if not ts or ts < since_iso:
                continue

            event_count += 1
            ts_first = ts if ts_first is None or ts < ts_first else ts_first
            ts_last = ts if ts_last is None or ts > ts_last else ts_last

            if cwd is None:
                cwd = ev.get("cwd")
            if git_branch is None:
                git_branch = ev.get("gitBranch")
            if slug is None:
                slug = ev.get("slug")

            etype = ev.get("type")
            if etype == "user":
                user_msg_count += 1
                if first_user_msg is None:
                    txt = _extract_first_user_text(ev)
                    if txt:
                        first_user_msg = _short(txt)
            elif etype == "assistant":
                msg = ev.get("message")
                if isinstance(msg, dict):
                    content = msg.get("content")
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "tool_use":
                                name = block.get("name", "?")
                                tool_counts[name] = tool_counts.get(name, 0) + 1

    if event_count == 0:
        return None

    return {
        "session_id": path.stem,
        "jsonl_path": str(path),
        "cwd": cwd,
        "git_branch": git_branch,
        "slug": slug,
        "ts_first": ts_first,
        "ts_last": ts_last,
        "first_user_msg": first_user_msg,
        "tool_counts": tool_counts,
        "event_count": event_count,
        "user_msg_count": user_msg_count,
        "_malformed_lines": malformed,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--since",
        required=True,
        help="ISO 8601 UTC cutoff (e.g. 2026-05-21T13:00:00Z). Events with "
             "timestamp >= this value are kept.",
    )
    ap.add_argument(
        "--projects-root",
        default=str(Path.home() / ".claude" / "projects"),
        help="Override projects dir (default: ~/.claude/projects).",
    )
    args = ap.parse_args()

    # Normalize the cutoff: callers may pass with/without trailing Z, with
    # microseconds or without. Compare as strings only if both are
    # lexicographically comparable (ISO 8601 with fixed UTC offset).
    cutoff = args.since.strip()
    try:
        # Validate parse, but compare via string (events use ms precision + Z)
        datetime.fromisoformat(cutoff.replace("Z", "+00:00"))
    except ValueError:
        print(f"invalid --since: {cutoff}", file=sys.stderr)
        return 2

    root = Path(args.projects_root)
    files = _iter_jsonls(root)

    sessions = []
    skipped: list[str] = []
    malformed_total = 0

    for f in files:
        try:
            agg = process_file(f, cutoff)
        except (OSError, UnicodeDecodeError) as e:
            skipped.append(f"{f}: {e}")
            continue
        if agg is None:
            continue
        malformed_total += agg.pop("_malformed_lines", 0)
        sessions.append(agg)

    sessions.sort(key=lambda s: (s["cwd"] or "", s["ts_first"] or ""))

    payload = {
        "sessions": sessions,
        "skipped_files": skipped,
        "malformed_lines": malformed_total,
        "scanned_files": len(files),
        "since": cutoff,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
