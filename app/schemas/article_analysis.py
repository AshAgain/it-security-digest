from typing import Literal

from pydantic import BaseModel


class ArticleAnalysis(BaseModel):
    relevant: bool
    topic: str
    importance: Literal["high", "medium", "low"]
    summary: str
    reason: str