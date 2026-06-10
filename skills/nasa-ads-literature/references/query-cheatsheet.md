# NASA ADS and arXiv Query Cheatsheet

## NASA ADS

Authentication:

- Prefer `~/.ads/dev_key`, one token line, permissions `0600`.
- Environment fallbacks: `ADS_DEV_KEY` or `ADS_API_TOKEN`.
- Requests use `Authorization: Bearer <token>`.

Search endpoint:

- `GET https://api.adsabs.harvard.edu/v1/search/query`
- Common params: `q`, `fl`, `rows`, `start`, `sort`.

Useful fields:

- `bibcode`
- `title`
- `author`
- `year`
- `pub`
- `pubdate`
- `doi`
- `identifier`
- `citation_count`
- `read_count`
- `abstract`
- `keyword`
- `bibstem`
- `doctype`

Common queries:

```text
author:"Gaia Collaboration" year:2024
author:"Loeb, Abraham" title:interstellar
title:"JWST" database:astronomy year:2024
bibstem:ApJ year:2023
property:refereed keyword:"exoplanets"
doi:"10.3847/1538-4357/ac2a3f"
identifier:"arXiv:2401.12345"
```

Useful sorting:

```text
date desc
citation_count desc
read_count desc
first_author asc
```

Bibcode lookup:

```text
bibcode:"2026NatSR..16.2536P"
```

## arXiv

API endpoint:

- `GET https://export.arxiv.org/api/query`

Common params:

- `search_query`
- `id_list`
- `start`
- `max_results`
- `sortBy`: `relevance`, `lastUpdatedDate`, `submittedDate`
- `sortOrder`: `ascending`, `descending`

Astronomy categories:

- `astro-ph.GA`: Astrophysics of Galaxies
- `astro-ph.CO`: Cosmology and Nongalactic Astrophysics
- `astro-ph.EP`: Earth and Planetary Astrophysics
- `astro-ph.HE`: High Energy Astrophysical Phenomena
- `astro-ph.IM`: Instrumentation and Methods for Astrophysics
- `astro-ph.SR`: Solar and Stellar Astrophysics

Common queries:

```text
cat:astro-ph.GA AND all:"Gaia DR3"
cat:astro-ph.CO AND ti:"dark energy"
au:"Planck Collaboration"
abs:"gravitational waves" AND cat:astro-ph.HE
```
