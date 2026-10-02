from pydantic import AnyHttpUrl, BaseModel, Field


class SourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    url: AnyHttpUrl
    source_type: str = Field(default="rss", min_length=1, max_length=50)


class SourceRead(BaseModel):
    id: int
    name: str
    url: str
    source_type: str
    is_active: bool
