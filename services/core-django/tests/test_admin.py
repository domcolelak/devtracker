import pytest

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_logged_client(client, django_user_model):
    django_user_model.objects.create_superuser(
        username="admin", email="admin@example.com", password="admin-pass-123"
    )
    client.login(username="admin", password="admin-pass-123")
    return client


@pytest.mark.parametrize(
    "path",
    [
        "/admin/common/user/",
        "/admin/teams/team/",
        "/admin/teams/membership/",
        "/admin/projects/project/",
        "/admin/analytics/teamproductivitystats/",
    ],
)
def test_changelists_render(admin_logged_client, path):
    assert admin_logged_client.get(path).status_code == 200


def test_admin_requires_login(client):
    response = client.get("/admin/teams/team/")
    assert response.status_code == 302
    assert "/admin/login/" in response["Location"]


def test_stats_are_read_only_in_admin(admin_logged_client, team):
    # THE ADD BUTTON PAGE MUST BE FORBIDDEN - SNAPSHOTS COME ONLY FROM CELERY
    response = admin_logged_client.get("/admin/analytics/teamproductivitystats/add/")
    assert response.status_code == 403
