#!/usr/bin/env python3
"""Convert a PDF to LLM-readable Markdown with MinerU and locate outputs."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", help="PDF file to convert")
    parser.add_argument(
        "-o",
        "--output-dir",
        help="Output directory. Defaults to <pdf parent>/mineru-md",
    )
    parser.add_argument(
        "-b",
        "--backend",
        default="pipeline",
        choices=[
            "pipeline",
            "vlm-http-client",
            "hybrid-http-client",
            "vlm-auto-engine",
            "hybrid-auto-engine",
        ],
        help="MinerU backend. Defaults to pipeline.",
    )
    parser.add_argument(
        "-m",
        "--method",
        default="txt",
        choices=["auto", "txt", "ocr"],
        help="MinerU parsing method. Use ocr for scanned/image PDFs.",
    )
    parser.add_argument(
        "-l",
        "--lang",
        default=None,
        help="OCR language hint, e.g. en, ch, japan, korean.",
    )
    parser.add_argument("--start", type=int, default=None, help="Start page, 0-based.")
    parser.add_argument("--end", type=int, default=None, help="End page, 0-based.")
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Disable formula and table parsing for faster text extraction.",
    )
    parser.add_argument(
        "--formula",
        choices=["true", "false"],
        default=None,
        help="Override formula parsing.",
    )
    parser.add_argument(
        "--table",
        choices=["true", "false"],
        default=None,
        help="Override table parsing.",
    )
    parser.add_argument(
        "--mineru-bin",
        default="mineru",
        help="MinerU executable. Defaults to mineru on PATH.",
    )
    parser.add_argument(
        "--preview-lines",
        type=int,
        default=12,
        help="Include first N lines of first Markdown file in JSON summary.",
    )
    return parser.parse_args()


def ensure_file(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"PDF not found: {path}")
    if not path.is_file():
        raise SystemExit(f"Path is not a file: {path}")
    if path.suffix.lower() != ".pdf":
        raise SystemExit(f"Expected a .pdf file: {path}")


def bool_arg(value: str | None) -> list[str]:
    if value is None:
        return []
    return [value]


def read_preview(md_path: Path, lines: int) -> str:
    if lines <= 0:
        return ""
    try:
        text = md_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return "\n".join(text.splitlines()[:lines]).strip()


def main() -> int:
    args = parse_args()
    pdf = Path(args.pdf).expanduser().resolve()
    ensure_file(pdf)

    mineru_bin = shutil.which(args.mineru_bin)
    if mineru_bin is None:
        raise SystemExit(
            f"MinerU executable not found on PATH: {args.mineru_bin}. "
            "Install MinerU and expose a mineru wrapper in ~/.local/bin or another PATH directory."
        )

    output_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else pdf.parent / "mineru-md"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    formula = args.formula
    table = args.table
    if args.fast:
        formula = "false" if formula is None else formula
        table = "false" if table is None else table

    cmd = [
        mineru_bin,
        "-p",
        str(pdf),
        "-o",
        str(output_dir),
        "-b",
        args.backend,
        "-m",
        args.method,
    ]
    if args.lang:
        cmd.extend(["--lang", args.lang])
    if args.start is not None:
        cmd.extend(["--start", str(args.start)])
    if args.end is not None:
        cmd.extend(["--end", str(args.end)])
    if formula is not None:
        cmd.extend(["--formula", formula])
    if table is not None:
        cmd.extend(["--table", table])

    env = os.environ.copy()
    env.setdefault("MINERU_MODEL_SOURCE", "modelscope")

    proc = subprocess.run(cmd, cwd=str(pdf.parent), env=env)
    if proc.returncode != 0:
        return proc.returncode

    markdown_files = sorted(str(path) for path in output_dir.rglob("*.md"))
    content_list_files = sorted(str(path) for path in output_dir.rglob("*content_list*.json"))
    middle_json_files = sorted(str(path) for path in output_dir.rglob("*middle.json"))

    summary = {
        "ok": bool(markdown_files),
        "pdf": str(pdf),
        "output_dir": str(output_dir),
        "markdown_files": markdown_files,
        "content_list_files": content_list_files,
        "middle_json_files": middle_json_files,
        "command": cmd,
        "method": args.method,
        "backend": args.backend,
        "fast": args.fast,
    }
    if markdown_files:
        summary["preview"] = read_preview(Path(markdown_files[0]), args.preview_lines)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if markdown_files else 2


if __name__ == "__main__":
    raise SystemExit(main())
