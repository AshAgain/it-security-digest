from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.article import Article
from app.models.article_analysis import ArticleAnalysis as ArticleAnalysisModel
from app.services.article_analyzer import ArticleAnalyzer
from app.services.article_collector import collect_all_sources
from app.services.article_selector import get_recent_articles
from app.services.digest_generator import generate_markdown_digest
from app.scripts.generate_digest_docx import save_docx
from app.services.digest_task_manager import update_task

@dataclass(slots=True)
class DigestResult:
    total_articles: int
    analyzed: int
    relevant: int
    not_relevant: int
    markdown_path: Path
    docx_path: Path
    preview: list[dict]


async def build_digest(
    session: AsyncSession,
    *,
    credentials: str,
    interests: list[str],
    sources: list[str],
    task_id: str | None = None,
) -> DigestResult:
    if not credentials.strip():
        raise ValueError(
            "LLM API credentials are required."
        )

    if not interests:
        raise ValueError(
            "At least one interest must be selected."
        )

    if not sources:
        raise ValueError(
            "At least one source must be selected."
        )
    
    if task_id:
        update_task(
            task_id,
            status="collecting",
            percent=5,
            message="Собираем публикации...",
        )

    # 1. Collect publications from selected sources.
    await collect_all_sources(
        session,
        source_names=sources,
    )

    # 2. Select recent publications from selected sources.
    articles = await get_recent_articles(
        session,
        days=7,
        limit=200,
        source_names=sources,
    )
    if task_id:
        update_task(
            task_id,
            status="analyzing",
            current=0,
            total=len(articles),
            percent=10,
            message=f"Найдено {len(articles)} статей. Начинаем анализ...",
        )
    if not articles:
        raise ValueError(
            "No recent articles found."
        )

    # 3. Analyze articles with the user's OpenAI-compatible API credentials.
    analyzer = ArticleAnalyzer(credentials)

    relevant = 0
    not_relevant = 0

    for index, article in enumerate(
        articles,
        start=1,
    ):
        print(
            f"[{index}/{len(articles)}] "
            f"Analyzing: {article.title}",
            flush=True,
        )

        analysis = await analyzer.analyze(
            session,
            article,
            interests,
            force_reanalysis=True,
        )

        if analysis.relevant:
            relevant += 1
        else:
            not_relevant += 1
        if task_id:
            percent = 10 + int(
                index / len(articles) * 80
            )

            update_task(
                task_id,
                status="analyzing",
                current=index,
                total=len(articles),
                percent=percent,
                message=(
                    f"Анализ статьи {index} "
                    f"из {len(articles)}"
                ),
            )

    # 4. Load the analyses produced by this run.
    article_ids = [
        article.id
        for article in articles
    ]

    result = await session.execute(
        select(Article)
        .join(ArticleAnalysisModel)
        .options(
            selectinload(Article.source),
            selectinload(Article.analysis),
        )
        .where(
            Article.id.in_(article_ids),
            ArticleAnalysisModel.relevant.is_(True),
        )
    )

    relevant_articles = list(
        result.scalars().unique().all()
    )

    preview = []

    for article in relevant_articles:
        if article.analysis is None:
            continue

        preview.append(
            {
                "title": article.title,
                "url": article.url,
                "source": (
                    article.source.name
                    if article.source
                    else "Unknown"
                ),
                "published_at": (
                    article.published_at.strftime(
                        "%Y-%m-%d %H:%M UTC"
                    )
                    if article.published_at
                    else "Unknown"
                ),
                "topic": article.analysis.topic,
                "importance": article.analysis.importance,
                "summary": article.analysis.summary,
                "reason": article.analysis.reason,
            }
        )

    if task_id:
        update_task(
            task_id,
            status="generating",
            percent=92,
            message="Генерируем Markdown и DOCX...",
        )

    # 5. Generate output files.
    output_dir = Path("output")
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    markdown_path = output_dir / "digest.md"
    docx_path = output_dir / "digest.docx"

    markdown = generate_markdown_digest(
        relevant_articles,
        total_analyzed=len(articles),
        total_relevant=relevant,
        total_not_relevant=not_relevant,
    )

    markdown_path.write_text(
        markdown,
        encoding="utf-8",
    )

    save_docx(
        relevant_articles,
        docx_path,
        total_analyzed=len(articles),
        total_relevant=relevant,
        total_not_relevant=not_relevant,
    )

    return DigestResult(
        total_articles=len(articles),
        analyzed=len(articles),
        relevant=relevant,
        not_relevant=not_relevant,
        markdown_path=markdown_path,
        docx_path=docx_path,
        preview=preview,
    )