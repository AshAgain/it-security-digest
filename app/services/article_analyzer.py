from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.article_analysis import ArticleAnalysis as ArticleAnalysisModel
from app.schemas.article_analysis import ArticleAnalysis
from app.services.article_topics import TOPICS
from app.services.gigachat import GigaChatClient


class ArticleAnalyzer:
    def __init__(self) -> None:
        self.client = GigaChatClient()

    async def analyze(
        self,
        session: AsyncSession,
        article: Article,
        interests: list[str],
    ) -> ArticleAnalysis:
        existing_result = await session.execute(
            select(ArticleAnalysisModel).where(
                ArticleAnalysisModel.article_id == article.id
            )
        )

        existing_analysis = existing_result.scalar_one_or_none()

        if existing_analysis is not None:
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
Проанализируй публикацию с точки зрения интересов пользователя.

Интересы пользователя:
{interests_text}

Допустимые темы:
{topics_text}

Публикация:

Название:
{article.title}

Источник:
{article.source.name}

Дата:
{article.published_at}

Описание:
{article.description or "Описание отсутствует"}

URL:
{article.url}

Требуется определить:

1. relevant

Определи, связана ли публикация с интересами пользователя.

2. topic

Выбери РОВНО ОДНУ тему из списка:

{topics_text}

Не создавай новые темы.

3. importance

Определи практическую значимость публикации:

- high — критически важная информация, например активно эксплуатируемая
  уязвимость, серьёзная угроза, критическое обновление безопасности
  или событие, которое специалисту важно узнать как можно скорее.
- medium — заметная и полезная информация для специалиста,
  но не требующая срочной реакции.
- low — второстепенная или преимущественно информационная публикация.

4. summary

Сделай краткое содержание публикации в 1-3 предложениях.

5. reason

Объясни, почему публикация релевантна или нерелевантна
интересам пользователя.

Верни ТОЛЬКО JSON следующего вида:

{{
    "relevant": true,
    "topic": "DevSecOps",
    "importance": "medium",
    "summary": "Краткое содержание публикации.",
    "reason": "Причина релевантности публикации."
}}
"""

        response = await self.client.chat(prompt)

        analysis = ArticleAnalysis.model_validate_json(response)

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