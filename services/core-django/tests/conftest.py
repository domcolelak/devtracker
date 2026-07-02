import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from rest_framework.test import APIClient

from apps.projects.models import Project
from apps.teams.models import Membership, Team

User = get_user_model()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="alice", email="alice@example.com", password="test-password-123"
    )


@pytest.fixture
def team(db, user):
    team = Team.objects.create(name="Platform", created_by=user)
    Membership.objects.create(team=team, user=user, role="owner")
    return team


@pytest.fixture
def project(team, user):
    return Project.objects.create(team=team, name="DevTracker API", created_by=user)


@pytest.fixture
def auth_client(api_client, user) -> APIClient:
    """API CLIENT PRE-AUTHENTICATED WITH A REAL simplejwt ACCESS TOKEN, SO TESTS
    EXERCISE THE FULL JWT AUTHENTICATION PATH RATHER THAN force_authenticate."""
    response = api_client.post(
        "/auth/token/",
        {"username": "alice", "password": "test-password-123"},
        format="json",
    )
    assert response.status_code == 200, response.content
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return api_client


@pytest.fixture
def tasks_table(db):
    """CREATES THE (NORMALLY api-fastapi OWNED, UNMANAGED) tasks TABLE SO TESTS OF
    apps.analytics CAN QUERY THE ExternalTask MODEL. SQLITE DDL PARTICIPATES IN THE
    TEST TRANSACTION, SO THE TABLE DISAPPEARS AGAIN ON ROLLBACK."""
    with connection.cursor() as cursor:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS tasks ("
            "id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL, title VARCHAR(200) NOT NULL, "
            "status VARCHAR(20) NOT NULL, priority VARCHAR(20) NOT NULL, assignee_id INTEGER, "
            "created_by_id INTEGER NOT NULL, due_date DATE, created_at DATETIME NOT NULL, "
            "updated_at DATETIME NOT NULL)"
        )
    return None


def insert_task(
    task_id: int,
    project_id: int,
    *,
    title: str = "Some task",
    status: str = "todo",
    assignee_id: int | None = None,
    created_by_id: int = 1,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO tasks (id, project_id, title, status, priority, assignee_id, "
            "created_by_id, created_at, updated_at) VALUES "
            "(%s, %s, %s, %s, 'medium', %s, %s, '2026-06-01 10:00:00', '2026-06-01 10:00:00')",
            [task_id, project_id, title, status, assignee_id, created_by_id],
        )
