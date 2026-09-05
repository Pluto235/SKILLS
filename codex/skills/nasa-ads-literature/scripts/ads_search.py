#!/usr/bin/env python3
"""Search NASA ADS and export compact results."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


ADS_SEARCH_URL = "https://api.adsabs.harvard.edu/v1/search/query"
ADS_EXPORT_URL = "https://api.adsabs.harvard.edu/v1/export/bibtex"
DEFAULT_FIELDS = (
    "bibcode,title,author,year,pub,pubdate,doi,identifier,"
    "citation_count,read_count,abstract,keyword,bibstem,doctype"
)


def read_token() -> str:
    for name in ("ADS_DEV_KEY", "ADS_API_TOKEN"):
        value = os.environ.get(name)
        if value:
            return value.strip()

    token_file = Path.home() / ".ads" / "dev_key"
    if token_file.exists():
        return token_file.read_text(encoding="utf-8").strip()

    raise SystemExit(
        "ADS token not found. Set ADS_DEV_KEY or create ~/.ads/dev_key with permissions 0600."
    )


def ads_get(params: dict[str, Any], token: str) -> dict[str, Any]:
    url = f"{ADS_SEARCH_URL}?{urlencode(params, doseq=True)}"
    request = Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"ADS HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise SystemExit(f"ADS request failed: {exc}") from exc


def ads_post_json(url: str, payload: dict[str, Any], token: str) -> str:
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"ADS HTTP {exc.code}: {body_text}") from exc
    except URLError as exc:
        raise SystemExit(f"ADS request failed: {exc}") from exc

    export = data.get("export")
    if not isinstance(export, str):
        raise SystemExit(f"Unexpected ADS export response: {data}")
    return export


def normalize_query(args: argparse.Namespace) -> str:
    if args.bibcode:
        return f'bibcode:"{args.bibcode}"'
    if args.doi:
        return f'doi:"{args.doi}"'
    if args.arxiv:
        value = args.arxiv
        if not value.lower().startswith("arxiv:"):
            value = f"arXiv:{value}"
        return f'identifier:"{value}"'
    if args.query:
        return args.query
    raise SystemExit("Provide --query, --bibcode, --doi, or --arxiv.")


def as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    if value is None:
        return []
    return [str(value)]


def ads_link(bibcode: str) -> str:
    return f"https://ui.adsabs.harvard.edu/abs/{bibcode}/abstract"


def arxiv_ids(doc: dict[str, Any]) -> list[str]:
    ids = []
    for identifier in as_list(doc.get("identifier")):
        low = identifier.lower()
        if low.startswith("arxiv:"):
            ids.append(identifier.split(":", 1)[1])
    return ids


def render_markdown(data: dict[str, Any], query: str, fields: str) -> str:
    response = data.get("response", {})
    docs = response.get("docs", [])
    total = response.get("numFound", "unknown")
    lines = [
        "# NASA ADS Results",
        "",
        f"- Query: `{query}`",
        f"- Retrieved: {time.strftime('%Y-%m-%d')}",
        f"- Total matches: {total}",
        f"- Returned: {len(docs)}",
        f"- Fields: `{fields}`",
        "",
    ]

    for i, doc in enumerate(docs, start=1):
        title = " ".join(as_list(doc.get("title"))) or "(untitled)"
        authors = as_list(doc.get("author"))
        first_author = authors[0] if authors else "Unknown author"
        year = doc.get("year", "n.d.")
        bibcode = doc.get("bibcode", "")
        pub = doc.get("pub", "")
        doi = as_list(doc.get("doi"))
        ids = arxiv_ids(doc)
        citations = doc.get("citation_count", 0)
        reads = doc.get("read_count", 0)

        lines.append(f"## {i}. {title}")
        lines.append("")
        lines.append(f"- Authors: {first_author}" + (f" et al. ({len(authors)} authors)" if len(authors) > 1 else ""))
        lines.append(f"- Year: {year}")
        if pub:
            lines.append(f"- Publication: {pub}")
        if bibcode:
            lines.append(f"- ADS: [{bibcode}]({ads_link(bibcode)})")
        if doi:
            lines.append(f"- DOI: https://doi.org/{doi[0]}")
        if ids:
            lines.append(f"- arXiv: https://arxiv.org/abs/{ids[0]}")
            lines.append(f"- PDF: https://arxiv.org/pdf/{ids[0]}")
        lines.append(f"- Citations: {citations}")
        lines.append(f"- Reads: {reads}")
        abstract = doc.get("abstract")
        if abstract:
            abstract = " ".join(str(abstract).split())
            lines.append(f"- Abstract: {abstract[:700]}{'...' if len(abstract) > 700 else ''}")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Search NASA ADS.")
    parser.add_argument("--query", help="ADS search query.")
    parser.add_argument("--bibcode", help="Lookup a single ADS bibcode.")
    parser.add_argument("--doi", help="Lookup a DOI.")
    parser.add_argument("--arxiv", help="Lookup an arXiv identifier through ADS.")
    parser.add_argument("--rows", type=int, default=10, help="Rows to return, max 2000.")
    parser.add_argument("--start", type=int, default=0, help="Start offset.")
    parser.add_argument("--sort", default="date desc", help="ADS sort string.")
    parser.add_argument("--fields", default=DEFAULT_FIELDS, help="Comma-separated ADS fields.")
    parser.add_argument(
        "--format",
        choices=("markdown", "json", "bibtex"),
        default="markdown",
        help="Output format.",
    )
    args = parser.parse_args()

    token = read_token()
    query = normalize_query(args)
    fields = args.fields
    params = {
        "q": query,
        "fl": fields,
        "rows": max(0, min(args.rows, 2000)),
        "start": max(0, args.start),
        "sort": args.sort,
    }
    data = ads_get(params, token)

    if args.format == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0

    if args.format == "bibtex":
        docs = data.get("response", {}).get("docs", [])
        bibcodes = [doc["bibcode"] for doc in docs if doc.get("bibcode")]
        if not bibcodes:
            return 0
        print(ads_post_json(ADS_EXPORT_URL, {"bibcode": bibcodes}, token))
        return 0

    print(render_markdown(data, query, fields))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
