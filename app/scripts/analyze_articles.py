import asyncio

from sqlalchemy import select

from app.database.session import async_session_factory
from app.models.article import Article
from app.models.article_analysis import ArticleAnalysis
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

RETRY_COUNT = 3
RETRY_DELAY_SECONDS = 10


async def analyze_article(
    article: Article,
    index: int,
    total: int,
) -> tuple[bool, bool]:
    print(f"[{index}/{total}] {article.title}")
    print("  analyzing...")

    for attempt in range(1, RETRY_COUNT + 1):
        try:
            async with async_session_factory() as session:
                analyzer = ArticleAnalyzer()

                analysis = await analyzer.analyze(
                    session,
                    article,
                    INTERESTS,
                )

                print(f"  relevant: {analysis.relevant}")
                print(f"  topic: {analysis.topic}")
                print(f"  importance: {analysis.importance}")
                print()

                return True, analysis.relevant

        except Exception as exc:
            print(f"  attempt {attempt}/{RETRY_COUNT} failed: {exc}")

            if attempt < RETRY_COUNT:
                print(
                    f"  waiting {RETRY_DELAY_SECONDS} seconds before retry..."
                )
                await asyncio.sleep(RETRY_DELAY_SECONDS)
            else:
                print("  ERROR: analysis failed")
                print()

    return False, False


async def main() -> None:
    async with async_session_factory() as session:
        articles = await get_recent_articles(
            session,
            days=7,
            limit=200,
        )

        if not articles:
            print("No articles found.")
            return

        total = len(articles)

        result = await session.execute(
            select(ArticleAnalysis.article_id).where(
                ArticleAnalysis.article_id.in_(
                    article.id for article in articles
                )
            )
        )

        analyzed_article_ids = set(result.scalars().all())

    articles_to_analyze = [
        article
        for article in articles
        if article.id not in analyzed_article_ids
    ]

    already_analyzed = len(analyzed_article_ids)

    print()
    print("Article analysis")
    print("----------------------------------------")
    print(f"Articles selected: {total}")
    print(f"Already analyzed: {already_analyzed}")
    print(f"To analyze: {len(articles_to_analyze)}")
    print(f"Retry count: {RETRY_COUNT}")
    print("----------------------------------------")
    print()

    if not articles_to_analyze:
        print("All selected articles are already analyzed.")
        return

    newly_analyzed = 0
    relevant_count = 0
    not_relevant_count = 0
    failed_count = 0

    for index, article in enumerate(articles_to_analyze, start=1):
        success, relevant = await analyze_article(
            article,
            index,
            total,
        )

        if not success:
            failed_count += 1
            continue

        newly_analyzed += 1

        if relevant:
            relevant_count += 1
        else:
            not_relevant_count += 1

    print("----------------------------------------")
    print("Analysis finished")
    print("----------------------------------------")
    print(f"Articles selected: {total}")
    print(f"Already analyzed: {already_analyzed}")
    print(f"Newly analyzed: {newly_analyzed}")
    print(f"Relevant: {relevant_count}")
    print(f"Not relevant: {not_relevant_count}")
    print(f"Failed: {failed_count}")
    print("----------------------------------------")
    print()


if __name__ == "__main__":
    asyncio.run(main())