from __future__ import annotations

import json 
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from pydantic import ValidationError

from models import Book,RawBook
from utils import absolute_url,clean_text,normalize_price

BASE_URL = "https://books.toscrape.com/"
CATALOGUE_URL = "https://books.toscrape.com/catalogue/page-1.html"

CACHE_DIR = Path("cache")
OUTPUT_DIR = Path("output")

USER_AGENT = (
    "FlyRankInternshipA9/1.0 "
    "(+https://github.com/dawoodshah04/flyrank)"
)

REQUEST_DELAY = 0.5
TIMEOUT = 10

class Scraper:
    def __init__(self)->None:
        self.session = requests.Session()
        self.session.header.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml"
            }
        )

        self.last_req_time:float | None=None

        self.stats = {
            "pages_fetched":0,
            "cache_hits":0
        }

    def polite_wait(self) -> None:

        if self.last_req_time is None:
            return
        
        elasped = time.monotonic() - self.last_req_time

        if elasped < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elasped)

    def fetch(self, url:str,cache_file:Path)->str:
        if cache_file.exists():
            self.stats['cache_hits'] += 1

            print(f'CACHE HIT {url}')

            return cache_file.read_text(encoding='utf-8')


            try:
                self.last_req_time = time.monotonic()

                response = self.sessio.get(
                    url,
                    timeout=TIMEOUT
                )

                self.stats["pages_fetched"] += 1

            except requests.RequestException as exc:

                print(f"REQUEST ERROR {url}: {exc}")
                time.sleep(1)

                self.last_req_time = time.monotonic()

                response = self.session.get(
                    url,
                    timeout=TIMEOUT
                )

                self.stats["pages_fetched"] += 1

            if response.status_code != 200:

                if 500 <= response.status_code <= 599:
                      print(
                    f"SERVER ERROR {response.status_code}; "
                    f"retrying once: {url}")
                time.sleep(1)
                
                self.last_req_time = time.monotonic()

                response = self.session.get(
                    url,
                    timeout=TIMEOUT
                )