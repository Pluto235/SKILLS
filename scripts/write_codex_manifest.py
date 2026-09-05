#!/usr/bin/env python3
"""Write a compact manifest for managed Codex assets."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def dirs(path: Path) -> list[str]:
    if not path.exists():
        return []
    return sorted(p.name for p in path.iterdir() if p.is_dir() and (p / "SKILL.md").exists())


def plugin_snapshot() -> tuple[list[dict[str, object]], list[str]]:
    try:
        proc = subprocess.run(
            ["codex", "plugin", "list", "--json"],
            check=True,
            capture_output=True,
            text=True,
        )
        installed = json.loads(proc.stdout).get("installed", [])
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"warning: could not read Codex plugins: {exc}", file=sys.stderr)
        return [], []

    enabled = [
        {
            "id": item.get("pluginId"),
            "version": item.get("version"),
            "marketplace": item.get("marketplaceName"),
            "auth_policy": item.get("authPolicy"),
            "install_policy": item.get("installPolicy"),
        }
        for item in installed
        if item.get("installed") and item.get("enabled") and item.get("pluginId")
    ]
    restore = sorted(
        item["id"]
        for item in enabled
        if item.get("marketplace") == "openai-curated-remote"
        and item.get("install_policy") == "AVAILABLE"
    )
    return enabled, restore


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: write_codex_manifest.py SNAPSHOT_DIR", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    enabled_plugins, restore_plugins = plugin_snapshot()
    manifest = {
        "skills": {
            "root": "~/.agents/skills",
            "installed": dirs(root / "skills"),
        },
        "plugins": {
            "enabled": enabled_plugins,
            "restore": restore_plugins,
            "notes": {
                "authentication_is_not_exported": True,
                "bundled_and_default_plugins_are_restored_by_codex": True,
            },
        },
    }
    (root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
