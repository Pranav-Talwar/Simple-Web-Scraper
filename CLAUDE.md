# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run a single test
pytest tests/test_scraper.py::test_parse_article_title -v

# Run the scraper
python scraper.py https://en.wikipedia.org/wiki/Web_scraping
```

## Architecture

Single-file tool: all logic lives in `scraper.py`. The five functions form a linear pipeline:

```
fetch_page(url) → parse_article(html) → save_json(article, filename)
                                ↑
               slugify(title) derives the output filename
```

`main()` orchestrates the pipeline: validates the CLI arg, calls each function in order, attaches `url` and `scraped_at` to the parsed dict before saving.

## Output Schema

The JSON written to disk always has these keys: `title`, `summary`, `sections`, `url`, `scraped_at`. `sections` is a list of `{"heading": str, "content": str}`.

## Wikipedia HTML assumptions

`parse_article` targets Wikipedia's specific DOM structure:
- Title: `<h1 id="firstHeading">`
- Content wrapper: `<div class="mw-parser-output">`
- Summary: paragraphs that are **immediate children** of the content wrapper, stopping at `<div id="toc">`
- Sections: h2/h3 tags (extracting text from inner `<span class="mw-headline">`) and their following paragraphs via `find_all` (all descendants, not just immediate children)

## Testing

HTTP calls are mocked at `scraper.requests.get`. File I/O tests use pytest's `tmp_path` fixture. No tests make real network requests.
