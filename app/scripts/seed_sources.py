import asyncio

from sqlalchemy import select

from app.database.session import async_session_factory
from app.models.source import Source

SOURCES = [
    {
        "name": "BleepingComputer",
        "url": "https://www.bleepingcomputer.com/feed/",
        "source_type": "rss",
    },
    {
        "name": "Schneier on Security",
        "url": "https://www.schneier.com/feed/atom",
        "source_type": "rss",
    },
    {
        "name": "Microsoft Security Response Center",
        "url": "https://api.msrc.microsoft.com/update-guide/rss",
        "source_type": "rss",
    },
]

async def main() -> None:
    async with async_session_factory() as session:
        for source_data in SOURCES:
            result = await session.execute(
                select(Source).where(Source.url == source_data["url"])
            )
            existing_source = result.scalar_one_or_none()

            if existing_source is not None:
                print(f"Already exists: {existing_source.name}")
                continue

            source = Source(**source_data)
            session.add(source)

            print(f"Added: {source_data['name']}")

        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())