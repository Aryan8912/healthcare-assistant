"""
db/database.py — Async SQLAlchemy engine, session factory, and DB initialiser.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import event
from backend.config import settings
from backend.db.models import Base


# ── Engine ────────────────────────────────────────────────────────────────────

engine = create_async_engine(
    settings.database_url,
    echo=(settings.app_env == "development"),
    future=True,
)


# Enable WAL mode for SQLite (better concurrency)
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# ── Session Factory ───────────────────────────────────────────────────────────

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ── FastAPI Dependency ────────────────────────────────────────────────────────

async def get_db() -> AsyncSession:
    """Provides a DB session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── DB Initialiser ────────────────────────────────────────────────────────────

async def init_db() -> None:
    """Create all tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created / verified.")