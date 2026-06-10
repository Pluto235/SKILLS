#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


SKILL_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = SKILL_DIR / "assets"


@dataclass
class Heading:
    level: int
    text: str
    slug: str


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    raw = text[4:end]
    body = text[end + 5 :]
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        meta[key.strip()] = value
    return meta, body


def slugify(text: str, used: set[str]) -> str:
    base = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text.strip().lower(), flags=re.UNICODE)
    base = re.sub(r"-+", "-", base).strip("-") or "section"
    slug = base
    i = 2
    while slug in used:
        slug = f"{base}-{i}"
        i += 1
    used.add(slug)
    return slug


def inline_md(text: str) -> str:
    tokens: list[str] = []

    def stash(value: str) -> str:
        tokens.append(value)
        return f"\x00{len(tokens)-1}\x00"

    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", lambda m: stash(f'<img src="{esc(m.group(2))}" alt="{esc(m.group(1))}">'), text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: stash(f'<a href="{esc(m.group(2))}">{esc(m.group(1))}</a>'), text)
    text = re.sub(r"`([^`]+)`", lambda m: stash(f"<code>{esc(m.group(1))}</code>"), text)
    text = esc(text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    for i, value in enumerate(tokens):
        text = text.replace(f"\x00{i}\x00", value)
    return text


def render_image_figure(line: str) -> str | None:
    m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", line.strip())
    if not m:
        return None
    alt, src = m.group(1), m.group(2)
    caption = f"<figcaption>{inline_md(alt)}</figcaption>" if alt.strip() else ""
    return f'<figure><img src="{esc(src)}" alt="{esc(alt)}">{caption}</figure>'


def is_table_start(lines: list[str], i: int) -> bool:
    if i + 1 >= len(lines):
        return False
    return "|" in lines[i] and re.match(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$", lines[i + 1]) is not None


def split_table_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]


def render_table(lines: list[str]) -> str:
    header = split_table_row(lines[0])
    rows = [split_table_row(line) for line in lines[2:] if line.strip()]
    out = ["<table>", "<thead><tr>"]
    out.extend(f"<th>{inline_md(cell)}</th>" for cell in header)
    out.append("</tr></thead>")
    out.append("<tbody>")
    for row in rows:
        out.append("<tr>")
        width = max(len(header), len(row))
        row = row + [""] * (width - len(row))
        out.extend(f"<td>{inline_md(cell)}</td>" for cell in row[:width])
        out.append("</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


def render_list(items: list[str], ordered: bool) -> str:
    tag = "ol" if ordered else "ul"
    out = [f"<{tag}>"]
    for item in items:
        item = re.sub(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)", "", item)
        out.append(f"<li>{inline_md(item)}</li>")
    out.append(f"</{tag}>")
    return "\n".join(out)


def render_blockquote(lines: list[str]) -> str:
    cleaned = [re.sub(r"^\s*>\s?", "", line) for line in lines]
    first = cleaned[0].strip() if cleaned else ""
    callout = re.match(r"^\[!(NOTE|TIP|WARNING|RESULT)\]\s*$", first, re.I)
    if callout:
        kind = callout.group(1).lower()
        labels = {"note": "说明", "tip": "提示", "warning": "注意", "result": "结果"}
        body = "\n".join(cleaned[1:]).strip()
        return f'<div class="callout {kind}"><div class="callout-title">{labels[kind]}</div>{render_blocks(body.splitlines(), collect_headings=False)[0]}</div>'
    body = render_blocks(cleaned, collect_headings=False)[0]
    return f"<blockquote>{body}</blockquote>"


def flush_paragraph(paragraph: list[str], out: list[str]) -> None:
    if paragraph:
        out.append(f"<p>{inline_md(' '.join(line.strip() for line in paragraph))}</p>")
        paragraph.clear()


def render_blocks(lines: list[str], collect_headings: bool = True) -> tuple[str, list[Heading]]:
    out: list[str] = []
    headings: list[Heading] = []
    used_slugs: set[str] = set()
    paragraph: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            flush_paragraph(paragraph, out)
            i += 1
            continue

        if stripped.startswith("```"):
            flush_paragraph(paragraph, out)
            lang = stripped[3:].strip()
            i += 1
            code_lines: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            class_attr = f' class="language-{esc(lang)}"' if lang else ""
            out.append(f"<pre><code{class_attr}>{esc(chr(10).join(code_lines))}</code></pre>")
            continue

        m = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if m:
            flush_paragraph(paragraph, out)
            level = len(m.group(1))
            text = re.sub(r"\s+#+\s*$", "", m.group(2)).strip()
            slug = slugify(re.sub(r"<[^>]+>", "", text), used_slugs)
            if collect_headings and level in (2, 3):
                headings.append(Heading(level=level, text=text, slug=slug))
            out.append(f'<h{level} id="{esc(slug)}">{inline_md(text)}</h{level}>')
            i += 1
            continue

        if is_table_start(lines, i):
            flush_paragraph(paragraph, out)
            table_lines = [lines[i], lines[i + 1]]
            i += 2
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                table_lines.append(lines[i])
                i += 1
            out.append(render_table(table_lines))
            continue

        if re.match(r"^\s*>\s?", line):
            flush_paragraph(paragraph, out)
            quote_lines = [line]
            i += 1
            while i < len(lines) and re.match(r"^\s*>\s?", lines[i]):
                quote_lines.append(lines[i])
                i += 1
            out.append(render_blockquote(quote_lines))
            continue

        if re.match(r"^\s*[-*+]\s+", line):
            flush_paragraph(paragraph, out)
            items = [line]
            i += 1
            while i < len(lines) and re.match(r"^\s*[-*+]\s+", lines[i]):
                items.append(lines[i])
                i += 1
            out.append(render_list(items, ordered=False))
            continue

        if re.match(r"^\s*\d+[.)]\s+", line):
            flush_paragraph(paragraph, out)
            items = [line]
            i += 1
            while i < len(lines) and re.match(r"^\s*\d+[.)]\s+", lines[i]):
                items.append(lines[i])
                i += 1
            out.append(render_list(items, ordered=True))
            continue

        if re.match(r"^---+$", stripped):
            flush_paragraph(paragraph, out)
            out.append("<hr>")
            i += 1
            continue

        if re.match(r"^!\[[^\]]*\]\([^)]+\)\s*$", stripped):
            flush_paragraph(paragraph, out)
            out.append(render_image_figure(stripped) or f"<figure>{inline_md(stripped)}</figure>")
            i += 1
            continue

        paragraph.append(line)
        i += 1

    flush_paragraph(paragraph, out)
    return "\n".join(out), headings


def render_toc(headings: Iterable[Heading], enabled: bool) -> str:
    if not enabled:
        return '<div class="toc-empty">未启用</div>'
    items = []
    for h in headings:
        cls = "toc-h3" if h.level == 3 else "toc-h2"
        items.append(f'<li class="{cls}"><a href="#{esc(h.slug)}" title="{esc(h.text)}">{esc(h.text)}</a></li>')
    if not items:
        return '<div class="toc-empty">无二级标题</div>'
    return '<ol class="toc-list">\n' + "\n".join(items) + "\n</ol>"


def render_report(markdown_path: Path, output_path: Path | None = None) -> Path:
    meta, body_md = parse_frontmatter(read_text(markdown_path))
    body_html, headings = render_blocks(body_md.splitlines())
    title = meta.get("title") or next((h.text for h in headings if h.level == 2), markdown_path.stem)
    output = output_path or Path(meta.get("output", markdown_path.with_suffix(".html").name))
    if not output.is_absolute():
        output = markdown_path.parent / output
    subtitle = meta.get("subtitle", "")
    author = meta.get("author", "")
    report_date = meta.get("date", date.today().isoformat())
    lang = meta.get("lang", "zh-CN")
    toc_enabled = meta.get("toc", "true").strip().lower() not in {"false", "0", "no", "off"}
    meta_parts = [part for part in [author, report_date] if part]
    template = read_text(ASSETS_DIR / "notion_report_template.html")
    css = read_text(ASSETS_DIR / "notion_report.css")
    html_text = template
    replacements = {
        "{{ lang }}": esc(lang),
        "{{ title }}": esc(title),
        "{{ subtitle }}": esc(subtitle),
        "{{ kicker }}": esc(meta.get("kicker", "Notion HTML Report")),
        "{{ meta }}": esc(" · ".join(meta_parts)),
        "{{ toc }}": render_toc(headings, toc_enabled),
        "{{ body }}": body_html,
        "{{ css }}": css,
    }
    for key, value in replacements.items():
        html_text = html_text.replace(key, value)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html_text, encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a Notion-like static HTML report from Markdown.")
    parser.add_argument("markdown", type=Path, help="Input Markdown report")
    parser.add_argument("--output", "-o", type=Path, help="Output HTML path")
    args = parser.parse_args()
    output = render_report(args.markdown, args.output)
    print(output)


if __name__ == "__main__":
    main()
