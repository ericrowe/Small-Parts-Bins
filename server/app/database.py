import os
import logging
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from server.app.models import Base

logger = logging.getLogger(__name__)

# Default database location in server/data/parts.db
DEFAULT_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DEFAULT_DB_DIR, exist_ok=True)
DEFAULT_DB_PATH = os.path.join(DEFAULT_DB_DIR, "parts.db")
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite+aiosqlite:///{DEFAULT_DB_PATH}")

connect_args = {"timeout": 30} if "sqlite" in DATABASE_URL else {}
engine = create_async_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def configure_db_engine(database_url: str):
    """Reconfigure database engine and AsyncSessionLocal for isolated test sandboxes."""
    global engine, AsyncSessionLocal, DATABASE_URL
    DATABASE_URL = database_url
    connect_args = {"timeout": 30} if "sqlite" in database_url else {}
    engine = create_async_engine(
        database_url,
        connect_args=connect_args,
        echo=False,
        future=True,
    )
    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return engine, AsyncSessionLocal


async def init_db() -> None:
    """Initialize database tables with WAL mode concurrency and seed default taxonomy."""
    async with engine.begin() as conn:
        if "sqlite" in DATABASE_URL:
            await conn.execute(text("PRAGMA journal_mode=WAL;"))
            await conn.execute(text("PRAGMA busy_timeout=30000;"))
            await conn.execute(text("PRAGMA synchronous=NORMAL;"))
            await conn.execute(text("PRAGMA foreign_keys=ON;"))
        await conn.run_sync(Base.metadata.create_all)

    # Seed taxonomy and sample inventory from hardware/labels/data/fasteners.json
    from server.app.seed import seed_database_from_json
    await seed_database_from_json()
    logger.info("Parts-Database initialized successfully with WAL concurrency enabled.")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency yielding an async database session for FastAPI endpoints."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
