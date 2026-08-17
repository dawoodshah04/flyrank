from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from pydantic import ValidationError

from models import Book, RawBook
from utils import absolute_url, clean_text, normalize_price

BASE_URL = "https://books.toscrape.com/"
CATALOGUE_URL = f"{BASE_URL}catalogue/page-1.html"
CACHE_DIR = Path("cache")
OUTPUT_DIR = Path("output")
USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/dawoodshah04/flyrank)"
REQUEST_DELAY = 0.5
TIMEOUT = 10


class Scraper:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
        self.last_req_time: float | None = None
        self.stats = {"pages_fetched": 0, "cache_hits": 0}

    def polite_wait(self) -> None:
        if self.last_req_time is not None:
            elapsed = time.monotonic() - self.last_req_time
            if elapsed < REQUEST_DELAY:
                time.sleep(REQUEST_DELAY - elapsed)

    def fetch(self, url: str, cache_file: Path) -> str:
        if cache_file.exists():
            self.stats["cache_hits"] += 1
            print(f"CACHE HIT {url}")
            return cache_file.read_text(encoding="utf-8")

        self.polite_wait()
        self.last_req_time = time.monotonic()
        try:
            response = self.session.get(url, timeout=TIMEOUT)
            self.stats["pages_fetched"] += 1
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(f"Request failed for {url}: {exc}") from exc

        html = response.text
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(html, encoding="utf-8")
        print(f"FETCH {url} status={response.status_code} size={len(html)} bytes")
        return html

    def catalogue_cache_path(self, page_number: int) -> Path:
        return CACHE_DIR / f"catalogue-page-{page_number}.html"

    def detail_cache_path(self, index: int) -> Path:
        return CACHE_DIR / f"book-{index:03d}.html"

    def discover_books(self) -> list[tuple[str, str]]:
        current_url = CATALOGUE_URL
        discovered: list[tuple[str, str]] = []
        pages_read = 0

        for page_number in range(1, 4):
            html = self.fetch(current_url, self.catalogue_cache_path(page_number))
            soup = BeautifulSoup(html, "html.parser")
            pages_read = page_number
            for article in soup.select("article.product_pod"):
                link = article.select_one("h3 a")
                href = link.get("href") if link else None
                if href:
                    discovered.append((absolute_url(href, current_url), current_url))
            next_link = soup.select_one("li.next a")
            if not next_link or not next_link.get("href"):
                break
            current_url = absolute_url(next_link["href"], current_url)

        unique: dict[str, str] = {}
        for product_url, source_page in discovered:
            unique.setdefault(product_url, source_page)
        print(f"catalogue_pages={pages_read} discovered={len(discovered)} unique_urls={len(unique)}")
        return list(unique.items())

    def extract_book(self, url: str, source_page: str, cache_file: Path) -> RawBook:
        html = self.fetch(url, cache_file)
        soup = BeautifulSoup(html, "html.parser")
        product = soup.select_one("article.product_page")
        if product is None:
            raise ValueError("Product article not found")

        title_element = product.select_one("h1")
        price_element = product.select_one("p.price_color")
        availability_element = product.select_one("p.instock")
        rating_element = product.select_one("p.star-rating")
        if not title_element:
            raise ValueError("Title not found")
        if not price_element:
            raise ValueError("Price not found")
        if not availability_element:
            raise ValueError("Availability not found")
        if not rating_element:
            raise ValueError("Rating not found")

        rating = next((name for name in ("One", "Two", "Three", "Four", "Five") if name in rating_element.get("class", [])), None)
        if rating is None:
            raise ValueError("Rating not found")

        description = None
        heading = product.select_one("#product_description")
        if heading:
            description_element = heading.find_next_sibling("p")
            if description_element:
                description = clean_text(description_element.get_text())

        return RawBook(
            title=clean_text(title_element.get_text()),
            product_url=url,
            price_text=clean_text(price_element.get_text()),
            availability_text=clean_text(availability_element.get_text()),
            rating_text=rating,
            description=description,
            source_page=source_page,
            fetched_at=datetime.now(timezone.utc).isoformat(),
        )

    def normalize_and_validate(self, raw: RawBook) -> Book:
        return Book(**raw.model_dump(), price_gbp=normalize_price(raw.price_text))

    def save_json(self, path: Path, data) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def run(self) -> None:
        start = time.monotonic()
        started_at = datetime.now(timezone.utc).isoformat()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        valid_books: dict[str, Book] = {}
        errors: list[dict] = []
        books = self.discover_books()

        for index, (url, source_page) in enumerate(books, start=1):
            print(f"[{index}/{len(books)}] {url}")
            try:
                raw = self.extract_book(url, source_page, self.detail_cache_path(index))
                book = self.normalize_and_validate(raw)
                valid_books[book.product_url] = book
            except ValidationError as exc:
                errors.append({"url": url, "type": "validation", "reason": str(exc)})
            except Exception as exc:
                errors.append({"url": url, "type": "fetch_or_parse", "reason": str(exc)})

        self.save_json(OUTPUT_DIR / "books.json", [book.model_dump() for book in valid_books.values()])
        self.save_json(OUTPUT_DIR / "errors.json", errors)
        report = {
            "started_at": started_at,
            "duration_seconds": round(time.monotonic() - start, 3),
            "catalogue_pages": 3,
            "discovered_urls": len(books),
            "unique_urls": len(books),
            "pages_fetched": self.stats["pages_fetched"],
            "cache_hits": self.stats["cache_hits"],
            "valid_records": len(valid_books),
            "invalid_records": len(errors),
            "failed_pages": len(errors),
        }
        self.save_json(OUTPUT_DIR / "run-report.json", report)
        print("\n===== RUN REPORT =====")
        print(json.dumps(report, indent=2))
