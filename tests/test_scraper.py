import json
import pytest
import requests
from pathlib import Path
from unittest.mock import patch, MagicMock

from scraper import slugify, fetch_page, parse_article, save_json, main


def test_slugify_basic():
    assert slugify("Python (programming language)") == "python_programming_language"


def test_slugify_spaces():
    assert slugify("Web scraping") == "web_scraping"


def test_slugify_hyphens_preserved():
    assert slugify("Test-driven development") == "test-driven_development"


def test_slugify_multiple_spaces():
    assert slugify("Hello  World") == "hello__world"


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
