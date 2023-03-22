import os

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

DATABASE_URL = os.environ.get("DATABASE_URL")
LOCAL_DEV = os.environ.get("LOCAL_DEV")

if LOCAL_DEV:
    DATABASE_URL = "sqlite+aiosqlite:///database.db"

if DATABASE_URL is None and LOCAL_DEV is None:
    # fallback to in memory sqlite - testing, misconfiguration, etc
    DATABASE_URL = "sqlite+aiosqlite:///"

engine = create_async_engine(DATABASE_URL, echo=True, future=True)


async def init_db():
    async with engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncSession:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
