class TestHealthThroughNginx:
    def test_all_services_healthy(self, http):
        assert http.get("/api/health").json()["service"] == "api-fastapi"
        assert http.get("/reports/health").json()["service"] == "reports-flask"
        # DJANGO HEALTH IS NOT EXPOSED THROUGH NGINX (INTERNAL ONLY), BUT ITS
        # AUTH ENDPOINTS ARE - COVERED BY THE tokens FIXTURE LOGGING IN


class TestCrossServiceJwt:
    def test_django_token_accepted_by_fastapi(self, http, auth_headers):
        response = http.get("/api/tasks", headers=auth_headers)
        assert response.status_code == 200

    def test_django_token_accepted_by_flask(self, http, auth_headers):
        response = http.get("/reports/productivity.pdf?team_id=1", headers=auth_headers)
        assert response.status_code == 200
        assert response.content[:4] == b"%PDF"

    def test_fastapi_rejects_missing_token(self, http):
        assert http.get("/api/tasks").status_code == 403

    def test_flask_rejects_missing_token(self, http):
        assert http.get("/reports/tasks.csv?team_id=1").status_code == 401

    def test_refreshed_token_also_works(self, http, tokens):
        refresh_response = http.post("/auth/token/refresh/", json={"refresh": tokens["refresh"]})
        assert refresh_response.status_code == 200
        new_access = refresh_response.json()["access"]

        response = http.get("/api/tasks", headers={"Authorization": f"Bearer {new_access}"})
        assert response.status_code == 200


class TestTaskFlowAcrossServices:
    def test_task_created_via_api_appears_in_csv_report(self, http, auth_headers, unique_title):
        me_teams = http.get("/auth/me/teams/", headers=auth_headers).json()
        team_id = me_teams[0]["team"]

        created = http.post(
            "/api/tasks",
            json={"title": unique_title, "project_id": 1, "priority": "high"},
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        task_id = created.json()["id"]

        try:
            csv_body = http.get(f"/reports/tasks.csv?team_id={team_id}", headers=auth_headers).text
            assert unique_title in csv_body
        finally:
            # CLEAN UP SO REPEATED RUNS DO NOT ACCUMULATE TASKS
            http.delete(f"/api/tasks/{task_id}", headers=auth_headers)

    def test_task_lifecycle_via_nginx(self, http, auth_headers, unique_title):
        created = http.post(
            "/api/tasks", json={"title": unique_title, "project_id": 1}, headers=auth_headers
        )
        assert created.status_code == 201
        task_id = created.json()["id"]

        patched = http.patch(f"/api/tasks/{task_id}", json={"status": "done"}, headers=auth_headers)
        assert patched.status_code == 200
        assert patched.json()["status"] == "done"

        assert http.delete(f"/api/tasks/{task_id}", headers=auth_headers).status_code == 204
        assert http.get(f"/api/tasks/{task_id}", headers=auth_headers).status_code == 404


class TestSwaggerThroughNginx:
    def test_swagger_ui_reachable(self, http):
        response = http.get("/api/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower()
