---
name: mineru-pdf-to-md
description: Convert PDF papers or documents into LLM-readable Markdown using the local MinerU installation. Use when the user asks to turn PDFs into Markdown, md, LLM-readable text, structured paper notes, OCR/text extraction output, or when they want arXiv/ADS PDFs prepared for LLM summarization, translation, annotation, or literature review.
---

# MinerU PDF To Markdown

Use this skill to convert local PDFs into Markdown and structured JSON outputs suitable for LLM reading.

## Requirements

- MinerU should be available as `mineru` on PATH.
- Recommended local setup: install MinerU in an isolated Python environment and expose a `mineru` wrapper in `~/.local/bin`.
- If ModelScope models are used, set `MINERU_MODEL_SOURCE=modelscope` in the wrapper or environment so MinerU uses the local ModelScope cache.

## Workflow

1. Identify the PDF path. If the user references an ADS/arXiv paper but no local PDF exists, use the literature download workflow first.
2. Prefer the bundled script:

```bash
python3 ~/.codex/skills/mineru-pdf-to-md/scripts/pdf_to_md.py /absolute/path/to/paper.pdf
```

3. If the user wants a specific output directory, pass it with `--output-dir`.
4. Choose mode:
   - Default: `--method txt --backend pipeline` for LLM-readable text from born-digital PDFs.
   - Use `--method ocr` for scanned/image PDFs.
   - Use `--fast` when the user only needs quick text and can skip formula/table parsing.
   - Keep formulas/tables enabled for scientific papers unless the user asks for speed.
5. After conversion, report the Markdown file path and mention the structured JSON files if useful.
6. For LLM workflows, use the `.md` first. Use `*_content_list.json` or `*_middle.json` when preserving layout, page indices, bounding boxes, or block structure matters.

## Script Examples

```bash
python3 ~/.codex/skills/mineru-pdf-to-md/scripts/pdf_to_md.py paper.pdf
python3 ~/.codex/skills/mineru-pdf-to-md/scripts/pdf_to_md.py paper.pdf --output-dir ./mineru-output
python3 ~/.codex/skills/mineru-pdf-to-md/scripts/pdf_to_md.py scanned.pdf --method ocr
python3 ~/.codex/skills/mineru-pdf-to-md/scripts/pdf_to_md.py paper.pdf --fast
python3 ~/.codex/skills/mineru-pdf-to-md/scripts/pdf_to_md.py paper.pdf --start 0 --end 3
```

The script prints a compact JSON summary with:

- `markdown_files`
- `content_list_files`
- `middle_json_files`
- `output_dir`
- `command`

## Direct MinerU Fallback

If the script is unavailable, run MinerU directly:

```bash
mineru -p /absolute/path/to/paper.pdf -o /absolute/path/to/output-dir -b pipeline -m txt
```

Fast text-only mode:

```bash
mineru -p /absolute/path/to/paper.pdf -o /absolute/path/to/output-dir -b pipeline -m txt --formula false --table false
```

## Validation

After conversion:

```bash
find output-dir -type f \( -name '*.md' -o -name '*content_list.json' -o -name '*middle.json' \) | sort
```

Open the Markdown and verify it contains expected title/body text. If the output is empty or garbled, rerun with `--method ocr` or specify language with `--lang en`, `--lang ch`, etc.

## Output Guidance

In the final response, keep it concise:

- State whether conversion succeeded.
- Give the absolute Markdown path.
- Mention any important caveat, such as OCR mode used, formulas/tables disabled, or pages subset.
- If useful, show a short preview from the Markdown.
