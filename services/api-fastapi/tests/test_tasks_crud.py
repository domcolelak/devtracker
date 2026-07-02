class TestAuthRequired:
    def test_list_requires_token(self, client):
        assert client.get("/tasks").status_code == 403

    def test_create_requires_token(self, client):
        assert client.post("/tasks", json={"title": "x", "project_id": 1}).status_code == 403


class TestCreateTask:
    def test_create_sets_defaults_and_creator(self, client, auth_headers):
        response = client.post(
            "/tasks",
            json={"title": "Write architecture docs", "project_id": 1, "priority": "high"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        task = response.json()
        assert task["status"] == "todo"
        assert task["priority"] == "high"
        assert task["created_by_id"] == 7
        assert task["project_id"] == 1

    def test_unknown_project_rejected(self, client, auth_headers):
        response = client.post(
            "/tasks", json={"title": "Ghost", "project_id": 999}, headers=auth_headers
        )
        assert response.status_code == 404

    def test_empty_title_rejected(self, client, auth_headers):
        response = client.post("/tasks", json={"title": "", "project_id": 1}, headers=auth_headers)
        assert response.status_code == 422

    def test_invalid_status_rejected(self, client, auth_headers):
        response = client.post(
            "/tasks",
            json={"title": "x", "project_id": 1, "status": "not-a-status"},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestReadTasks:
    def test_list_and_filter_by_status(self, client, auth_headers):
        client.post("/tasks", json={"title": "A", "project_id": 1}, headers=auth_headers)
        client.post(
            "/tasks",
            json={"title": "B", "project_id": 1, "status": "done"},
            headers=auth_headers,
        )

        all_tasks = client.get("/tasks", headers=auth_headers).json()
        assert len(all_tasks) == 2

        done_tasks = client.get("/tasks?status=done", headers=auth_headers).json()
        assert len(done_tasks) == 1
        assert done_tasks[0]["title"] == "B"

    def test_get_single_task(self, client, auth_headers):
        created = client.post(
            "/tasks", json={"title": "A", "project_id": 1}, headers=auth_headers
        ).json()
        response = client.get(f"/tasks/{created['id']}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["title"] == "A"

    def test_get_missing_task_404(self, client, auth_headers):
        assert client.get("/tasks/9999", headers=auth_headers).status_code == 404


class TestUpdateTask:
    def test_patch_status(self, client, auth_headers):
        created = client.post(
            "/tasks", json={"title": "A", "project_id": 1}, headers=auth_headers
        ).json()
        response = client.patch(
            f"/tasks/{created['id']}", json={"status": "in_progress"}, headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "in_progress"
        # UNTOUCHED FIELDS ARE PRESERVED
        assert response.json()["title"] == "A"

    def test_patch_missing_task_404(self, client, auth_headers):
        response = client.patch("/tasks/9999", json={"status": "done"}, headers=auth_headers)
        assert response.status_code == 404


class TestDeleteTask:
    def test_delete_then_404(self, client, auth_headers):
        created = client.post(
            "/tasks", json={"title": "A", "project_id": 1}, headers=auth_headers
        ).json()
        assert client.delete(f"/tasks/{created['id']}", headers=auth_headers).status_code == 204
        assert client.get(f"/tasks/{created['id']}", headers=auth_headers).status_code == 404

    def test_delete_missing_task_404(self, client, auth_headers):
        assert client.delete("/tasks/9999", headers=auth_headers).status_code == 404
