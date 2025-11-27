import asyncio
import os

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.database import Base, engine


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """Setup test database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    """Async test client fixture"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session():
    """PostgreSQL 데이터베이스 세션 for testing"""
    database_url = os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/testdb"
    )

    engine = create_async_engine(database_url)
    TestSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # 완전한 스키마 재생성
    async with engine.begin() as conn:
        # public 스키마 완전 삭제 후 재생성
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))

        # PostGIS 확장 생성
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))

        # 테이블만 생성 (인덱스 제외)
        await conn.run_sync(
            Base.metadata.create_all, tables=[Base.metadata.tables["locations"]]
        )

    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

    await engine.dispose()
