# FlyRank A9 — Scraping in Practice

A small Python scraping pipeline for Books to Scrape.

## Target classification

The target is Books to Scrape:

https://books.toscrape.com/

The site is a public scraping sandbox specifically intended for practising
web scraping.

I only process the first three catalogue pages, which contain 60 books.

I collect:

- title
- product_url
- price_text
- availability_text
- rating_text
- description
- source_page
- fetched_at

I then normalize the price into `price_gbp` and validate the finished
record before storing it.

### Robots check

I requested:

https://books.toscrape.com/robots.txt

The request returned 404 Not Found, so I recorded:

"no robots file found"

A missing robots.txt file is not treated as permission to scrape other sites.

I will not reuse this code on another site without checking its rules and
terms first.

## Stack

Python 3.10+

- Requests
- BeautifulSoup
- Pydantic
- pytest

## Installation

```bash
python -m venv .venv
