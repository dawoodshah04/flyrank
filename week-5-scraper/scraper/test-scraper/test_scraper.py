import pytest
from utils import absolute_url, clean_text, normalize_price


def test_price_normalization():
    assert normalize_price("£51.77") == 51.77


def test_relative_url():
    result = absolute_url(
        "../book/test/index.html",
        "https://books.toscrape.com/catalogue/page-1.html",
    )

    assert result == (
        "https://books.toscrape.com/book/test/index.html"
    )


def test_clean_text():
    assert clean_text(
        "   hello     world\n"
    ) == "hello world"


def test_missing_description():
    assert clean_text(None) is None


def test_malformed_price():
    with pytest.raises(ValueError):
        normalize_price("not a price")


def test_duplicate_urls():
    urls = [
        "https://example.com/a",
        "https://example.com/a",
        "https://example.com/b",
    ]

    unique = list(dict.fromkeys(urls))

    assert len(unique) == 2