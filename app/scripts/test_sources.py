import asyncio

from app.collectors.rss import collect_rss


SOURCES = [
    {
        "name": "BleepingComputer",
        "url": "https://www.bleepingcomputer.com/feed/",
    },
    {
        "name": "The Register — Security",
        "url": "https://api.theregister.com/api/v1/article?limit=25&orderBy=published&query=tag%3Asecurity&remapper=rss&site_id=2",
    },
    {
        "name": "The Register — AI & ML",
        "url": "https://api.theregister.com/api/v1/article?limit=25&orderBy=published&query=tag%3A%22ai+and+ml%22&remapper=rss&site_id=2",
    },
    {
        "name": "Schneier on Security",
        "url": "https://www.schneier.com/feed/atom",
    },
    {
        "name": "Microsoft Security Response Center",
        "url": "https://api.msrc.microsoft.com/update-guide/rss",
    },
]


async def main() -> None:
    for source in SOURCES:
        print("=" * 70)
        print(source["name"])
        print(source["url"])

        try:
            articles = await collect_rss(source["url"])

            print(f"OK: {len(articles)} articles")

            for article in articles[:3]:
                print(f"  - {article.title}")

        except Exception as exc:
            print(f"ERROR: {type(exc).__name__}: {exc}")

        print()


if __name__ == "__main__":
    asyncio.run(main())