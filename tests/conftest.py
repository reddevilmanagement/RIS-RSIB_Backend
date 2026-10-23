"""
Pytest fixtures — shared test setup for auth and RBAC tests.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.db.base import Base
from app.db.session import AsyncSessionLocal
from app.core.dependencies import get_db
from app.core.security import hash_password
from app.models.user import User, UserRole

# ─── In-memory SQLite for tests ───────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ─── User fixtures ────────────────────────────────────────────────────

async def _create_user(db: AsyncSession, username: str, role: UserRole) -> User:
    user = User(
        username=username,
        email=f"{username}@test.com",
        full_name=f"Test {username.capitalize()}",
        hashed_password=hash_password("password123"),
        role=role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session):
    return await _create_user(db_session, "test_admin", UserRole.ADMIN)


@pytest_asyncio.fixture
async def radiolog_user(db_session):
    return await _create_user(db_session, "test_radiolog", UserRole.RADIOLOG)


@pytest_asyncio.fixture
async def dokter_user(db_session):
    return await _create_user(db_session, "test_dokter", UserRole.DOKTER)


@pytest_asyncio.fixture
async def resepsionis_user(db_session):
    return await _create_user(db_session, "test_resepsionis", UserRole.RESEPSIONIS)


async def _get_token(client: AsyncClient, username: str) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": "password123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def admin_token(client, admin_user):
    return await _get_token(client, admin_user.username)


@pytest_asyncio.fixture
async def radiolog_token(client, radiolog_user):
    return await _get_token(client, radiolog_user.username)


@pytest_asyncio.fixture
async def dokter_token(client, dokter_user):
    return await _get_token(client, dokter_user.username)


@pytest_asyncio.fixture
async def resepsionis_token(client, resepsionis_user):
    return await _get_token(client, resepsionis_user.username)
