---
name: awesome-ai-research-writing
description: "Use this skill for AI-assisted academic research writing tasks based on Leey21/awesome-ai-research-writing: Chinese/English translation, LaTeX or Word-ready paper prose, English or Chinese polishing, shortening, expansion, logic checks, reducing obvious AI writing style, figure/table captions, experiment analysis, reviewer-style manuscript critique, and model/tool selection for research writing. Prefer this skill when the user asks to write, translate, polish, humanize, review, or structure research paper text, especially in Chinese-English academic writing workflows."
---

# Awesome AI Research Writing

## Overview

This skill wraps the upstream `Leey21/awesome-ai-research-writing` prompt collection for Codex use. It is not a native upstream Codex skill repository; the upstream material is preserved in `references/upstream-readme.md` and should be loaded selectively when an exact template is needed.

Use the user's requested medium and language as the first routing signal:
- LaTeX: preserve math and LaTeX syntax, escape special characters when producing LaTeX.
- Word/plain text: avoid Markdown and LaTeX escaping unless the user explicitly asks for it.
- Chinese input to English paper prose: produce polished academic English plus a Chinese back-translation when useful.
- English paper prose to Chinese: prefer faithful translation for understanding unless the user asks for polishing.

## Task Routing

Read only the relevant section of `references/upstream-readme.md` when exact constraints are needed. Useful anchors include:
- `中转英-latex`: Chinese draft to English LaTeX academic prose.
- `英转中-latex`: English LaTeX to faithful Chinese reading translation.
- `中转英-word`: Chinese draft to Word-ready English academic prose.
- `中转中-word`: Chinese draft to formal Chinese academic prose.
- `缩写`: lightly shorten English LaTeX without losing information.
- `扩写`: lightly expand English LaTeX by making implicit logic explicit.
- `表达润色（英文论文）`: polish English paper text.
- `表达润色（中文论文）`: polish Chinese paper text.
- `逻辑检查`: check argument flow and logical gaps.
- `去 AI 味（LaTeX 英文）` and `去 AI 味（Word 中文）`: reduce obvious AI style while preserving meaning.
- `论文架构图`: plan a research paper concept/framework figure.
- `实验绘图推荐`: suggest appropriate academic plots for results.
- `生成图的标题` and `生成表的标题`: write figure/table captions.
- `实验分析`: write or improve experimental analysis.
- `论文整体以 Reviewer 视角进行审视`: critique a paper like a reviewer.
- `模型选择`: advise which model/tool is suitable for a writing task.

## Response Discipline

- Match the output format to the destination. For Word-ready outputs, return clean plain text. For LaTeX outputs, return valid LaTeX snippets and avoid Markdown decoration.
- Preserve technical claims, numbers, formulas, citations, labels, and terminology unless the user asks to rewrite structure.
- Do not invent results, citations, methods, or paper claims. Mark unknowns explicitly or ask for the missing source material when needed.
- For translation/polishing workflows, keep the scientific meaning stricter than stylistic elegance.
- When the user asks for review, lead with concrete issues and revision suggestions rather than generic praise.
- When the user supplies a target venue or journal style, adapt tone, structure, and terminology to that target.

## Recommended Workflow

1. Identify the requested task, target medium, target language, and expected output shape.
2. If exact prompt constraints matter, load the relevant section from `references/upstream-readme.md` instead of the whole file.
3. Apply the template's constraints pragmatically to the user's concrete text.
4. Self-check for formatting mistakes, untranslated text, altered scientific meaning, and unsupported claims before responding.

## Source

Upstream project: `https://github.com/Leey21/awesome-ai-research-writing`

Local reference copy: `references/upstream-readme.md`
