import asyncio

from app.collectors.rss import collect_rss


RSS_URL = "https://www.bleepingcomputer.com/feed/"


async def main() -> None:
    articles = await collect_rss(RSS_URL)

    print(f"Received articles: {len(articles)}")
    print()

    for article in articles[:5]:
        print(f"Title: {article.title}")
        print(f"URL: {article.url}")
        print(f"Published: {article.published_at}")
        print("-" * 80)


if __name__ == "__main__":
    asyncio.run(main())