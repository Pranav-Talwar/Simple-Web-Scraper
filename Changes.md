# Changes

## What Was Broken

| Problem | Symptom |
|---|---|
| Some Wikipedia articles (e.g. "Film") returned empty summary and sections | `film.json` had `"summary": ""` and `"sections": []` |
| Sections like "References", "See also", "Further reading" had empty content | Those sections only contain lists, not paragraphs |
| Citation numbers cluttered the extracted text | Text like `"Python[1] is a language[2][3]"` in output |

---

## Fix 1 — Smarter Content Detection

**Problem:** The scraper only looked for `<div class="mw-parser-output">`. Some Wikipedia articles (especially high-traffic ones) wrap their content differently — either inside a `<div id="mw-content-text">` or a language-direction wrapper like `<div class="mw-content-ltr">`. This caused the "Film" article to return empty results.

**Fix:** Added a new `find_content_div()` function. Some Wikipedia pages (like "Film") have **two** `mw-parser-output` divs — a small empty one in the page head and the real article content div inside `mw-content-text`. The old code always grabbed the first one (wrong). The fix searches inside `mw-content-text` first, which scopes directly to the article body, then falls back to a full-page search for simpler layouts.

Also changed summary extraction from iterating **immediate children** (which missed nested paragraphs) to using `find_all(["p", "h2"])` which searches recursively — finding paragraphs regardless of nesting depth, stopping at the first `<h2>` heading.

---

## Fix 2 — Collect List Items, Not Just Paragraphs

**Problem:** Wikipedia sections like "Specific theories of film" use `<ul>/<li>` lists instead of `<p>` paragraphs. The old scraper only collected `<p>` tags, so those sections came out empty.

**Fix:** The section extraction loop now also processes `<ul>` and `<ol>` tags. Each list's `<li>` items are joined with semicolons and added to the section content. Only top-level lists are processed (nested lists are skipped to avoid counting items twice).

---

## Fix 3 — Filter Boilerplate Sections

**Problem:** Sections like "References", "See also", "External links", and "Further reading" are navigation aids — not article content. They were being included as sections with mostly empty or noisy content.

**Fix:** Added a `BOILERPLATE_SECTIONS` constant listing section names to skip. When a heading matches this list (case-insensitive), the entire section is excluded from the output.

Sections filtered out:
- References
- External links
- See also
- Notes
- Further reading
- Bibliography
- Footnotes
- Citations
- Sources

---

## Fix 4 — Strip Citation Markers

**Problem:** Wikipedia text contains citation markers like `[1]`, `[23]`, `[citation needed]`, `[note 1]`, `[a]`. These appear throughout extracted text and make it harder to read.

**Fix:** Added a `strip_citations()` function that removes anything inside square brackets up to 20 characters long. This covers all Wikipedia citation formats. Applied to both summary and section content.

**Before:**
```
"Python[1] is a high-level, general-purpose programming language.[2][3]"
```

**After:**
```
"Python is a high-level, general-purpose programming language."
```
