#!/usr/bin/env python3
"""Extract privacy-limited metadata from recent Codex JSONL sessions."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def parse_since(value: str) -> datetime:
    value = value.strip()
    now = datetime.now(timezone.utc)
    if match := re.fullmatch(r"(\d+)([hd])", value):
        amount = int(match.group(1))
        return now - (timedelta(hours=amount) if match.group(2) == "h" else timedelta(days=amount))
    if value.startswith("since "):
        value = value.removeprefix("since ").strip()
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def text_content(content: Any) -> str | None:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return None
    parts = [
        item.get("text", "")
        for item in content
        if isinstance(item, dict) and item.get("type") in {"input_text", "output_text", "text"}
    ]
    value = " ".join(part for part in parts if part)
    return value or None


def shorten(value: str, limit: int = 240) -> str:
    value = " ".join(value.split())
    return value if len(value) <= limit else value[: limit - 1] + "…"


def process(path: Path, cutoff: datetime) -> tuple[dict[str, Any] | None, int]:
    session_id = path.stem
    cwd = None
    source = None
    model = None
    first_user_msg = None
    first_at = None
    last_at = None
    user_msg_count = 0
    event_count = 0
    tools: Counter[str] = Counter()
    malformed = 0

    try:
        lines = path.open("r", encoding="utf-8", errors="replace")
    except OSError:
        return None, 0
    with lines:
        for raw in lines:
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                malformed += 1
                continue
            payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
            if event.get("type") == "session_meta":
                session_id = payload.get("id") or session_id
                cwd = payload.get("cwd") or cwd
                source = payload.get("source") or source
            if event.get("type") == "turn_context":
                cwd = payload.get("cwd") or cwd
                model = payload.get("model") or model

            at = timestamp(event.get("timestamp"))
            if at is None or at < cutoff:
                continue
            event_count += 1
            first_at = at if first_at is None or at < first_at else first_at
            last_at = at if last_at is None or at > last_at else last_at

            if (
                event.get("type") == "response_item"
                and payload.get("type") == "message"
                and payload.get("role") == "user"
            ):
                user_msg_count += 1
                if first_user_msg is None and (value := text_content(payload.get("content"))):
                    first_user_msg = shorten(value)
            if event.get("type") == "response_item" and payload.get("type") in {
                "function_call",
                "custom_tool_call",
            }:
                tools[str(payload.get("name") or payload.get("tool_name") or "unknown")] += 1

    if event_count == 0:
        return None, malformed
    return {
        "session_id": session_id,
        "cwd": cwd,
        "source": source,
        "model": model,
        "ts_first": first_at.isoformat().replace("+00:00", "Z") if first_at else None,
        "ts_last": last_at.isoformat().replace("+00:00", "Z") if last_at else None,
        "first_user_msg": first_user_msg,
        "tool_counts": dict(tools.most_common()),
        "event_count": event_count,
        "user_msg_count": user_msg_count,
    }, malformed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", default="24h")
    parser.add_argument("--sessions-root", default=str(Path.home() / ".codex" / "sessions"))
    args = parser.parse_args()
    try:
        cutoff = parse_since(args.since)
    except ValueError as exc:
        print(f"invalid --since value: {args.since}: {exc}", file=sys.stderr)
        return 2

    root = Path(args.sessions_root).expanduser()
    files = sorted(root.rglob("*.jsonl")) if root.exists() else []
    sessions = []
    malformed = 0
    for path in files:
        item, skipped = process(path, cutoff)
        malformed += skipped
        if item is not None:
            sessions.append(item)
    sessions.sort(key=lambda item: (item.get("cwd") or "", item.get("ts_first") or ""))
    json.dump(
        {
            "since": cutoff.isoformat().replace("+00:00", "Z"),
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "scanned_files": len(files),
            "malformed_lines": malformed,
            "sessions": sessions,
        },
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
