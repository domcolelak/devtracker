import asyncio
import time

import fakeredis.aioredis
import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.core.redis as redis_module
from app.core.config import get_settings
from app.core.db import get_db
from app.main import app
from app.models.base import Base
from app.models.external import projects_table, users_table

settings = get_settings()


@pytest.fixture
def db_engine():
    """FRESH IN-MEMORY SQLITE PER TEST. ALL TABLES (INCLUDING THE NORMALLY
    DJANGO-OWNED ONES) LIVE IN Base.metadata, SO create_all BUILDS THE WHOLE
    SCHEMA INCLUDING THE CROSS-SERVICE FOREIGN KEYS."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async def setup() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(
                projects_table.insert().values(
                    id=1, team_id=1, name="DevTracker API", slug="devtracker-api", status="active"
                )
            )
            await conn.execute(
                users_table.insert().values(id=7, username="alice", email="alice@example.com")
            )

    asyncio.run(setup())
    yield engine
    asyncio.run(engine.dispose())


@pytest.fixture
def client(db_engine):
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    # REDIRECT REDIS PUBLISHES TO fakeredis SO NO SERVER IS NEEDED. tasks.py CALLS
    # get_redis_client() WHICH READS THE MODULE-LEVEL _shared_client SINGLETON.
    redis_module._shared_client = fakeredis.aioredis.FakeRedis(decode_responses=True)

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    redis_module._shared_client = None


def make_token(
    *,
    user_id: int = 7,
    token_type: str = "access",
    expires_in: int = 3600,
    signing_key: str | None = None,
) -> str:
    """BUILDS A TOKEN WITH THE EXACT CLAIM SHAPE djangorestframework-simplejwt USES."""
    payload = {
        "token_type": token_type,
        "exp": int(time.time()) + expires_in,
        "iat": int(time.time()),
        "jti": "test-token",
        "user_id": user_id,
    }
    return jwt.encode(
        payload, signing_key or settings.jwt_signing_key, algorithm=settings.jwt_algorithm
    )


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token()}"}
