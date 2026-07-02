"""
BLACK-BOX INTEGRATION TESTS AGAINST A RUNNING docker-compose STACK.

THESE TESTS TALK TO THE STACK THROUGH NGINX (DEFAULT http://localhost), THE SAME
WAY A REAL CLIENT WOULD, AND VERIFY THAT THE SERVICES ACTUALLY WORK TOGETHER:
DJANGO-ISSUED JWT ACCEPTED BY FASTAPI AND FLASK, TASKS CREATED THROUGH THE API
VISIBLE IN REPORTS, AND SO ON.

THE WHOLE MODULE IS SKIPPED AUTOMATICALLY WHEN THE STACK IS NOT UP, SO UNIT TEST
RUNS AND CI LINT JOBS ARE NOT BLOCKED BY IT. RUN IT WITH:

    docker compose -f infra/docker-compose.yml up -d
    docker compose -f infra/docker-compose.yml exec core-django python manage.py seed_demo_data
    pytest tests/integration
"""

import os
import uuid

import httpx
import pytest

BASE_URL = os.environ.get("DEVTRACKER_BASE_URL", "http://localhost")
SEED_PASSWORD = os.environ.get("DEVTRACKER_SEED_PASSWORD", "devtracker123")


def _stack_is_up() -> bool:
    try:
        response = httpx.get(f"{BASE_URL}/nginx-health", timeout=3)
        return response.status_code == 200
    except httpx.HTTPError:
        return False


def pytest_collection_modifyitems(config, items) -> None:
    # A MODULE-LEVEL pytestmark IN conftest.py WOULD NOT PROPAGATE TO TEST MODULES,
    # SO THE STACK CHECK IS APPLIED HERE AT COLLECTION TIME INSTEAD
    if _stack_is_up():
        return
    skip_marker = pytest.mark.skip(
        reason="docker-compose stack is not running (nginx health endpoint unreachable)"
    )
    for item in items:
        item.add_marker(skip_marker)


@pytest.fixture(scope="session")
def http() -> httpx.Client:
    return httpx.Client(base_url=BASE_URL, timeout=15)


@pytest.fixture(scope="session")
def tokens(http) -> dict:
    """LOGS IN AS THE SEEDED alice USER AND RETURNS access + refresh TOKENS."""
    response = http.post("/auth/token/", json={"username": "alice", "password": SEED_PASSWORD})
    assert (
        response.status_code == 200
    ), f"Login failed ({response.status_code}) - did you run seed_demo_data? {response.text}"
    return response.json()


@pytest.fixture(scope="session")
def auth_headers(tokens) -> dict:
    return {"Authorization": f"Bearer {tokens['access']}"}


@pytest.fixture()
def unique_title() -> str:
    return f"integration-test-{uuid.uuid4().hex[:12]}"
