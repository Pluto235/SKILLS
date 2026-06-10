---
name: notion-html-report
description: Create or restyle Notion-like static HTML reports from Markdown, especially Chinese technical, scientific, experiment, reproduction, pipeline, and project reports that need a compact left table of contents, readable sections, figures, tables, callouts, and reproducibility metadata.
---

# Notion HTML Report

Use this skill when the user wants a polished static HTML report, especially when they mention Notion style, nition style, HTML 报告, 中文技术报告, 科研复现报告, pipeline 报告, 实验报告, or wants a readable report with a table of contents.

## Default Output

- Generate a single HTML file with inline CSS from Markdown. Referenced images remain normal local or remote links.
- Use a Notion-like reading style: white background, narrow readable body, quiet borders, compact tables, clear figures, and restrained callouts.
- Put the table of contents on the left on desktop, but keep it low-occupation: about 176px wide, small type, no heavy sidebar block. On narrower screens, move the TOC above the document.
- Prefer Chinese prose when the source report is Chinese or the user asks in Chinese.

## Workflow

1. Draft or collect the report as Markdown.
2. Include YAML frontmatter when useful:

```yaml
---
title: "报告标题"
subtitle: "一句话说明"
author: "作者或项目"
date: "YYYY-MM-DD"
output: "report.html"
lang: "zh-CN"
toc: true
---
```

3. Use the bundled renderer:

```bash
python /Users/luoji/.codex/skills/notion-html-report/scripts/render_notion_report.py input.md --output report.html
```

4. Validate the generated HTML locally. Check that headings, TOC anchors, tables, figures, links, and mobile layout are usable.

## Report Writing Rules

- Start with a short executive summary before detailed methods.
- For beginner-facing reports, add plain-language explanations for terminology, data flow, intermediate files, and how to read figures.
- For scientific or engineering reproduction reports, include method, environment, input data, pipeline, results, comparison target, failure modes, and limitations.
- Keep cards and callouts meaningful. Do not turn every paragraph into a card.
- Every figure should have a nearby explanation or caption. For a standalone Markdown image, the renderer uses the image alt text as the caption.
- Every important result table should state what counts as success or failure.

## Supported Markdown Features

The renderer supports headings, paragraphs, unordered and ordered lists, tables, fenced code blocks, blockquotes, images, links, inline code, bold, emphasis, and callouts:

```markdown
> [!NOTE]
> 这里写说明。

> [!RESULT]
> 这里写关键结果。

> [!WARNING]
> 这里写限制或风险。
```

If the report needs advanced Markdown features, create clean basic Markdown first, then extend the renderer only as needed.
