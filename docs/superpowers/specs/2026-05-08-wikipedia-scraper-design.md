# Wikipedia Content Extractor — Design

**Date:** 2026-05-08  
**Status:** Approved

---

## Overview

A single-file Python CLI tool that accepts a Wikipedia article URL, extracts structured content using BeautifulSoup, and saves the result to a JSON file.

---

## Usage

```bash
python scraper.py https://en.wikipedia.org/wiki/Python_(programming_language)
```

Output file: `python_programming_language.json` (derived from article title — lowercased, spaces replaced with underscores, special characters stripped)

---

## Extracted Fields

| Field | Description |
|---|---|
| `title` | Article title from the `<h1>` tag |
| `summary` | Paragraphs before the table of contents |
| `sections` | List of `{ "heading": str, "content": str }` objects |
| `url` | Source URL passed by the user |
| `scraped_at` | ISO 8601 timestamp of when the scrape ran |

---

## Architecture

Single file: `scraper.py`

**Functions:**
- `fetch_page(url)` — makes HTTP GET request, returns raw HTML
- `parse_article(html)` — uses BeautifulSoup to extract title, summary, sections
- `slugify(title)` — converts article title to a safe filename
- `save_json(data, filename)` — writes dict to a `.json` file
- `main()` — CLI entry point, wires everything together

---

## Libraries

- `requests` — HTTP fetching
- `beautifulsoup4` — HTML parsing (using built-in `html.parser`)

Install: `pip install requests beautifulsoup4`

---

## Error Handling

| Scenario | Behavior |
|---|---|
| No URL argument provided | Print usage message and exit with code 1 |
| URL is not a Wikipedia URL | Print clear error and exit |
| HTTP error (4xx, 5xx) | Print status code and exit |
| Page content not found | Print error and exit |
| File write failure | Print error and exit |

---

## Output Example

```json
{
  "title": "Python (programming language)",
  "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
  "scraped_at": "2026-05-08T14:32:00",
  "summary": "Python is a high-level, general-purpose programming language...",
  "sections": [
    { "heading": "History", "content": "Guido van Rossum began working on Python in the late 1980s..." },
    { "heading": "Design philosophy", "content": "Python is a multi-paradigm programming language..." }
  ]
}
```
