# Iron Arena — Database Connection and Session Management
# Created by: engineering-backend-architect
# Purpose: SQLAlchemy async engine setup, session factory, init/close lifecycle

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://iron_arena:iron_arena_pass@localhost:5432/iron_arena"
)
# Fix prefix for asyncpg
DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")


class Base(DeclarativeBase):
    pass


engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    """Create all tables on startup (use Alembic for production migrations)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Dispose engine connections on shutdown."""
    await engine.dispose()


async def get_session() -> AsyncSession:
    """FastAPI dependency: yield a database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
