import time
from datetime import datetime

import jwt
import pytest
from sqlalchemy import create_engine

import app.db as db_module
import app.routes as routes_module
from app import create_app

TEST_SIGNING_KEY = "test-signing-key-32-bytes-long!!"


@pytest.fixture
def engine(monkeypatch):
    """IN-MEMORY SQLITE WITH THE SAME TABLE SHAPES THE SERVICE READS IN PRODUCTION,
    PRE-SEEDED WITH A SMALL, KNOWN DATASET."""
    engine = create_engine("sqlite:///:memory:")
    db_module.metadata.create_all(engine)

    with engine.begin() as conn:
        conn.execute(db_module.teams_table.insert().values(id=1, name="Platform", slug="platform"))
        conn.execute(
            db_module.projects_table.insert().values(
                id=1, team_id=1, name="DevTracker API", slug="devtracker-api", status="active"
            )
        )
        conn.execute(
            db_module.users_table.insert(),
            [
                {"id": 7, "username": "alice", "email": "alice@example.com"},
                {"id": 8, "username": "bob", "email": "bob@example.com"},
            ],
        )
        conn.execute(
            db_module.tasks_table.insert(),
            [
                {
                    "id": 1,
                    "project_id": 1,
                    "title": "Write architecture docs",
                    "description": None,
                    "status": "done",
                    "priority": "high",
                    "assignee_id": 7,
                    "created_by_id": 7,
                    "due_date": None,
                    "created_at": datetime(2026, 6, 1, 10, 0),
                    "updated_at": datetime(2026, 6, 15, 10, 0),
                },
                {
                    "id": 2,
                    "project_id": 1,
                    "title": "Set up CI",
                    "description": None,
                    "status": "in_progress",
                    "priority": "medium",
                    "assignee_id": 8,
                    "created_by_id": 7,
                    "due_date": None,
                    "created_at": datetime(2026, 6, 2, 10, 0),
                    "updated_at": datetime(2026, 6, 2, 10, 0),
                },
            ],
        )

    # routes.py IMPORTED get_engine INTO ITS OWN NAMESPACE, SO PATCH IT THERE
    monkeypatch.setattr(routes_module, "get_engine", lambda: engine)
    monkeypatch.setattr(db_module, "get_engine", lambda: engine)
    return engine


@pytest.fixture
def client(engine, monkeypatch):
    monkeypatch.setenv("JWT_SIGNING_KEY", TEST_SIGNING_KEY)
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    return flask_app.test_client()


def make_token(*, token_type: str = "access", expires_in: int = 3600) -> str:
    payload = {
        "token_type": token_type,
        "exp": int(time.time()) + expires_in,
        "iat": int(time.time()),
        "jti": "test-token",
        "user_id": 7,
    }
    return jwt.encode(payload, TEST_SIGNING_KEY, algorithm="HS256")


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token()}"}
