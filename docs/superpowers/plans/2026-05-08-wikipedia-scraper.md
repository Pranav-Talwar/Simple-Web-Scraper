# Wikipedia Content Extractor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CLI tool that takes a Wikipedia URL, extracts structured content with BeautifulSoup, and saves it as a JSON file.

**Architecture:** Single `scraper.py` file with five focused functions wired together by `main()`. Tests live in `tests/test_scraper.py` and use `pytest` with `unittest.mock` for HTTP calls and `tmp_path` for file I/O.

**Tech Stack:** Python 3.8+, `requests`, `beautifulsoup4`, `pytest`

---

## File Map

| File | Role |
|---|---|
| `scraper.py` | Main script — all logic and CLI entry point |
| `tests/test_scraper.py` | Unit tests for every function |
| `requirements.txt` | Pinned dependencies |

---

### Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `tests/__init__.py`
- Create: `tests/test_scraper.py` (scaffold only)

- [ ] **Step 1: Create requirements.txt**

```
requests==2.31.0
beautifulsoup4==4.12.3
pytest==8.2.0
```

- [ ] **Step 2: Install dependencies**

Run:
```bash
pip install -r requirements.txt
```

Expected: All packages install without errors.

- [ ] **Step 3: Create test scaffold**

Create `tests/__init__.py` (empty file).

Create `tests/test_scraper.py`:

```python
import pytest
```

- [ ] **Step 4: Verify pytest runs**

Run:
```bash
pytest tests/ -v
```

Expected: `no tests ran` — 0 errors, collection works.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt tests/__init__.py tests/test_scraper.py
git commit -m "chore: project setup with dependencies and test scaffold"
```

---

### Task 2: `slugify` — Convert Title to Filename

**Files:**
- Create: `scraper.py` (initial)
- Modify: `tests/test_scraper.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_scraper.py`:

```python
from scraper import slugify

def test_slugify_basic():
    assert slugify("Python (programming language)") == "python_programming_language"

def test_slugify_spaces():
    assert slugify("Web scraping") == "web_scraping"

def test_slugify_hyphens_preserved():
    assert slugify("Test-driven development") == "test-driven_development"

def test_slugify_multiple_spaces():
    assert slugify("Hello  World") == "hello__world"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
pytest tests/test_scraper.py -v
```

Expected: `ImportError: cannot import name 'slugify' from 'scraper'`

- [ ] **Step 3: Create `scraper.py` with `slugify`**

Create `scraper.py`:

```python
import re
import json
import sys
from datetime import datetime

import requests
from bs4 import BeautifulSoup


