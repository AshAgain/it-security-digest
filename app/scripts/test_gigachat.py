import asyncio

from app.services.gigachat import GigaChatClient


async def main() -> None:
    client = GigaChatClient()

    response = await client.chat(
        "Объясни в 3-4 предложениях, почему организациям "
        "важно отслеживать новые уязвимости в программном обеспечении."
    )

    print()
    print("GigaChat response:")
    print(response)
    print()


if __name__ == "__main__":
    asyncio.run(main())