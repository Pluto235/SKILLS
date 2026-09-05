---
name: nasa-ads-literature
description: Search and retrieve astronomy and astrophysics literature from NASA ADS and arXiv. Use when the user asks to search ADS, query ADS bibcodes, find recent arXiv papers, retrieve astronomy paper metadata, get citation counts, export BibTeX, monitor new papers, or download legally available open-access PDFs.
---

# NASA ADS Literature

Use this skill for astronomy and astrophysics literature discovery through NASA ADS and arXiv.

Never place API tokens in prompts, command arguments, source files, logs, or final answers. ADS authentication must come from `ADS_DEV_KEY`, `ADS_API_TOKEN`, or `~/.ads/dev_key`.

## Workflow

1. Prefer ADS when the user needs peer-reviewed metadata, citation counts, bibcodes, DOI lookup, author searches, publication filters, or BibTeX.
2. Prefer arXiv when the user asks for latest preprints, `astro-ph.*` categories, arXiv IDs, or directly downloadable PDFs.
3. For open PDFs, prefer arXiv PDF URLs and other openly available source links. Do not bypass publisher access controls.
4. For reproducible literature work, report the exact query, source, date, result count, and filters used.
5. For broad review requests, combine this skill with `literature-review` or `academic-research-suite`.

## Scripts

Run scripts from this skill directory:

```bash
python3 scripts/ads_search.py --query 'author:"Gaia Collaboration" year:2024' --rows 10
python3 scripts/ads_search.py --bibcode '2026NatSR..16.2536P' --format json
python3 scripts/ads_search.py --query 'title:"JWST" database:astronomy year:2024' --format bibtex --rows 5
python3 scripts/arxiv_search.py --query 'cat:astro-ph.GA AND all:"Gaia DR3"' --rows 10
python3 scripts/fetch_open_pdf.py --arxiv 2401.12345 --output-dir ./papers
```

`ads_search.py` outputs compact Markdown by default. Use `--format json` for downstream processing and `--format bibtex` for references.

`arxiv_search.py` uses the public arXiv export API and needs no API key.

`fetch_open_pdf.py` downloads only openly reachable PDFs from arXiv or explicit PDF URLs.

## Query Guidance

Read `references/query-cheatsheet.md` when constructing ADS or arXiv queries, especially for author, year, bibstem, citation sorting, and arXiv category searches.

## Output Discipline

For each result set, include:

- source: ADS or arXiv
- exact query
- retrieval date
- total results when available
- returned fields and row count
- links: ADS, DOI, arXiv, or PDF when available

Mark preprints as preprints. Do not imply a paper is peer-reviewed solely because it appears in arXiv.
