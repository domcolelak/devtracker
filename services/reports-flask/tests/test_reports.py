from tests.conftest import make_token


class TestHealth:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.get_json() == {"status": "ok", "service": "reports-flask"}


class TestAuth:
    def test_missing_token_rejected(self, client):
        assert client.get("/productivity.pdf?team_id=1").status_code == 401
        assert client.get("/tasks.csv?team_id=1").status_code == 401

    def test_garbage_token_rejected(self, client):
        headers = {"Authorization": "Bearer not-a-jwt"}
        assert client.get("/productivity.pdf?team_id=1", headers=headers).status_code == 401

    def test_expired_token_rejected(self, client):
        headers = {"Authorization": f"Bearer {make_token(expires_in=-10)}"}
        assert client.get("/productivity.pdf?team_id=1", headers=headers).status_code == 401

    def test_refresh_token_rejected(self, client):
        headers = {"Authorization": f"Bearer {make_token(token_type='refresh')}"}
        assert client.get("/productivity.pdf?team_id=1", headers=headers).status_code == 401


class TestProductivityPdf:
    def test_missing_team_id_rejected(self, client, auth_headers):
        response = client.get("/productivity.pdf", headers=auth_headers)
        assert response.status_code == 400

    def test_unknown_team_404(self, client, auth_headers):
        response = client.get("/productivity.pdf?team_id=999", headers=auth_headers)
        assert response.status_code == 404

    def test_generates_valid_pdf(self, client, auth_headers):
        response = client.get(
            "/productivity.pdf?team_id=1&start_date=2026-06-01&end_date=2026-06-30",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.content_type == "application/pdf"
        assert response.data[:4] == b"%PDF"
        assert "productivity_platform.pdf" in response.headers["Content-Disposition"]

    def test_pdf_without_date_range_defaults_to_all_time(self, client, auth_headers):
        response = client.get("/productivity.pdf?team_id=1", headers=auth_headers)
        assert response.status_code == 200
        assert response.data[:4] == b"%PDF"


class TestTasksCsv:
    def test_missing_filters_rejected(self, client, auth_headers):
        response = client.get("/tasks.csv", headers=auth_headers)
        assert response.status_code == 400

    def test_export_by_project(self, client, auth_headers):
        response = client.get("/tasks.csv?project_id=1", headers=auth_headers)
        assert response.status_code == 200
        assert response.content_type.startswith("text/csv")

        body = response.data.decode()
        lines = body.strip().splitlines()
        assert lines[0] == "id,title,status,priority,assignee,project,due_date,created_at"
        assert len(lines) == 3
        assert "Write architecture docs" in body
        assert "alice" in body
        assert "bob" in body

    def test_export_by_team(self, client, auth_headers):
        response = client.get("/tasks.csv?team_id=1", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.data.decode().strip().splitlines()) == 3

    def test_export_empty_project_has_header_only(self, client, auth_headers, engine):
        import app.db as db_module

        with engine.begin() as conn:
            conn.execute(
                db_module.projects_table.insert().values(
                    id=2, team_id=1, name="Empty", slug="empty", status="active"
                )
            )
        response = client.get("/tasks.csv?project_id=2", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.data.decode().strip().splitlines()) == 1
