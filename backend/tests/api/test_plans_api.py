from fastapi.testclient import TestClient

from backend.domain.skill_graph import SkillGraph
from backend.main import create_app


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

    resp = client.post(
        "/api/v1/plans",
        json={
            "user_id": "u1",
            "target_skill_ids": ["goal"],
            "mode": "surface",
            "mastered_skill_ids": [],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"]
    assert body["user_id"] == "u1"
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

    created = client.post(
        "/api/v1/plans",
        json={"user_id": "u1", "target_skill_ids": ["goal"], "mode": "surface"},
    )
    plan_id = created.json()["id"]

    got = client.get(f"/api/v1/plans/{plan_id}")
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

    created = client.post(
        "/api/v1/plans",
        json={"user_id": "u1", "target_skill_ids": ["goal"], "mode": "surface"},
    )
    plan_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/plans/{plan_id}/skills/a/status",
        json={"status": "mastered"},
    )
    assert updated.status_code == 200
    assert updated.json()["skill_statuses"]["a"] == "mastered"

    progress = client.get("/api/v1/progress/u1")
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

    created = client.post(
        "/api/v1/plans",
        json={"user_id": "u1", "target_skill_ids": ["goal"], "mode": "surface"},
    )
    plan_id = created.json()["id"]

    rebuilt = client.patch(
        f"/api/v1/plans/{plan_id}/rebuild",
        json={"mastered_skill_ids": ["a"]},
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

    progress = client.patch("/api/v1/progress/u1/skills/a/status", json={"status": "mastered"})
    assert progress.status_code == 200

    created = client.post(
        "/api/v1/plans",
        json={"user_id": "u1", "target_skill_ids": ["goal"], "mode": "surface"},
    )
    assert created.status_code == 200
    assert created.json()["ordered_skill_ids"] == ["b", "goal"]
