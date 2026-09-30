from __future__ import annotations

from datetime import datetime, timezone

from app.models.article import Article
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


def format_published_at(
    published_at: datetime | None,
) -> str:
    if published_at is None:
        return "Unknown"

    return published_at.strftime("%Y-%m-%d %H:%M UTC")


def generate_markdown_digest(
    articles: list[Article],
    *,
    total_analyzed: int,
    total_relevant: int,
    total_not_relevant: int,
) -> str:
    generated_at = datetime.now(timezone.utc)

    sorted_articles = sorted(
        articles,
        key=lambda article: (
            TOPICS.index(article.analysis.topic)
            if article.analysis and article.analysis.topic in TOPICS
            else len(TOPICS),
            IMPORTANCE_ORDER.get(
                article.analysis.importance
                if article.analysis
                else "low",
                99,
            ),
            -(
                article.published_at.timestamp()
                if article.published_at
                else 0
            ),
        ),
    )

    topic_counts: dict[str, int] = {}

    for article in sorted_articles:
        if article.analysis is None:
            continue

        topic = article.analysis.topic
        topic_counts[topic] = topic_counts.get(topic, 0) + 1

    lines = [
        "# IT / Information Security Digest",
        "",
        f"**Generated:** "
        f"{generated_at.strftime('%Y-%m-%d %H:%M UTC')}",
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

    if topic_counts:
        for topic, count in topic_counts.items():
            lines.append(f"- **{topic}:** {count}")
    else:
        lines.append("- No relevant articles found.")

    lines.extend(
        [
            "",
            "## Articles",
            "",
        ]
    )

    if not sorted_articles:
        lines.append("No relevant articles found.")
        return "\n".join(lines)

    current_topic = None

    for article in sorted_articles:
        if article.analysis is None:
            continue

        analysis = article.analysis
        topic = analysis.topic

        if topic != current_topic:
            current_topic = topic

            lines.extend(
                [
                    f"## {topic}",
                    "",
                ]
            )

        importance = IMPORTANCE_LABELS.get(
            analysis.importance,
            analysis.importance,
        )

        source_name = (
            article.source.name
            if article.source
            else "Unknown"
        )

        lines.extend(
            [
                f"### {article.title}",
                "",
                f"**Source:** {source_name}",
                "",
                f"**Published:** "
                f"{format_published_at(article.published_at)}",
                "",
                f"**Importance:** {importance}",
                "",
                f"**Summary:** {analysis.summary}",
                "",
                f"**Why relevant:** {analysis.reason}",
                "",
                f"[Read original article]({article.url})",
                "",
                "---",
                "",
            ]
        )

    return "\n".join(lines)