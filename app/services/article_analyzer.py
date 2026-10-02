from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.article_analysis import ArticleAnalysis as ArticleAnalysisModel
from app.schemas.article_analysis import ArticleAnalysis
from app.services.article_topics import TOPICS
from app.services.gigachat import GigaChatClient
from app.services.llm import OpenAIClient


class ArticleAnalyzer:
    def __init__(self, credentials: str | None = None) -> None:
        #self.client = OpenAIClient(credentials)
        self.client = GigaChatClient(credentials)

    async def analyze(
        self,
        session: AsyncSession,
        article: Article,
        interests: list[str],
        *,
        force_reanalysis: bool = False,
    ) -> ArticleAnalysis:
        existing_result = await session.execute(
            select(ArticleAnalysisModel).where(
                ArticleAnalysisModel.article_id == article.id
            )
        )

        existing_analysis = existing_result.scalar_one_or_none()

        if existing_analysis is not None and not force_reanalysis:
            return ArticleAnalysis(
                relevant=existing_analysis.relevant,
                topic=existing_analysis.topic,
                importance=existing_analysis.importance,
                summary=existing_analysis.summary,
                reason=existing_analysis.reason,
            )

        interests_text = ", ".join(interests)
        topics_text = ", ".join(TOPICS)

        prompt = f"""
Проанализируй публикацию из области IT и информационной безопасности.

Интересы пользователя:
{interests_text}

Допустимые темы:
{topics_text}

Информация о публикации:

Название:
{article.title}

Источник:
{article.source.name if article.source else "Unknown"}

Дата публикации:
{article.published_at}

Описание:
{article.description or "Описание отсутствует"}

URL:
{article.url}

Определи:

1. relevant — представляет ли публикация интерес для пользователя с учетом его интересов.
2. topic — выбери одну тему из списка допустимых тем.
3. importance — важность публикации: high, medium или low.
4. summary — краткое описание содержания публикации на русском языке.
5. reason — кратко объясни, почему публикация релевантна или нерелевантна интересам пользователя.

Верни результат строго в JSON следующего формата:

{{
    "relevant": true,
    "topic": "Vulnerabilities",
    "importance": "high",
    "summary": "Краткое содержание публикации.",
    "reason": "Публикация связана с интересами пользователя."
}}

Не добавляй Markdown, комментарии или дополнительный текст.
"""

        response = await self.client.chat(prompt)

        analysis = ArticleAnalysis.model_validate_json(response)

        if existing_analysis is not None:
            existing_analysis.relevant = analysis.relevant
            existing_analysis.topic = analysis.topic
            existing_analysis.importance = analysis.importance
            existing_analysis.summary = analysis.summary
            existing_analysis.reason = analysis.reason
        else:
            analysis_record = ArticleAnalysisModel(
                article_id=article.id,
                relevant=analysis.relevant,
                topic=analysis.topic,
                importance=analysis.importance,
                summary=analysis.summary,
                reason=analysis.reason,
            )

            session.add(analysis_record)

        await session.commit()

        return analysis