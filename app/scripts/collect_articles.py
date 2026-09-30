import asyncio

from app.database.session import async_session_factory
from app.services.article_collector import collect_all_sources


async def main() -> None:
    async with async_session_factory() as session:
        results = await collect_all_sources(session)

    if not results:
        print("No active sources found.")
        return

    total_received = 0
    total_saved = 0
    total_duplicates = 0
    failed_sources = 0

    print()
    print("Collecting publications...")
    print()

    for result in results:
        print(result.source_name)

        if result.error is not None:
            failed_sources += 1
            print(f"  ERROR: {result.error}")
            print()
            continue

        print(f"  received:   {result.received}")
        print(f"  saved:      {result.saved}")
        print(f"  duplicates: {result.duplicates}")
        print(f"  skipped old: {result.skipped_old}")
        print()

        total_received += result.received
        total_saved += result.saved
        total_duplicates += result.duplicates

    print("-" * 40)
    print(f"Sources processed: {len(results)}")
    print(f"Sources failed:    {failed_sources}")
    print(f"Articles received: {total_received}")
    print(f"Articles saved:    {total_saved}")
    print(f"Duplicates:        {total_duplicates}")


if __name__ == "__main__":
    asyncio.run(main())