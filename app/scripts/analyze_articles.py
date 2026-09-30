import asyncio
from sqlalchemy import select
from app.database.session import async_session_factory
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

        analyzer = ArticleAnalyzer()

        total = len(articles)
        already_analyzed = 0
        newly_analyzed = 0
        relevant_count = 0
        not_relevant_count = 0

        print()
        print("Analyzing articles...")
        print()

        for index, article in enumerate(articles, start=1):
            print(f"[{index}/{total}] {article.title}")

            result = await session.execute(
                select(ArticleAnalysis).where(
                    ArticleAnalysis.article_id == article.id
                )
            )

            existing_analysis = result.scalar_one_or_none()

            if existing_analysis is not None:
                already_analyzed += 1

                if existing_analysis.relevant:
                    relevant_count += 1
                else:
                    not_relevant_count += 1

                print("  already analyzed -> skipped")
                print(f"  relevant: {existing_analysis.relevant}")
                print(f"  topic: {existing_analysis.topic}")
                print(f"  importance: {existing_analysis.importance}")
                print()

                continue

            print("  analyzing...")

            analysis = await analyzer.analyze(
                session,
                article,
                INTERESTS,
            )

            newly_analyzed += 1

            if analysis.relevant:
                relevant_count += 1
            else:
                not_relevant_count += 1

            print(f"  relevant: {analysis.relevant}")
            print(f"  topic: {analysis.topic}")
            print(f"  importance: {analysis.importance}")
            print()

        print("----------------------------------------")
        print(f"Articles selected: {total}")
        print(f"Already analyzed: {already_analyzed}")
        print(f"Newly analyzed: {newly_analyzed}")
        print(f"Relevant: {relevant_count}")
        print(f"Not relevant: {not_relevant_count}")
        print("----------------------------------------")
        print()


if __name__ == "__main__":
    asyncio.run(main())