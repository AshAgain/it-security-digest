from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import Source
from app.schemas.source import SourceCreate


async def list_sources(session: AsyncSession) -> list[Source]:
    result = await session.execute(
        select(Source)
        .where(Source.is_active.is_(True))
        .order_by(Source.name)
    )
    return list(result.scalars().all())


async def create_source(
    session: AsyncSession,
    source_data: SourceCreate,
) -> Source:
    source = Source(
        name=source_data.name.strip(),
        url=str(source_data.url),
        source_type=source_data.source_type.strip().lower(),
    )
    session.add(source)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise ValueError("Источник с таким URL уже существует.")

    await session.refresh(source)
    return source


async def delete_source(
    session: AsyncSession,
    source_id: int,
) -> bool:
    source = await session.get(Source, source_id)
    if source is None:
        return False

    await session.delete(source)
    await session.commit()
    return True