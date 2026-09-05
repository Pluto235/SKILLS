#!/usr/bin/env python3
"""Search arXiv's public export API."""

from __future__ import annotations

import argparse
import json
import time
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


ARXIV_URL = "https://export.arxiv.org/api/query"
ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"


def fetch(params: dict[str, Any]) -> bytes:
    url = f"{ARXIV_URL}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "codex-nasa-ads-literature/1.0"})
    try:
        with urlopen(request, timeout=30) as response:
            return response.read()
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"arXiv HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise SystemExit(f"arXiv request failed: {exc}") from exc


def text(parent: ET.Element, name: str) -> str:
    node = parent.find(name)
    return "" if node is None or node.text is None else " ".join(node.text.split())


def parse_entry(entry: ET.Element) -> dict[str, Any]:
    links = []
    for link in entry.findall(f"{ATOM}link"):
        links.append(
            {
                "rel": link.attrib.get("rel"),
                "type": link.attrib.get("type"),
                "href": link.attrib.get("href"),
                "title": link.attrib.get("title"),
            }
        )

    categories = [cat.attrib.get("term", "") for cat in entry.findall(f"{ATOM}category")]
    authors = [text(author, f"{ATOM}name") for author in entry.findall(f"{ATOM}author")]
    arxiv_id = text(entry, f"{ATOM}id").rsplit("/", 1)[-1]
    pdf = ""
    for link in links:
        if link.get("title") == "pdf" or link.get("type") == "application/pdf":
            pdf = link.get("href") or ""
            break
    if pdf and not pdf.endswith(".pdf"):
        pdf = f"{pdf}.pdf"

    primary_node = entry.find(f"{ARXIV}primary_category")

    return {
        "id": arxiv_id,
        "title": text(entry, f"{ATOM}title"),
        "authors": authors,
        "summary": text(entry, f"{ATOM}summary"),
        "published": text(entry, f"{ATOM}published"),
        "updated": text(entry, f"{ATOM}updated"),
        "primary_category": primary_node.attrib.get("term", "") if primary_node is not None else "",
        "categories": categories,
        "doi": text(entry, f"{ARXIV}doi"),
        "journal_ref": text(entry, f"{ARXIV}journal_ref"),
        "comment": text(entry, f"{ARXIV}comment"),
        "abs_url": f"https://arxiv.org/abs/{arxiv_id}",
        "pdf_url": pdf or f"https://arxiv.org/pdf/{arxiv_id}.pdf",
    }


def parse_feed(raw: bytes) -> tuple[int | None, list[dict[str, Any]]]:
    root = ET.fromstring(raw)
    total_node = root.find("{http://a9.com/-/spec/opensearch/1.1/}totalResults")
    total = int(total_node.text) if total_node is not None and total_node.text else None
    entries = [parse_entry(entry) for entry in root.findall(f"{ATOM}entry")]
    return total, entries


def render_markdown(query: str, total: int | None, entries: list[dict[str, Any]]) -> str:
    lines = [
        "# arXiv Results",
        "",
        f"- Query: `{query}`",
        f"- Retrieved: {time.strftime('%Y-%m-%d')}",
        f"- Total matches: {total if total is not None else 'unknown'}",
        f"- Returned: {len(entries)}",
        "",
    ]

    for i, item in enumerate(entries, start=1):
        authors = item["authors"]
        first_author = authors[0] if authors else "Unknown author"
        lines.append(f"## {i}. {item['title']}")
        lines.append("")
        lines.append(f"- Authors: {first_author}" + (f" et al. ({len(authors)} authors)" if len(authors) > 1 else ""))
        lines.append(f"- Published: {item['published'][:10]}")
        lines.append(f"- Updated: {item['updated'][:10]}")
        if item["primary_category"]:
            lines.append(f"- Primary category: {item['primary_category']}")
        lines.append(f"- arXiv: [{item['id']}]({item['abs_url']})")
        lines.append(f"- PDF: {item['pdf_url']}")
        if item["doi"]:
            lines.append(f"- DOI: https://doi.org/{item['doi']}")
        if item["journal_ref"]:
            lines.append(f"- Journal ref: {item['journal_ref']}")
        if item["comment"]:
            lines.append(f"- Comment: {item['comment']}")
        summary = item["summary"]
        lines.append(f"- Summary: {summary[:700]}{'...' if len(summary) > 700 else ''}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Search arXiv.")
    parser.add_argument("--query", help="arXiv search_query string.")
    parser.add_argument("--id-list", help="Comma-separated arXiv IDs.")
    parser.add_argument("--rows", type=int, default=10, help="Max results.")
    parser.add_argument("--start", type=int, default=0, help="Start offset.")
    parser.add_argument(
        "--sort-by",
        choices=("relevance", "lastUpdatedDate", "submittedDate"),
        default="submittedDate",
    )
    parser.add_argument(
        "--sort-order",
        choices=("ascending", "descending"),
        default="descending",
    )
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    if not args.query and not args.id_list:
        raise SystemExit("Provide --query or --id-list.")

    params = {
        "start": max(0, args.start),
        "max_results": max(0, min(args.rows, 100)),
        "sortBy": args.sort_by,
        "sortOrder": args.sort_order,
    }
    if args.query:
        params["search_query"] = args.query
    if args.id_list:
        params["id_list"] = args.id_list

    raw = fetch(params)
    total, entries = parse_feed(raw)
    if args.format == "json":
        print(json.dumps({"total": total, "entries": entries}, indent=2, ensure_ascii=False))
        return 0
    print(render_markdown(args.query or f"id_list:{args.id_list}", total, entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
