import asyncio
from collections import Counter

from app.database.session import async_session_factory
from app.services.article_selector import get_recent_articles


async def main() -> None:
    async with async_session_factory() as session:
        articles = await get_recent_articles(
            session,
            days=7,
            limit=200,
        )

    print()
    print(f"Recent articles: {len(articles)}")
    print()

    source_counts = Counter(article.source.name for article in articles)

    print("Articles by source:")
    for source_name, count in source_counts.items():
        print(f"  {source_name}: {count}")

    print()

    for index, article in enumerate(articles, start=1):
        published_at = (
            article.published_at.isoformat()
            if article.published_at
            else "unknown"
        )

        print(f"{index}. {article.title}")
        print(f"   Source: {article.source.name}")
        print(f"   Date:   {published_at}")
        print(f"   URL:    {article.url}")
        print()


if __name__ == "__main__":
    asyncio.run(main())