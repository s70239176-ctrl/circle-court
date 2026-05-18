from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings


settings = get_settings()
engine_kwargs = {"pool_pre_ping": True}
if settings.database_url.startswith("sqlite"):
    engine_kwargs["poolclass"] = NullPool

engine = create_async_engine(settings.database_url, **engine_kwargs)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
