import asyncio

from app.database.session import async_session_factory
from app.schemas.article_analysis import ArticleAnalysis
from app.services.article_analyzer import ArticleAnalyzer
from app.services.article_selector import get_recent_articles


INTERESTS = [
    "Python",
    "Linux",
    "кибербезопасность",
    "уязвимости",
    "AI",
    "LLM",
    "Docker",
    "DevSecOps",
]


async def main() -> None:
    async with async_session_factory() as session:
        articles = await get_recent_articles(
            session,
            days=7,
            limit=1,
        )

    if not articles:
        print("No articles found.")
        return

    article = articles[0]

    print()
    print("Article:")
    print(f"Title:  {article.title}")
    print(f"Source: {article.source.name}")
    print(f"URL:    {article.url}")
    print()

    analyzer = ArticleAnalyzer()

    analysis: ArticleAnalysis = await analyzer.analyze(
        session,
        article,
        INTERESTS,
    )

    print("Analysis:")
    print(analysis.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())