def slugify(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = slug.replace(" ", "_")
    return slug
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_scraper.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scraper.py tests/test_scraper.py
git commit -m "feat: add slugify for safe filename generation"
```

---

### Task 3: `fetch_page` — HTTP Request

**Files:**
- Modify: `scraper.py`
- Modify: `tests/test_scraper.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_scraper.py`:

```python
from unittest.mock import patch, MagicMock
from scraper import fetch_page

def test_fetch_page_returns_html():
    mock_response = MagicMock()
    mock_response.text = "<html><body>Hello</body></html>"
    mock_response.raise_for_status = MagicMock()

    with patch("scraper.requests.get", return_value=mock_response) as mock_get:
        result = fetch_page("https://en.wikipedia.org/wiki/Python")
        mock_get.assert_called_once_with(
            "https://en.wikipedia.org/wiki/Python",
            headers={"User-Agent": "wikipedia-scraper/1.0"},
            timeout=10,
        )
        assert result == "<html><body>Hello</body></html>"

def test_fetch_page_raises_on_http_error():
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("404")

    with patch("scraper.requests.get", return_value=mock_response):
        with pytest.raises(requests.HTTPError):
            fetch_page("https://en.wikipedia.org/wiki/DoesNotExist")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
pytest tests/test_scraper.py::test_fetch_page_returns_html tests/test_scraper.py::test_fetch_page_raises_on_http_error -v
```

Expected: `ImportError: cannot import name 'fetch_page'`

- [ ] **Step 3: Implement `fetch_page` in `scraper.py`**

Add after `slugify`:

```python
def fetch_page(url: str) -> str:
    headers = {"User-Agent": "wikipedia-scraper/1.0"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.text
```

Also add `import requests` at top if not present (it's already there from Task 2).

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_scraper.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scraper.py tests/test_scraper.py
git commit -m "feat: add fetch_page with user-agent header and error propagation"
```

---

### Task 4: `parse_article` — HTML Parsing

**Files:**
- Modify: `scraper.py`
- Modify: `tests/test_scraper.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_scraper.py`:

```python
from scraper import parse_article

SAMPLE_HTML = """
<html>
<body>
<h1 id="firstHeading">Python (programming language)</h1>
<div id="mw-content-text">
  <div class="mw-parser-output">
    <p>Python is a high-level programming language.</p>
    <p>It was created by Guido van Rossum.</p>
    <div id="toc"></div>
    <h2><span class="mw-headline">History</span></h2>
    <p>Python was conceived in the late 1980s.</p>
    <h2><span class="mw-headline">Design</span></h2>
    <p>Python emphasizes code readability.</p>
  </div>
</div>
</body>
</html>
"""

def test_parse_article_title():
    result = parse_article(SAMPLE_HTML)
    assert result["title"] == "Python (programming language)"

def test_parse_article_summary():
    result = parse_article(SAMPLE_HTML)
    assert "Python is a high-level programming language." in result["summary"]
    assert "It was created by Guido van Rossum." in result["summary"]

def test_parse_article_sections():
    result = parse_article(SAMPLE_HTML)
    assert len(result["sections"]) == 2
    assert result["sections"][0]["heading"] == "History"
    assert "conceived" in result["sections"][0]["content"]
    assert result["sections"][1]["heading"] == "Design"
    assert "readability" in result["sections"][1]["content"]

def test_parse_article_missing_title_raises():
    result = parse_article("<html><body></body></html>")
    assert result["title"] == ""
    assert result["summary"] == ""
    assert result["sections"] == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
pytest tests/test_scraper.py::test_parse_article_title tests/test_scraper.py::test_parse_article_summary tests/test_scraper.py::test_parse_article_sections tests/test_scraper.py::test_parse_article_missing_title_raises -v
```

Expected: `ImportError: cannot import name 'parse_article'`

- [ ] **Step 3: Implement `parse_article` in `scraper.py`**

Add after `fetch_page`:

```python
def parse_article(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    title_tag = soup.find("h1", id="firstHeading")
    title = title_tag.get_text(strip=True) if title_tag else ""

    summary_parts = []
    content_div = soup.find("div", class_="mw-parser-output")
    if content_div:
        for tag in content_div.children:
            if hasattr(tag, "get") and tag.get("id") == "toc":
                break
            if getattr(tag, "name", None) == "p":
                text = tag.get_text(strip=True)
                if text:
                    summary_parts.append(text)
    summary = " ".join(summary_parts)

    sections = []
    if content_div:
        current_heading = None
        current_paragraphs = []
        for tag in content_div.find_all(["h2", "h3", "p"]):
            if tag.name in ("h2", "h3"):
                if current_heading:
                    sections.append({
                        "heading": current_heading,
                        "content": " ".join(current_paragraphs),
                    })
                headline = tag.find(class_="mw-headline")
                current_heading = headline.get_text(strip=True) if headline else tag.get_text(strip=True)
                current_paragraphs = []
            elif tag.name == "p" and current_heading:
                text = tag.get_text(strip=True)
                if text:
                    current_paragraphs.append(text)
        if current_heading:
            sections.append({
                "heading": current_heading,
                "content": " ".join(current_paragraphs),
            })

    return {"title": title, "summary": summary, "sections": sections}
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_scraper.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scraper.py tests/test_scraper.py
git commit -m "feat: add parse_article to extract title, summary, and sections"
```

---

### Task 5: `save_json` — File Output

**Files:**
- Modify: `scraper.py`
- Modify: `tests/test_scraper.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_scraper.py`:

```python
import json
from pathlib import Path
from scraper import save_json

def test_save_json_writes_file(tmp_path):
    data = {"title": "Test", "sections": []}
    output_path = tmp_path / "output.json"
    save_json(data, str(output_path))
    assert output_path.exists()
    loaded = json.loads(output_path.read_text(encoding="utf-8"))
    assert loaded["title"] == "Test"

def test_save_json_is_valid_json(tmp_path):
    data = {"title": "Test", "sections": [{"heading": "A", "content": "B"}]}
    output_path = tmp_path / "out.json"
    save_json(data, str(output_path))
    loaded = json.loads(output_path.read_text(encoding="utf-8"))
    assert loaded["sections"][0]["heading"] == "A"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
pytest tests/test_scraper.py::test_save_json_writes_file tests/test_scraper.py::test_save_json_is_valid_json -v
```

Expected: `ImportError: cannot import name 'save_json'`

- [ ] **Step 3: Implement `save_json` in `scraper.py`**

Add after `parse_article`:

```python
def save_json(data: dict, filepath: str) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_scraper.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scraper.py tests/test_scraper.py
git commit -m "feat: add save_json for writing structured output to disk"
```

---

### Task 6: `main` — CLI Entry Point and Error Handling

**Files:**
- Modify: `scraper.py`
- Modify: `tests/test_scraper.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_scraper.py`:

```python
from unittest.mock import patch, MagicMock
from scraper import main

def test_main_no_args_exits(capsys):
    with patch("sys.argv", ["scraper.py"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Usage" in captured.out

def test_main_non_wikipedia_url_exits(capsys):
    with patch("sys.argv", ["scraper.py", "https://google.com/something"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Wikipedia" in captured.out

def test_main_success(tmp_path):
    mock_html = """
    <html><body>
    <h1 id="firstHeading">Test Article</h1>
    <div id="mw-content-text"><div class="mw-parser-output">
    <p>Summary text.</p>
    </div></div>
    </body></html>
    """
    with patch("sys.argv", ["scraper.py", "https://en.wikipedia.org/wiki/Test"]), \
         patch("scraper.fetch_page", return_value=mock_html), \
         patch("scraper.save_json") as mock_save:
        main()
        assert mock_save.called
        call_args = mock_save.call_args[0]
        data = call_args[0]
        assert data["title"] == "Test Article"
        assert data["url"] == "https://en.wikipedia.org/wiki/Test"
        assert "scraped_at" in data
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
pytest tests/test_scraper.py::test_main_no_args_exits tests/test_scraper.py::test_main_non_wikipedia_url_exits tests/test_scraper.py::test_main_success -v
```

Expected: `ImportError: cannot import name 'main'`

- [ ] **Step 3: Implement `main` in `scraper.py`**

Add at the end of `scraper.py`:

```python
def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scraper.py <wikipedia-url>")
        sys.exit(1)

    url = sys.argv[1]
    if "wikipedia.org" not in url:
        print("Error: URL must be a Wikipedia URL (e.g. https://en.wikipedia.org/wiki/...)")
        sys.exit(1)

    try:
        html = fetch_page(url)
    except requests.HTTPError as e:
        print(f"Error fetching page: {e}")
        sys.exit(1)

    article = parse_article(html)
    article["url"] = url
    article["scraped_at"] = datetime.now().isoformat(timespec="seconds")

    if not article["title"]:
        print("Error: Could not extract article content. Is this a valid Wikipedia article URL?")
        sys.exit(1)

    filename = slugify(article["title"]) + ".json"
    save_json(article, filename)
    print(f"Saved: {filename}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run all tests to verify they pass**

Run:
```bash
pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 5: Manual smoke test**

Run:
```bash
python scraper.py https://en.wikipedia.org/wiki/Web_scraping
```

Expected:
```
Saved: web_scraping.json
```

Open `web_scraping.json` and verify it contains `title`, `summary`, `sections`, `url`, and `scraped_at`.

- [ ] **Step 6: Commit**

```bash
git add scraper.py tests/test_scraper.py
git commit -m "feat: add main CLI entry point with argument validation and error handling"
```

---

## Done

The tool is complete when:
- `pytest tests/ -v` shows all green
- `python scraper.py <url>` produces a valid JSON file for any Wikipedia article URL
