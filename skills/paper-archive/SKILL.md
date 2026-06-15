---
name: paper-archive
description: Archive academic papers into the user's hard-coded IDEA paper accumulation library. Use when the user gives an arXiv link, arXiv ID, DOI, paper title, abstract snippet, or any searchable paper clue and asks to archive, accumulate, remember, save to paper library, add to paper archived, or otherwise build their paper collection.
---

# Paper Archive

## Fixed Destination

Always append paper records to:

`/Users/luoji/Documents/projects/IDEA/paper_archived.md`

Treat this path as hard-coded. Create the file if it is missing, using `# Paper Archived` as the top-level heading.

## Workflow

1. Identify the paper from the user's clue.
   - Prefer official arXiv pages/API for arXiv papers.
   - If the clue is only a title or fuzzy text, search enough to determine the exact paper before writing.
   - If multiple papers plausibly match, ask one concise clarification question.

2. Fetch enough metadata and abstract-level detail.
   - Preserve original title, arXiv ID, link, categories, publication date, authors when available, DOI, journal reference, and comments/status when visible.
   - Do not invent missing metadata. If publication or journal status is not visible, write `投稿/接收/期刊信息: 未显示`.

3. Append one Markdown entry to the fixed file.
   - Keep the library useful for later research, not just a citation dump.
   - Use a date heading for the archive date if it is not already present.
   - If the paper already exists by arXiv ID, DOI, or exact title, update the existing entry only if the user asks; otherwise report that it is already archived.

4. Verify the file after writing.
   - Read back the appended section or search for the arXiv ID/title.
   - Report the absolute file link in the final answer.

## Entry Format

Use this structure unless the existing file has clearly evolved into a better local pattern:

```markdown
## YYYY-MM-DD

### Original Paper Title

- arXiv ID: `...`
- DOI: `...`
- 链接: [...]
- 分类: `...`
- 发布日期: `...`
- 作者: ...
- 匹配主题: ...
- 投稿/接收/期刊信息: ...

**积累理由**

...

**核心问题**

...

**数据与方法**

...

**主要结论**

...

**对我可能有用的点**

- ...

**后续跟进问题**

- ...
```

If a field is unavailable, omit it when it is not central, except for publication/journal status, where the explicit `未显示` line is useful.

## Summary Style

Write in Chinese by default. Keep the original paper title in English. Explain:

- the scientific problem;
- the data, instrument, sample, model, or method;
- the main result or claim;
- why the paper may matter for the user's research accumulation;
- concrete follow-up questions that can become reading notes or project ideas.

