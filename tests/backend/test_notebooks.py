"""测试笔记本 CRUD 路由。"""

from __future__ import annotations


class TestListNotebooks:
    """GET /api/v1/notebooks"""

    def test_list(self, client):
        resp = client.get("/api/v1/notebooks")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "plan" in data
        assert "diary" in data

    def test_list_returns_names(self, client):
        resp = client.get("/api/v1/notebooks")
        names = resp.json()
        for nb in ["plan", "diary", "word", "accumulation", "aimemory", "timeline", "schedule"]:
            assert nb in names


class TestGetSchema:
    """GET /api/v1/notebooks/{name}/schema"""

    def test_get_schema(self, client):
        resp = client.get("/api/v1/notebooks/plan/schema")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["name"] == "id"

    def test_get_schema_not_found(self, client):
        resp = client.get("/api/v1/notebooks/nonexistent/schema")
        assert resp.status_code == 404
        assert "detail" in resp.json()


class TestQueryEntries:
    """GET /api/v1/notebooks/{name}/entries"""

    def test_query_with_defaults(self, client):
        resp = client.get("/api/v1/notebooks/plan/entries?view={}")
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "results" in data

    def test_query_with_view(self, client):
        import json
        view = json.dumps({"plan": [{"columns": ["content"], "filter": []}]})
        resp = client.get(f"/api/v1/notebooks/plan/entries?view={view}")
        assert resp.status_code == 200

    def test_query_not_found(self, client):
        resp = client.get("/api/v1/notebooks/nonexistent/entries?view={}")
        assert resp.status_code == 404


class TestAddEntries:
    """POST /api/v1/notebooks/{name}/entries"""

    def test_add(self, client):
        resp = client.post(
            "/api/v1/notebooks/plan/entries",
            json={"entries": [{"content": "新计划", "month": "2607"}]},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["count"] == 1
        assert len(data["results"]) == 1

    def test_add_multiple(self, client):
        resp = client.post(
            "/api/v1/notebooks/plan/entries",
            json={"entries": [
                {"content": "A", "month": "2607"},
                {"content": "B", "month": "2607"},
            ]},
        )
        assert resp.status_code == 201
        assert resp.json()["count"] == 2

    def test_add_invalid_notetype(self, client):
        resp = client.post(
            "/api/v1/notebooks/nonexistent/entries",
            json={"entries": [{"content": "x"}]},
        )
        assert resp.status_code == 404

    def test_add_missing_required(self, client):
        resp = client.post(
            "/api/v1/notebooks/plan/entries",
            json={"entries": [{}]},
        )
        assert resp.status_code == 422

    def test_add_empty_list(self, client):
        resp = client.post(
            "/api/v1/notebooks/plan/entries",
            json={"entries": []},
        )
        assert resp.status_code == 422  # min_length=1


class TestUpdateEntries:
    """PUT /api/v1/notebooks/{name}/entries"""

    def _add_plan(self, client) -> str:
        resp = client.post(
            "/api/v1/notebooks/plan/entries",
            json={"entries": [{"content": "旧计划", "month": "2607"}]},
        )
        return resp.json()["results"][0]["id"]

    def test_update(self, client):
        entry_id = self._add_plan(client)
        resp = client.put(
            "/api/v1/notebooks/plan/entries",
            json={"filter": [[{"column": "id", "op": "=", "value": entry_id}]], "values": {"content": "新计划"}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["results"][0]["content"] == "新计划"

    def test_update_not_found(self, client):
        resp = client.put(
            "/api/v1/notebooks/plan/entries",
            json={"filter": [[{"column": "id", "op": "=", "value": "nonexistent"}]], "values": {"content": "x"}},
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 0


class TestDeleteEntries:
    """DELETE /api/v1/notebooks/{name}/entries"""

    def _add_plan(self, client) -> str:
        resp = client.post(
            "/api/v1/notebooks/plan/entries",
            json={"entries": [{"content": "待删除", "month": "2607"}]},
        )
        return resp.json()["results"][0]["id"]

    def test_delete(self, client):
        entry_id = self._add_plan(client)
        resp = client.request(
            "DELETE", "/api/v1/notebooks/plan/entries",
            json={"filter": [[{"column": "id", "op": "=", "value": entry_id}]]},
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 1

    def test_delete_not_found(self, client):
        resp = client.request(
            "DELETE", "/api/v1/notebooks/plan/entries",
            json={"filter": [[{"column": "id", "op": "=", "value": "nonexistent"}]]},
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 0
