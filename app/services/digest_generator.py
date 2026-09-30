from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.article import Article
from app.models.article_analysis import ArticleAnalysis
from app.services.article_topics import TOPICS


IMPORTANCE_ORDER = {
    "high": 0,
    "medium": 1,
    "low": 2,
}

IMPORTANCE_LABELS = {
    "high": "High priority",
    "medium": "Medium priority",
    "low": "Low priority",
}


def format_published_at(published_at: datetime | None) -> str:
    if published_at is None:
        return "Unknown"

    return published_at.strftime("%Y-%m-%d %H:%M UTC")


async def generate_markdown_digest(
    session: AsyncSession,
) -> str:
    result = await session.execute(
        select(Article)
        .join(ArticleAnalysis)
        .options(
            selectinload(Article.source),
            selectinload(Article.analysis),
        )
        .where(
            ArticleAnalysis.relevant.is_(True),
        )
    )

    articles = list(result.scalars().all())

    articles.sort(
        key=lambda article: (
            TOPICS.index(article.analysis.topic)
            if article.analysis.topic in TOPICS
            else len(TOPICS),
            IMPORTANCE_ORDER.get(article.analysis.importance, 99),
            -(
                article.published_at.timestamp()
                if article.published_at
                else 0
            ),
        )
    )

    generated_at = datetime.now(timezone.utc)

    total_relevant = len(articles)

    all_analyses_result = await session.execute(
        select(ArticleAnalysis)
    )
    all_analyses = list(all_analyses_result.scalars().all())

    total_analyzed = len(all_analyses)
    total_not_relevant = sum(
        1 for analysis in all_analyses
        if not analysis.relevant
    )

    topic_counts: dict[str, int] = {}

    for article in articles:
        topic = article.analysis.topic
        topic_counts[topic] = topic_counts.get(topic, 0) + 1

    lines: list[str] = [
        "# IT / Information Security Digest",
        "",
        f"**Generated:** {generated_at.strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Statistics",
        "",
        f"- **Analyzed:** {total_analyzed}",
        f"- **Relevant:** {total_relevant}",
        f"- **Not relevant:** {total_not_relevant}",
        "",
        "## Topics",
        "",
    ]

    for topic in TOPICS:
        count = topic_counts.get(topic, 0)

        if count > 0:
            lines.append(f"- **{topic}** — {count}")

    lines.extend(
        [
            "",
        ]
    )

    current_topic: str | None = None
    current_importance: str | None = None

    for article in articles:
        analysis = article.analysis

        if analysis is None:
            continue

        topic = analysis.topic
        importance = analysis.importance

        if topic != current_topic:
            current_topic = topic
            current_importance = None

            lines.extend(
                [
                    f"## {topic}",
                    "",
                ]
            )

        if importance != current_importance:
            current_importance = importance

            lines.extend(
                [
                    f"### {IMPORTANCE_LABELS.get(importance, importance)}",
                    "",
                ]
            )

        source_name = (
            article.source.name
            if article.source
            else "Unknown source"
        )

        lines.extend(
            [
                f"#### {article.title}",
                "",
                f"**Source:** {source_name}  ",
                f"**Published:** {format_published_at(article.published_at)}",
                "",
                analysis.summary,
                "",
                f"[Read article]({article.url})",
                "",
            ]
        )

    if not articles:
        lines.append("No relevant articles found.")

    return "\n".join(lines)