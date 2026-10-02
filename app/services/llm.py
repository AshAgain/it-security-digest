from __future__ import annotations

from openai import AsyncOpenAI

from app.config.settings import get_settings


class OpenAIClient:
    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()

        self.base_url = settings.openai_base_url
        self.api_key = api_key if api_key is not None else settings.openai_api_key
        self.model = settings.openai_model


    async def chat(self, prompt: str) -> str:
        import httpx
        async with httpx.AsyncClient(verify=False) as http_client:
            async with AsyncOpenAI(
                api_key=self.api_key, 
                base_url=self.base_url,
                http_client=http_client
            ) as client:
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Ты помощник для анализа публикаций "
                                "в области IT и информационной безопасности."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                
        return response.choices[0].message.content
