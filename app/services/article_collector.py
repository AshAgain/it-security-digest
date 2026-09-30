from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.rss import collect_rss
from app.models.article import Article
from app.models.source import Source


MAX_ARTICLE_AGE_DAYS = 7


@dataclass(slots=True)
class SourceCollectionResult:
    source_name: str
    received: int = 0
    saved: int = 0
    duplicates: int = 0
    skipped_old: int = 0
    error: str | None = None


async def collect_source(
    session: AsyncSession,
    source: Source,
) -> SourceCollectionResult:
    result = SourceCollectionResult(source_name=source.name)

    if source.source_type != "rss":
        result.error = f"Unsupported source type: {source.source_type}"
        return result

    try:
        collected_articles = await collect_rss(source.url)
    except (httpx.HTTPError, ValueError) as exc:
        result.error = str(exc)
        return result

    result.received = len(collected_articles)

    if not collected_articles:
        return result

    cutoff_date = datetime.now(timezone.utc) - timedelta(
        days=MAX_ARTICLE_AGE_DAYS
    )

    recent_articles = []

    for article in collected_articles:
        if (
            article.published_at is not None
            and article.published_at < cutoff_date
        ):
            result.skipped_old += 1
            continue

        recent_articles.append(article)

    if not recent_articles:
        return result

    urls = [article.url for article in recent_articles]

    existing_urls_result = await session.execute(
        select(Article.url).where(Article.url.in_(urls))
    )
    existing_urls = set(existing_urls_result.scalars().all())

    for collected in recent_articles:
        if collected.url in existing_urls:
            result.duplicates += 1
            continue

        article = Article(
            source_id=source.id,
            title=collected.title,
            url=collected.url,
            description=collected.description,
            published_at=collected.published_at,
        )

        session.add(article)
        existing_urls.add(collected.url)
        result.saved += 1

    await session.commit()

    return result


async def collect_all_sources(
    session,
    source_names: list[str] | None = None,
):
    query = (
        select(Source)
        .where(Source.is_active.is_(True))
        .order_by(Source.id)
    )

    if source_names:
        query = query.where(Source.name.in_(source_names))

    sources_result = await session.execute(query)
    sources = sources_result.scalars().all()

    results = []

    for source in sources:
        result = await collect_source(session, source)
        results.append(result)

    return results