from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from time import struct_time
from typing import Any

import feedparser
import httpx


@dataclass(slots=True)
class CollectedArticle:
    title: str
    url: str
    description: str | None
    published_at: datetime | None


def _parse_datetime(value: struct_time | None) -> datetime | None:
    if value is None:
        return None

    return datetime(
        year=value.tm_year,
        month=value.tm_mon,
        day=value.tm_mday,
        hour=value.tm_hour,
        minute=value.tm_min,
        second=value.tm_sec,
        tzinfo=timezone.utc,
    )


def _normalize_entry(entry: Any) -> CollectedArticle | None:
    title = str(entry.get("title", "")).strip()
    url = str(entry.get("link", "")).strip()

    if not title or not url:
        return None

    description = str(
        entry.get("summary") or entry.get("description") or ""
    ).strip()

    published_parsed = entry.get("published_parsed")
    if published_parsed is None:
        published_parsed = entry.get("updated_parsed")

    return CollectedArticle(
        title=title,
        url=url,
        description=description or None,
        published_at=_parse_datetime(published_parsed),
    )


async def collect_rss(
    url: str,
    *,
    timeout: float = 20.0,
) -> list[CollectedArticle]:
    headers = {
        "User-Agent": "IT-Security-Digest/0.1",
        "Accept": (
            "application/rss+xml, application/atom+xml, "
            "application/xml, text/xml, */*"
        ),
    }

    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True,
        headers=headers,
    ) as client:
        response = await client.get(url)
        response.raise_for_status()

    feed = feedparser.parse(response.content)

    if feed.bozo and not feed.entries:
        raise ValueError(
            f"Failed to parse RSS feed: {feed.bozo_exception}"
        )

    articles: list[CollectedArticle] = []

    for entry in feed.entries:
        article = _normalize_entry(entry)

        if article is not None:
            articles.append(article)

    return articles