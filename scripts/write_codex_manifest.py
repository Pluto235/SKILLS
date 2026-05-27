#!/usr/bin/env python3
"""Write a compact manifest for managed Codex assets."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def dirs(path: Path) -> list[str]:
    if not path.exists():
        return []
    return sorted(p.name for p in path.iterdir() if p.is_dir() and (p / "SKILL.md").exists())


def subdirs(path: Path) -> list[str]:
    if not path.exists():
        return []
    return sorted(p.name for p in path.iterdir() if p.is_dir())


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: write_codex_manifest.py CODEX_DIR", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    manifest = {
        "skills": {
            "codex": dirs(root / "skills"),
            "agents": dirs(root / "agents-skills"),
            "shared": dirs(root.parent / "shared" / "skills"),
            "pua_codex": bool(dirs(root / "pua-skills")),
        },
        "plugins": {
            "enabled": ["browser@openai-bundled"],
            "local_marketplaces": subdirs(root / "local-marketplaces"),
            "notes": {
                "claude_plugins_are_not_copied": True,
                "context7_github_web_access": "Adapt later through Codex MCP/plugin support instead of copying Claude plugins verbatim.",
            },
        },
    }
    (root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
