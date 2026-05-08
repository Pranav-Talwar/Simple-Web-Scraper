import re
import json
import sys
from datetime import datetime

import requests
from bs4 import BeautifulSoup


BOILERPLATE_SECTIONS = {
    "references", "external links", "see also", "notes", "further reading",
    "bibliography", "footnotes", "citations", "sources"
}


def slugify(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = slug.replace(" ", "_")
    return slug


def strip_citations(text: str) -> str:
    return re.sub(r"\[[^\]]{1,20}\]", "", text).strip()


def find_content_div(soup: BeautifulSoup):
    wrapper = soup.find("div", id="mw-content-text")
    if wrapper:
        content = wrapper.find("div", class_="mw-parser-output")
        if content:
            return content
    return soup.find("div", class_="mw-parser-output")


def parse_article(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    title_tag = soup.find("h1", id="firstHeading")
    title = title_tag.get_text(strip=True) if title_tag else ""

    content_div = find_content_div(soup)

    if not content_div:
        return {"title": title, "summary": "", "sections": []}

    summary_parts = []
    for tag in content_div.find_all(["p", "h2"]):
        if tag.name == "h2":
            break
        if tag.name == "p":
            if tag.find_parent("table"):
                continue
            text = strip_citations(tag.get_text(strip=True))
            if text:
                summary_parts.append(text)
    summary = " ".join(summary_parts)

    sections = []
    current_heading = None
    current_content_parts = []
    skip_current = False

    for tag in content_div.find_all(["h2", "h3", "p", "ul", "ol"]):

        if tag.name in ("h2", "h3"):
            if current_heading and not skip_current:
                sections.append({
                    "heading": current_heading,
                    "content": " ".join(current_content_parts),
                })
            headline = tag.find(class_="mw-headline")
            heading_text = headline.get_text(strip=True) if headline else tag.get_text(strip=True)
            skip_current = heading_text.lower() in BOILERPLATE_SECTIONS
            current_heading = heading_text
            current_content_parts = []

        elif tag.name == "p" and current_heading and not skip_current:
            if tag.find_parent("table"):
                continue
            text = strip_citations(tag.get_text(strip=True))
            if text:
                current_content_parts.append(text)

        elif tag.name in ("ul", "ol") and current_heading and not skip_current:
            if tag.find_parent(["ul", "ol"]):
                continue
            items = [
                strip_citations(li.get_text(strip=True))
                for li in tag.find_all("li", recursive=False)
            ]
            items = [i for i in items if i]
            if items:
                current_content_parts.append("; ".join(items))

    if current_heading and not skip_current:
        sections.append({
            "heading": current_heading,
            "content": " ".join(current_content_parts),
        })

    return {"title": title, "summary": summary, "sections": sections}


def fetch_page(url: str) -> str:
    headers = {"User-Agent": "wikipedia-scraper/1.0"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.text


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
