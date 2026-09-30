from pydantic import BaseModel, Field


class DigestRequest(BaseModel):
    credentials: str = Field(min_length=1)
    interests: list[str] = Field(min_length=1)
    sources: list[str] = Field(min_length=1)