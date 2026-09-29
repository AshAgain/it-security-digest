from __future__ import annotations

from dataclasses import dataclass

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.rss import collect_rss
from app.models.article import Article
from app.models.source import Source


@dataclass(slots=True)
class SourceCollectionResult:
    source_name: str
    received: int = 0
    saved: int = 0
    duplicates: int = 0
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

    urls = [article.url for article in collected_articles]

    existing_urls_result = await session.execute(
        select(Article.url).where(Article.url.in_(urls))
    )
    existing_urls = set(existing_urls_result.scalars().all())

    for collected in collected_articles:
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
    session: AsyncSession,
) -> list[SourceCollectionResult]:
    sources_result = await session.execute(
        select(Source)
        .where(Source.is_active.is_(True))
        .order_by(Source.id)
    )

    sources = sources_result.scalars().all()

    results: list[SourceCollectionResult] = []

    for source in sources:
        result = await collect_source(session, source)
        results.append(result)

    return results