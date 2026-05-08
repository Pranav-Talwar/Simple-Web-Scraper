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


def fetch_page(url: str) -> str:
    headers = {"User-Agent": "wikipedia-scraper/1.0"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.text


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


def save_json(data: dict, filepath: str) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


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
