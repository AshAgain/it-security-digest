from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.session import async_session_factory
from app.models.article import Article
from app.models.article_analysis import ArticleAnalysis
from app.services.article_topics import TOPICS


OUTPUT_DIR = Path("output")
OUTPUT_FILE = OUTPUT_DIR / "digest.docx"

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


async def get_relevant_articles():
    async with async_session_factory() as session:
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

    return articles


def add_hyperlink(paragraph, text: str, url: str) -> None:
    part = paragraph.part

    r_id = part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )

    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(
        qn("r:id"),
        r_id,
    )

    run = OxmlElement("w:r")

    run_properties = OxmlElement("w:rPr")

    color = OxmlElement("w:color")
    color.set(
        qn("w:val"),
        "0563C1",
    )
    run_properties.append(color)

    underline = OxmlElement("w:u")
    underline.set(
        qn("w:val"),
        "single",
    )
    run_properties.append(underline)

    run.append(run_properties)

    text_element = OxmlElement("w:t")
    text_element.text = text
    run.append(text_element)

    hyperlink.append(run)

    paragraph._p.append(hyperlink)


def format_date(published_at: datetime | None) -> str:
    if published_at is None:
        return "Unknown"

    return published_at.strftime("%Y-%m-%d %H:%M UTC")


def build_document(articles: list[Article]) -> Document:
    document = Document()

    styles = document.styles

    styles["Normal"].font.name = "Arial"
    styles["Normal"].font.size = Pt(10)

    title = document.add_heading(
        "IT / Information Security Digest",
        level=0,
    )
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    generated_at = datetime.now(timezone.utc)

    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    run = paragraph.add_run(
        f"Generated: {generated_at.strftime('%Y-%m-%d %H:%M UTC')}"
    )
    run.italic = True

    document.add_heading("Statistics", level=1)

    total_analyzed = len(articles)

    # Получаем количество анализов отдельно позже.
    paragraph = document.add_paragraph()
    paragraph.add_run("Relevant articles: ").bold = True
    paragraph.add_run(str(len(articles)))

    document.add_heading("Topics", level=1)

    topic_counts: dict[str, int] = {}

    for article in articles:
        topic = article.analysis.topic
        topic_counts[topic] = topic_counts.get(topic, 0) + 1

    for topic in TOPICS:
        count = topic_counts.get(topic, 0)

        if count > 0:
            paragraph = document.add_paragraph(
                style="List Bullet"
            )
            paragraph.add_run(f"{topic} — {count}")

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

            document.add_page_break()
            document.add_heading(topic, level=1)

        if importance != current_importance:
            current_importance = importance

            document.add_heading(
                IMPORTANCE_LABELS.get(
                    importance,
                    importance,
                ),
                level=2,
            )

        document.add_heading(
            article.title,
            level=3,
        )

        source_name = (
            article.source.name
            if article.source
            else "Unknown source"
        )

        paragraph = document.add_paragraph()

        run = paragraph.add_run("Source: ")
        run.bold = True

        paragraph.add_run(source_name)

        paragraph.add_run("\n")

        run = paragraph.add_run("Published: ")
        run.bold = True

        paragraph.add_run(
            format_date(article.published_at)
        )

        document.add_paragraph(
            analysis.summary
        )

        paragraph = document.add_paragraph()

        add_hyperlink(
            paragraph,
            "Read article",
            article.url,
        )

    return document


async def main() -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    articles = await get_relevant_articles()

    document = build_document(articles)

    document.save(OUTPUT_FILE)

    print("----------------------------------------")
    print("DOCX digest generated")
    print("----------------------------------------")
    print(f"Relevant articles: {len(articles)}")
    print(f"Output file: {OUTPUT_FILE}")
    print("----------------------------------------")


if __name__ == "__main__":
    asyncio.run(main())