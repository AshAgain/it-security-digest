import asyncio

from app.services.llm import OpenAIClient


async def main() -> None:
    client = OpenAIClient()

    response = await client.chat(
        "Объясни в 3-4 предложениях, почему организациям "
        "важно отслеживать новые уязвимости в программном обеспечении."
    )

    print()
    print("OpenAI-compatible model response:")
    print(response)
    print()


if __name__ == "__main__":
    asyncio.run(main())