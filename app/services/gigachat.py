from __future__ import annotations

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

from app.config.settings import get_settings


class GigaChatClient:
    def __init__(self) -> None:
        settings = get_settings()

        self.credentials = settings.gigachat_credentials
        self.model = settings.gigachat_model

    async def chat(self, prompt: str) -> str:
        payload = Chat(
            messages=[
                Messages(
                    role=MessagesRole.SYSTEM,
                    content=(
                        "Ты помощник для анализа публикаций "
                        "в области IT и информационной безопасности."
                    ),
                ),
                Messages(
                    role=MessagesRole.USER,
                    content=prompt,
                ),
            ],
            model=self.model,
        )

        async with GigaChat(
            credentials=self.credentials,
            verify_ssl_certs=False,
        ) as client:
            response = await client.achat(payload)

        return response.choices[0].message.content