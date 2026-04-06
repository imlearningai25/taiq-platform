import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.main import app
from app.core.database import Base, get_db

# Use SQLite for tests (in-memory)
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    async with TestSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ── Tests ──────────────────────────────────────────────────────────────────────
@pytest.mark.anyio
async def test_health(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.anyio
async def test_register_and_login(client):
    # Register
    r = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "Secure@Pass1",
        "full_name": "Test User",
        "role": "candidate",
    })
    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data
    assert data["user"]["email"] == "test@example.com"

    # Duplicate registration
    r2 = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "Secure@Pass1",
        "full_name": "Test User",
        "role": "candidate",
    })
    assert r2.status_code == 400

    # Login
    r3 = await client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "Secure@Pass1",
    })
    assert r3.status_code == 200
    assert "access_token" in r3.json()


@pytest.mark.anyio
async def test_jobs_list(client):
    r = await client.get("/api/v1/jobs")
    assert r.status_code == 200
    body = r.json()
    assert "jobs" in body
    assert "total" in body


@pytest.mark.anyio
async def test_public_stats(client):
    r = await client.get("/api/v1/public/stats")
    assert r.status_code == 200
    body = r.json()
    assert "total_jobs" in body


@pytest.mark.anyio
async def test_public_industries(client):
    r = await client.get("/api/v1/public/industries")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.anyio
async def test_me_requires_auth(client):
    r = await client.get("/api/v1/me")
    assert r.status_code == 403   # No auth header → HTTPBearer returns 403
