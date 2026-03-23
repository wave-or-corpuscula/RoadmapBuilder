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
