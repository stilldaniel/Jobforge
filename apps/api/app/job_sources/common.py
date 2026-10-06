"""
Helpers shared by job source integrations.
"""

import html
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from typing import Any

import httpx


USER_AGENT = "JobForge/0.1 (job matching service)"

DEFAULT_TIMEOUT = 30.0

# Search APIs are queried once per search term, so cap how many
# terms a single fetch can use.
MAX_SEARCH_QUERIES = 5


def get_json(
    url: str,
    params: dict | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> Any:
    response = httpx.get(
        url,
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
        follow_redirects=True,
    )

    response.raise_for_status()

    return response.json()


def get_text(
    url: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    response = httpx.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
        follow_redirects=True,
    )

    response.raise_for_status()

    return response.text


# ============================================================
# HTML
# ============================================================

BLOCK_TAGS = {
    "p",
    "div",
    "br",
    "li",
    "ul",
    "ol",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "tr",
    "section",
    "article",
}


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

        if tag == "li":
            self.parts.append("• ")

    def handle_endtag(self, tag):
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        self.parts.append(data)


def html_to_text(value: str | None) -> str | None:
    """
    Convert an HTML job description to plain text with one
    paragraph per line, which is how the frontend renders it.
    """

    if not value:
        return None

    # Some APIs (e.g. Greenhouse) return HTML that is itself escaped.
    if "&lt;" in value and "<" not in value:
        value = html.unescape(value)

    parser = _TextExtractor()
    parser.feed(value)
    parser.close()

    text = "".join(parser.parts).replace("\xa0", " ")

    lines = [
        re.sub(r"[ \t]+", " ", line).strip()
        for line in text.splitlines()
    ]

    text = "\n".join(line for line in lines if line)

    return text or None


# ============================================================
# VALUES
# ============================================================

def clean_str(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()

    return text or None


def to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None

    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return None

    # Several APIs use 0 to mean "not provided".
    return number if number > 0 else None


def parse_iso_datetime(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed


def parse_epoch(value: Any, milliseconds: bool = False) -> datetime | None:
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        return None

    if milliseconds:
        seconds /= 1000

    try:
        return datetime.fromtimestamp(seconds, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def parse_rfc822(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None

    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed


# ============================================================
# SALARY
# ============================================================

PERIOD_MULTIPLIERS = {
    "year": 1,
    "month": 12,
    "week": 52,
    "day": 260,
    "hour": 2080,
}

PERIOD_ALIASES = {
    "year": "year",
    "yearly": "year",
    "annual": "year",
    "annually": "year",
    "1 year": "year",
    "per-year-salary": "year",
    "month": "month",
    "monthly": "month",
    "1 month": "month",
    "per-month-salary": "month",
    "week": "week",
    "weekly": "week",
    "1 week": "week",
    "day": "day",
    "daily": "day",
    "1 day": "day",
    "hour": "hour",
    "hourly": "hour",
    "1 hour": "hour",
    "per-hour-wage": "hour",
}


def normalize_salary(
    minimum: Any,
    maximum: Any,
    currency: Any,
    period: Any,
) -> tuple[int | None, int | None, str | None, str | None]:
    """
    Convert a salary range to yearly amounts.

    Returns (salary_min, salary_max, currency, "year"), or all None
    when the amount, currency or period is unknown, because a number
    without its unit cannot be compared with a candidate's preference.
    """

    salary_min = to_int(minimum)
    salary_max = to_int(maximum)
    currency_code = clean_str(currency)
    period_key = PERIOD_ALIASES.get(
        (clean_str(period) or "").lower()
    )

    if (
        (salary_min is None and salary_max is None)
        or not currency_code
        or not period_key
    ):
        return None, None, None, None

    multiplier = PERIOD_MULTIPLIERS[period_key]

    return (
        salary_min * multiplier if salary_min is not None else None,
        salary_max * multiplier if salary_max is not None else None,
        currency_code.upper(),
        "year",
    )


def company_from_slug(slug: str) -> str:
    return " ".join(
        part.capitalize()
        for part in re.split(r"[-_]+", slug)
        if part
    )


def config_list(value: str | None) -> list[str]:
    if not value:
        return []

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]
