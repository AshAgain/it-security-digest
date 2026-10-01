from __future__ import annotations

import asyncio
from pathlib import Path

from app.database.session import async_session_factory
from app.services.digest_generator import generate_markdown_digest


OUTPUT_DIR = Path("output")
OUTPUT_FILE = OUTPUT_DIR / "digest.md"


async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    async with async_session_factory() as session:
        digest = await generate_markdown_digest(session)

    OUTPUT_FILE.write_text(
        digest,
        encoding="utf-8",
    )

    print("----------------------------------------")
    print("Digest generated")
    print("----------------------------------------")
    print(f"Output file: {OUTPUT_FILE}")
    print("----------------------------------------")


if __name__ == "__main__":
    asyncio.run(main())