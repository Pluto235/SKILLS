#!/usr/bin/env python3
"""Merge a small safe TOML template into ~/.codex/config.toml.

This intentionally supports only the subset this repo owns: top-level scalar
preferences plus [marketplaces.*] and [plugins.*] tables.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def expand_home(text: str) -> str:
    return text.replace("$HOME", str(Path.home()))


def parse_simple_toml(text: str) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    top: dict[str, str] = {}
    tables: dict[str, dict[str, str]] = {}
    current: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            tables.setdefault(current, {})
            continue
        if "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        if current is None:
            top[key] = value
        else:
            tables[current][key] = value
    return top, tables


def render_table(name: str, values: dict[str, str]) -> str:
    lines = [f"[{name}]"]
    lines.extend(f"{key} = {value}" for key, value in values.items())
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: merge_codex_config.py CONFIG TEMPLATE", file=sys.stderr)
        return 2

    config_path = Path(sys.argv[1]).expanduser()
    template_path = Path(sys.argv[2]).expanduser()
    template = expand_home(template_path.read_text())
    template_top, template_tables = parse_simple_toml(template)

    existing = config_path.read_text() if config_path.exists() else ""
    existing_top, existing_tables = parse_simple_toml(existing)
    existing_top.update(template_top)
    existing_tables.update(template_tables)

    # Preserve unmanaged top-level scalar settings; drop and regenerate managed
    # marketplace/plugin tables so repeated installs stay idempotent.
    lines: list[str] = []
    for key, value in existing_top.items():
        lines.append(f"{key} = {value}")
    if lines:
        lines.append("")
    for name, values in existing_tables.items():
        lines.append(render_table(name, values))
        lines.append("")

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("\n".join(lines).rstrip() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
