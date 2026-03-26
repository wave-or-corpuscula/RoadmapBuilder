from fastapi.testclient import TestClient

from backend.domain.skill_graph import SkillGraph
from backend.main import create_app


def _auth_context(client: TestClient, email: str = "u1@example.com") -> tuple[dict[str, str], str]:
    registered = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "supersecret", "display_name": "u1"},
    )
    token = registered.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    me = client.get("/api/v1/users/me", headers=headers)
    return headers, me.json()["id"]


def test_create_plan_surface_returns_expected_order():
    raw_graph = {
        "skills": [
            {"id": "a", "title": "", "description": "", "difficulty": 1, "prerequisites": []},
            {"id": "b", "title": "", "description": "", "difficulty": 1, "prerequisites": ["a"]},
            {"id": "goal", "title": "", "description": "", "difficulty": 1, "prerequisites": ["b"]},
        ]
    }
    app = create_app(graph=SkillGraph.from_dict(raw_graph))
    client = TestClient(app)
    headers, user_id = _auth_context(client)

    resp = client.post(
        "/api/v1/plans",
        json={
            "target_skill_ids": ["goal"],
            "mode": "surface",
            "mastered_skill_ids": [],
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"]
    assert body["user_id"] == user_id
    assert body["goal"]["target_skill_ids"] == ["goal"]
    assert body["goal"]["mode"] == "surface"
    assert body["ordered_skill_ids"] == ["a", "b", "goal"]
    assert body["skill_statuses"] == {"a": "unknown", "b": "unknown", "goal": "unknown"}


def test_get_import_template():
    raw_graph = {
        "skills": [
            {"id": "a", "title": "", "description": "", "difficulty": 1, "prerequisites": []},
        ]
    }
    app = create_app(graph=SkillGraph.from_dict(raw_graph))
    client = TestClient(app)
    headers, _ = _auth_context(client)

    resp = client.get("/api/v1/plans/import-template", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["schema_version"] == "1.0"
    assert "skills" in body
    assert "target_skill_ids" in body
    assert "mode" in body


def test_get_import_prompt():
    raw_graph = {
        "skills": [
            {"id": "a", "title": "", "description": "", "difficulty": 1, "prerequisites": []},
        ]
    }
    app = create_app(graph=SkillGraph.from_dict(raw_graph))
    client = TestClient(app)
    headers, _ = _auth_context(client)

    resp = client.post("/api/v1/plans/import-prompt", headers=headers, json={"topic": "Backend engineering"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["schema_version"] == "1.0"
    assert body["topic"] == "Backend engineering"
    assert '"Backend engineering"' in body["prompt"]


def test_import_plan_and_get_plan_graph():
    raw_graph = {
        "skills": [
            {"id": "a", "title": "", "description": "", "difficulty": 1, "prerequisites": []},
        ]
    }
    app = create_app(graph=SkillGraph.from_dict(raw_graph))
    client = TestClient(app)
    headers, _ = _auth_context(client)

    imported = client.post(
        "/api/v1/plans/import",
        headers=headers,
        json={
            "skills": [
                {"id": "x", "title": "X", "description": "", "difficulty": 1, "prerequisites": []},
                {"id": "y", "title": "Y", "description": "", "difficulty": 2, "prerequisites": ["x"]},
                {"id": "z", "title": "Z", "description": "", "difficulty": 3, "prerequisites": ["y"]},
            ],
            "target_skill_ids": ["z"],
            "mode": "surface",
            "mastered_skill_ids": [],
        },
    )
    assert imported.status_code == 200
    plan_id = imported.json()["id"]
    assert imported.json()["ordered_skill_ids"] == ["x", "y", "z"]

    graph = client.get(f"/api/v1/plans/{plan_id}/graph", headers=headers)
    assert graph.status_code == 200
    skill_ids = {item["id"] for item in graph.json()["skills"]}
    assert skill_ids == {"x", "y", "z"}


def test_imported_plan_allows_status_update_for_graph_nodes_not_in_ordered_list():
    raw_graph = {
        "skills": [
            {"id": "a", "title": "", "description": "", "difficulty": 1, "prerequisites": []},
        ]
    }
    app = create_app(graph=SkillGraph.from_dict(raw_graph))
    client = TestClient(app)
    headers, _ = _auth_context(client)

    payload = {
        "skills": [
            {"id": "a", "title": "A", "description": "", "difficulty": 1, "prerequisites": []},
            {"id": "b", "title": "B", "description": "", "difficulty": 2, "prerequisites": ["a"]},
            {"id": "goal", "title": "Goal", "description": "", "difficulty": 3, "prerequisites": ["b"]},
        ],
        "target_skill_ids": ["goal"],
        "mode": "surface",
    }

    first = client.post("/api/v1/plans/import", headers=headers, json=payload)
    assert first.status_code == 200
    first_plan_id = first.json()["id"]

    mark_mastered = client.patch(
        f"/api/v1/plans/{first_plan_id}/skills/a/status",
        headers=headers,
        json={"status": "mastered"},
    )
    assert mark_mastered.status_code == 200

    second = client.post("/api/v1/plans/import", headers=headers, json=payload)
    assert second.status_code == 200
    second_plan_id = second.json()["id"]
    assert "a" not in second.json()["ordered_skill_ids"]

    update_again = client.patch(
        f"/api/v1/plans/{second_plan_id}/skills/a/status",
        headers=headers,
        json={"status": "learning"},
    )
    assert update_again.status_code == 200
    assert update_again.json()["skill_statuses"]["a"] == "learning"


def test_imported_plan_keeps_mastered_status_for_nodes_outside_ordered_list():
    raw_graph = {
        "skills": [
            {"id": "seed", "title": "", "description": "", "difficulty": 1, "prerequisites": []},
        ]
    }
    app = create_app(graph=SkillGraph.from_dict(raw_graph))
    client = TestClient(app)
    headers, _ = _auth_context(client)

    payload = {
        "skills": [
            {"id": "a", "title": "A", "description": "", "difficulty": 1, "prerequisites": []},
            {"id": "b", "title": "B", "description": "", "difficulty": 2, "prerequisites": ["a"]},
            {"id": "goal", "title": "Goal", "description": "", "difficulty": 3, "prerequisites": ["b"]},
        ],
        "target_skill_ids": ["goal"],
        "mode": "surface",
    }

    first = client.post("/api/v1/plans/import", headers=headers, json=payload)
    assert first.status_code == 200
    first_plan_id = first.json()["id"]

    marked = client.patch(
        f"/api/v1/plans/{first_plan_id}/skills/a/status",
        headers=headers,
        json={"status": "mastered"},
    )
    assert marked.status_code == 200
    assert marked.json()["skill_statuses"]["a"] == "mastered"

    second = client.post("/api/v1/plans/import", headers=headers, json=payload)
    assert second.status_code == 200
    body = second.json()
    assert "a" not in body["ordered_skill_ids"]
    assert body["skill_statuses"]["a"] == "mastered"


def test_import_plan_rejects_unsupported_schema_version():
    raw_graph = {
        "skills": [
            {"id": "seed", "title": "", "description": "", "difficulty": 1, "prerequisites": []},
        ]
    }
    app = create_app(graph=SkillGraph.from_dict(raw_graph))
    client = TestClient(app)
    headers, _ = _auth_context(client)

    payload = {
        "schema_version": "9.9",
        "skills": [
            {"id": "a", "title": "A", "description": "", "difficulty": 1, "prerequisites": []},
            {"id": "goal", "title": "Goal", "description": "", "difficulty": 2, "prerequisites": ["a"]},
        ],
        "target_skill_ids": ["goal"],
        "mode": "surface",
    }

    imported = client.post("/api/v1/plans/import", headers=headers, json=payload)
    assert imported.status_code == 400
    assert "schema_version" in imported.json()["detail"]


def test_get_plan_by_id():
    raw_graph = {
        "skills": [
            {"id": "a", "title": "", "description": "", "difficulty": 1, "prerequisites": []},
            {"id": "goal", "title": "", "description": "", "difficulty": 1, "prerequisites": ["a"]},
        ]
    }
    app = create_app(graph=SkillGraph.from_dict(raw_graph))
    client = TestClient(app)
    headers, _ = _auth_context(client)

    created = client.post(
        "/api/v1/plans",
        json={"target_skill_ids": ["goal"], "mode": "surface"},
        headers=headers,
    )
    plan_id = created.json()["id"]

    got = client.get(f"/api/v1/plans/{plan_id}", headers=headers)
    assert got.status_code == 200
    assert got.json()["id"] == plan_id


def test_list_plans_returns_user_plans_only_ordered_desc():
    raw_graph = {
        "skills": [
            {"id": "a", "title": "", "description": "", "difficulty": 1, "prerequisites": []},
            {"id": "goal", "title": "", "description": "", "difficulty": 1, "prerequisites": ["a"]},
        ]
    }
    app = create_app(graph=SkillGraph.from_dict(raw_graph))
    client = TestClient(app)

    headers1, _ = _auth_context(client, email="u1@example.com")
    headers2, _ = _auth_context(client, email="u2@example.com")

    first = client.post(
        "/api/v1/plans",
        json={"target_skill_ids": ["goal"], "mode": "surface"},
        headers=headers1,
    )
    assert first.status_code == 200
    second = client.post(
        "/api/v1/plans",
        json={"target_skill_ids": ["goal"], "mode": "surface"},
        headers=headers1,
    )
    assert second.status_code == 200

    other = client.post(
        "/api/v1/plans",
        json={"target_skill_ids": ["goal"], "mode": "surface"},
        headers=headers2,
    )
    assert other.status_code == 200

    listed = client.get("/api/v1/plans", headers=headers1)
    assert listed.status_code == 200
    body = listed.json()
    assert len(body) == 2
    assert body[0]["id"] == second.json()["id"]
    assert body[1]["id"] == first.json()["id"]


def test_update_plan_skill_status():
    raw_graph = {
        "skills": [
            {"id": "a", "title": "", "description": "", "difficulty": 1, "prerequisites": []},
            {"id": "goal", "title": "", "description": "", "difficulty": 1, "prerequisites": ["a"]},
        ]
    }
    app = create_app(graph=SkillGraph.from_dict(raw_graph))
    client = TestClient(app)
    headers, _ = _auth_context(client)

    created = client.post(
        "/api/v1/plans",
        json={"target_skill_ids": ["goal"], "mode": "surface"},
        headers=headers,
    )
    plan_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/plans/{plan_id}/skills/a/status",
        json={"status": "mastered"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["skill_statuses"]["a"] == "mastered"

    progress = client.get("/api/v1/progress/me", headers=headers)
    assert progress.status_code == 200
    assert progress.json()["statuses"]["a"] == "mastered"


def test_rebuild_plan_keeps_id_and_excludes_mastered():
    raw_graph = {
        "skills": [
            {"id": "a", "title": "", "description": "", "difficulty": 1, "prerequisites": []},
            {"id": "b", "title": "", "description": "", "difficulty": 1, "prerequisites": ["a"]},
            {"id": "goal", "title": "", "description": "", "difficulty": 1, "prerequisites": ["b"]},
        ]
    }
    app = create_app(graph=SkillGraph.from_dict(raw_graph))
    client = TestClient(app)
    headers, _ = _auth_context(client)

    created = client.post(
        "/api/v1/plans",
        json={"target_skill_ids": ["goal"], "mode": "surface"},
        headers=headers,
    )
    plan_id = created.json()["id"]

    rebuilt = client.patch(
        f"/api/v1/plans/{plan_id}/rebuild",
        json={"mastered_skill_ids": ["a"]},
        headers=headers,
    )
    assert rebuilt.status_code == 200
    body = rebuilt.json()
    assert body["id"] == plan_id
    assert body["ordered_skill_ids"] == ["b", "goal"]


def test_create_plan_uses_global_progress_when_mastered_not_provided():
    raw_graph = {
        "skills": [
            {"id": "a", "title": "", "description": "", "difficulty": 1, "prerequisites": []},
            {"id": "b", "title": "", "description": "", "difficulty": 1, "prerequisites": ["a"]},
            {"id": "goal", "title": "", "description": "", "difficulty": 1, "prerequisites": ["b"]},
        ]
    }
    app = create_app(graph=SkillGraph.from_dict(raw_graph))
    client = TestClient(app)
    headers, _ = _auth_context(client)

    progress = client.patch("/api/v1/progress/skills/a/status", json={"status": "mastered"}, headers=headers)
    assert progress.status_code == 200

    created = client.post(
        "/api/v1/plans",
        json={"target_skill_ids": ["goal"], "mode": "surface"},
        headers=headers,
    )
    assert created.status_code == 200
    assert created.json()["ordered_skill_ids"] == ["b", "goal"]
