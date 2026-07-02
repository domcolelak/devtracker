import pytest

pytestmark = pytest.mark.django_db


class TestRegister:
    def test_register_creates_user(self, api_client, django_user_model):
        response = api_client.post(
            "/auth/register/",
            {"username": "frank", "email": "frank@example.com", "password": "Sup3rSecret!pass"},
            format="json",
        )
        assert response.status_code == 201
        assert django_user_model.objects.filter(username="frank").exists()

    def test_password_is_hashed_not_stored_plain(self, api_client, django_user_model):
        api_client.post(
            "/auth/register/",
            {"username": "frank", "email": "frank@example.com", "password": "Sup3rSecret!pass"},
            format="json",
        )
        frank = django_user_model.objects.get(username="frank")
        assert frank.password != "Sup3rSecret!pass"
        assert frank.check_password("Sup3rSecret!pass")

    def test_weak_password_rejected(self, api_client):
        response = api_client.post(
            "/auth/register/",
            {"username": "frank", "email": "frank@example.com", "password": "123"},
            format="json",
        )
        assert response.status_code == 400

    def test_duplicate_email_rejected(self, api_client, user):
        response = api_client.post(
            "/auth/register/",
            {"username": "alice2", "email": "alice@example.com", "password": "Sup3rSecret!pass"},
            format="json",
        )
        assert response.status_code == 400


class TestTokenFlow:
    def test_obtain_and_refresh(self, api_client, user):
        response = api_client.post(
            "/auth/token/",
            {"username": "alice", "password": "test-password-123"},
            format="json",
        )
        assert response.status_code == 200
        assert set(response.data.keys()) == {"access", "refresh"}

        refresh_response = api_client.post(
            "/auth/token/refresh/", {"refresh": response.data["refresh"]}, format="json"
        )
        assert refresh_response.status_code == 200
        assert "access" in refresh_response.data

    def test_wrong_password_rejected(self, api_client, user):
        response = api_client.post(
            "/auth/token/",
            {"username": "alice", "password": "wrong"},
            format="json",
        )
        assert response.status_code == 401


class TestMe:
    def test_me_returns_profile(self, auth_client):
        response = auth_client.get("/auth/me/")
        assert response.status_code == 200
        assert response.data["username"] == "alice"
        assert response.data["email"] == "alice@example.com"

    def test_me_requires_auth(self, api_client):
        assert api_client.get("/auth/me/").status_code == 401

    def test_me_teams_lists_memberships(self, auth_client, team):
        response = auth_client.get("/auth/me/teams/")
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["team_name"] == "Platform"
        assert response.data[0]["role"] == "owner"


class TestHealth:
    def test_health_endpoint(self, api_client):
        response = api_client.get("/health/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "service": "core-django"}
