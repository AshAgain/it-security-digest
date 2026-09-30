from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.article import Article
from app.models.source import Source


async def get_recent_articles(
    session: AsyncSession,
    *,
    days: int = 7,
    limit: int = 200,
    per_source_limit: int = 70,
    source_names: list[str] | None = None,
) -> list[Article]:
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    sources_query = (
        select(Source)
        .where(Source.is_active.is_(True))
        .order_by(Source.id)
    )

    if source_names:
        sources_query = sources_query.where(
            Source.name.in_(source_names)
        )

    sources_result = await session.execute(sources_query)
    sources = list(sources_result.scalars().all())

    articles = []

    for source in sources:
        result = await session.execute(
            select(Article)
            .options(selectinload(Article.source))
            .where(
                Article.source_id == source.id,
                Article.published_at.is_not(None),
                Article.published_at >= cutoff_date,
            )
            .order_by(Article.published_at.desc())
            .limit(per_source_limit)
        )

        articles.extend(result.scalars().all())

    articles.sort(
        key=lambda article: (
            article.published_at.timestamp()
            if article.published_at
            else 0
        ),
        reverse=True,
    )

    return articles[:limit]