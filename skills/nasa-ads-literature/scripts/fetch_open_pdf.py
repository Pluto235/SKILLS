#!/usr/bin/env python3
"""Download openly reachable PDFs, with first-class support for arXiv."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def safe_name(value: str) -> str:
    value = value.strip().replace("/", "_")
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value)


def arxiv_pdf_url(arxiv_id: str) -> str:
    cleaned = arxiv_id.strip()
    if cleaned.lower().startswith("arxiv:"):
        cleaned = cleaned.split(":", 1)[1]
    return f"https://arxiv.org/pdf/{cleaned}.pdf"


def download(url: str, output: Path) -> None:
    request = Request(url, headers={"User-Agent": "codex-nasa-ads-literature/1.0"})
    try:
        with urlopen(request, timeout=60) as response:
            content_type = response.headers.get("Content-Type", "")
            data = response.read()
    except HTTPError as exc:
        body = exc.read(300).decode("utf-8", errors="replace")
        raise SystemExit(f"Download HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise SystemExit(f"Download failed: {exc}") from exc

    if not data.startswith(b"%PDF") and "pdf" not in content_type.lower():
        raise SystemExit(f"Refusing to save non-PDF response from {url} ({content_type}).")

    output.write_bytes(data)


def main() -> int:
    parser = argparse.ArgumentParser(description="Download an open PDF.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--arxiv", help="arXiv identifier.")
    group.add_argument("--url", help="Direct open PDF URL.")
    parser.add_argument("--output-dir", default=".", help="Destination directory.")
    parser.add_argument("--filename", help="Optional output filename.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.arxiv:
        url = arxiv_pdf_url(args.arxiv)
        filename = args.filename or f"arxiv-{safe_name(args.arxiv)}.pdf"
    else:
        url = args.url
        parsed_name = Path(urlparse(url).path).name or "paper.pdf"
        filename = args.filename or safe_name(parsed_name)
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"

    output = output_dir / filename
    download(url, output)
    print(output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
