import re
from urllib.parse import urljoin

def absolute_url(href: str,base_url:str):
    """Convert a relative URL into an absolute"""
    return urljoin(base_url,href)


def normalize_price(price_text:str)->float:
    match = re.search(r"(\d+(?:\.\d+)?)",price_text)

    if not match:
        raise ValueError(f"Could not find price in {price_text}")

    return float(match.group(1))


def clean_text(value:str | None)-> str | None:
    if value is None:
        return None

    value = " ".join(value.split())

    return value if value else None


