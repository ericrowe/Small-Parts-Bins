import os
import logging
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from server.app.models import Base

logger = logging.getLogger(__name__)

def resolve_database_url() -> str:
    """Resolve database URL with production SSD mount detection and workstation fallback."""
    if "DATABASE_URL" in os.environ:
        return os.environ["DATABASE_URL"]
    ssd_dir = "/srv/database/parts"
    if os.path.isdir(ssd_dir):
        return f"sqlite+aiosqlite:///{os.path.join(ssd_dir, 'parts.db')}"
    local_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    os.makedirs(local_dir, exist_ok=True)
    return f"sqlite+aiosqlite:///{os.path.join(local_dir, 'parts.db')}"

DATABASE_URL = resolve_database_url()

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


async def run_sqlite_migrations(conn):
    """Perform self-healing schema migrations on existing SQLite databases."""
    if "sqlite" not in DATABASE_URL:
        return

    # Check if bins table exists with legacy schema (part_id NOT NULL on bins)
    try:
        res = await conn.execute(text("PRAGMA table_info(bins);"))
        existing_cols = {row[1]: row for row in res.fetchall()}
        
        if existing_cols:
            # If bins table has legacy part_id column, drop and let Base.metadata.create_all recreate
            if "part_id" in existing_cols or "compartment_count" not in existing_cols:
                logger.info("Migrating schema: Upgrading legacy bins table to multi-compartment architecture...")
                await conn.execute(text("DROP TABLE IF EXISTS bin_compartments;"))
                await conn.execute(text("DROP TABLE IF EXISTS bins;"))
    except Exception as e:
        logger.debug(f"Migration check on bins table: {e}")


async def init_db() -> None:
    """Initialize database tables with WAL mode concurrency, self-healing migrations, and seed taxonomy."""
    async with engine.begin() as conn:
        if "sqlite" in DATABASE_URL:
            await conn.execute(text("PRAGMA journal_mode=WAL;"))
            await conn.execute(text("PRAGMA busy_timeout=30000;"))
            await conn.execute(text("PRAGMA synchronous=NORMAL;"))
            await conn.execute(text("PRAGMA foreign_keys=ON;"))
            await run_sqlite_migrations(conn)
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
