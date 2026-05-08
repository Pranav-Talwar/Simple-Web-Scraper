# Wikipedia Content Extractor

A command-line tool that scrapes a Wikipedia article and saves its content as a structured JSON file.

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Usage

```bash
python scraper.py https://en.wikipedia.org/wiki/Web_scraping
```

This produces a file called `web_scraping.json` in the current directory.

---

## Output Format

```json
{
  "title": "Web scraping",
  "summary": "Web scraping is the process of extracting data from websites...",
  "sections": [
    { "heading": "Techniques", "content": "..." },
    { "heading": "Legal issues", "content": "..." }
  ],
  "url": "https://en.wikipedia.org/wiki/Web_scraping",
  "scraped_at": "2026-05-08T14:32:00"
}
```

| Field | Description |
|---|---|
| `title` | Article title |
| `summary` | Introductory paragraphs before the first section heading |
| `sections` | Each section heading paired with its text content (paragraphs and lists). Boilerplate sections like References and See Also are excluded. Citation markers like `[1]` are stripped. |
| `url` | The URL you passed in |
| `scraped_at` | ISO 8601 timestamp of when the scrape ran |

---

## How It Works

The tool is built around five functions that form a pipeline:

```
URL → fetch_page → parse_article → save_json → article.json
                                      ↑
                          slugify(title) → filename
```

### 1. `fetch_page(url)`

Makes an HTTP GET request to the Wikipedia URL using the `requests` library.

- Sets a `User-Agent` header (`wikipedia-scraper/1.0`) so Wikipedia can identify the request
- Enforces a 10-second timeout to avoid hanging
- Calls `raise_for_status()` which throws an exception for any 4xx or 5xx HTTP error

```python
def fetch_page(url: str) -> str:
    headers = {"User-Agent": "wikipedia-scraper/1.0"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.text  # raw HTML string
```

---

### 2. `parse_article(html)`

Takes the raw HTML string and uses **BeautifulSoup** to extract three things from Wikipedia's page structure.

#### Title

Wikipedia always puts the article title in `<h1 id="firstHeading">`:

```html
<h1 id="firstHeading">Web scraping</h1>
```

```python
title_tag = soup.find("h1", id="firstHeading")
title = title_tag.get_text(strip=True) if title_tag else ""
```

#### Summary

The summary is the introductory text before the first section heading. The function searches for all `<p>` tags inside `<div class="mw-parser-output">`, stopping at the first `<h2>`. Paragraphs inside tables (infoboxes) are skipped. All collected paragraphs are joined with a space into a single `summary` string.

#### Sections

Each `<h2>` or `<h3>` heading starts a new section. Wikipedia wraps heading text in `<span class="mw-headline">` — the function extracts text from there when present, falling back to the raw heading text otherwise:

```html
<h2><span class="mw-headline">History</span></h2>
<p>Python was conceived in the late 1980s.</p>
<p>Guido van Rossum started the project...</p>
```

This becomes:
```json
{ "heading": "History", "content": "Python was conceived in the late 1980s. Guido van Rossum started the project..." }
```

The function uses a simple accumulator pattern — it keeps track of the current heading and collects paragraphs and list items (`<ul>`, `<ol>`) until the next heading is found.

---

### 3. `slugify(title)`

Converts the article title to a safe filename:

1. Lowercase everything
2. Remove any character that isn't a word character (`\w`), space, or hyphen
3. Replace spaces with underscores

```
"Python (programming language)"
  → "python (programming language)"   # lowercase
  → "python programming language"     # remove parentheses
  → "python_programming_language"     # spaces → underscores
```

The output filename is `slugify(title) + ".json"`.

---

### 4. `save_json(data, filepath)`

Writes the article dict to disk as pretty-printed JSON:

- `indent=2` — human-readable indentation
- `ensure_ascii=False` — preserves non-ASCII characters (accented letters, etc.) instead of escaping them

---

### 5. `main()`

The CLI entry point that wires everything together:

```
1. Check that a URL was passed as a command-line argument
2. Validate that the URL contains "wikipedia.org"
3. Fetch the page HTML
4. Parse the HTML into a structured dict
5. Attach `url` and `scraped_at` to the dict
6. Check that a title was actually extracted (catches non-article URLs)
7. Derive the output filename from the title
8. Save to JSON
9. Print confirmation
```

Error handling at each step prints a clear message and exits with code `1`.

---

## Running Tests

```bash
pytest tests/ -v
```

Tests cover all five functions. HTTP calls are mocked so no real network requests are made during testing.

To run a single test:

```bash
pytest tests/test_scraper.py::test_parse_article_sections -v
```
