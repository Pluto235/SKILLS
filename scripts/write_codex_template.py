#!/usr/bin/env python3
"""Write a safe Codex config template from the current config."""
from __future__ import annotations

import sys
from pathlib import Path

SAFE_TOP_LEVEL = {"model_reasoning_effort", "disable_response_storage"}
SAFE_TABLE_PREFIXES = ("plugins.",)


def parse_simple_toml(text: str) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    top: dict[str, str] = {}
    tables: dict[str, dict[str, str]] = {}
    current: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            table_name = line[1:-1]
            current = table_name if table_name.startswith(SAFE_TABLE_PREFIXES) else None
            if current is not None:
                tables.setdefault(current, {})
            continue
        if "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        if current is None:
            if key in SAFE_TOP_LEVEL:
                top[key] = value.replace(str(Path.home()), "$HOME")
        elif current is not None:
            tables[current][key] = value.replace(str(Path.home()), "$HOME")
    return top, tables


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: write_codex_template.py CONFIG OUT", file=sys.stderr)
        return 2
    config_path = Path(sys.argv[1]).expanduser()
    out_path = Path(sys.argv[2]).expanduser()
    text = config_path.read_text() if config_path.exists() else ""
    top, tables = parse_simple_toml(text)
    lines = ["# Safe Codex config template. No auth tokens, sessions, caches, or project trust entries."]
    for key, value in top.items():
        lines.append(f"{key} = {value}")
    for name, values in tables.items():
        lines.extend(["", f"[{name}]"])
        lines.extend(f"{key} = {value}" for key, value in values.items())
    out_path.write_text("\n".join(lines).rstrip() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
