from fastapi.testclient import TestClient

from backend.domain.skill_graph import SkillGraph
from backend.main import create_app


def _make_client() -> TestClient:
    raw_graph = {
        "skills": [
            {"id": "a", "title": "A", "description": "", "difficulty": 1, "prerequisites": []},
            {"id": "b", "title": "B", "description": "", "difficulty": 2, "prerequisites": ["a"]},
            {"id": "goal", "title": "Goal", "description": "", "difficulty": 3, "prerequisites": ["b"]},
        ]
    }
    app = create_app(graph=SkillGraph.from_dict(raw_graph))
    return TestClient(app)


def test_create_skill_and_list():
    client = _make_client()

    created = client.post(
        "/api/v1/skills",
        json={
            "id": "c",
            "title": "C",
            "description": "",
            "difficulty": 2,
            "prerequisites": ["a"],
        },
    )
    assert created.status_code == 201
    assert created.json()["id"] == "c"

    listed = client.get("/api/v1/skills")
    assert listed.status_code == 200
    skill_ids = [item["id"] for item in listed.json()]
    assert set(skill_ids) == {"a", "b", "goal", "c"}


def test_update_skill_rejects_cycle():
    client = _make_client()

    resp = client.patch("/api/v1/skills/a", json={"prerequisites": ["goal"]})
    assert resp.status_code == 400
    assert "cycle" in resp.json()["detail"].lower()


def test_delete_skill_conflict_and_force():
    client = _make_client()

    conflict = client.delete("/api/v1/skills/b")
    assert conflict.status_code == 409

    forced = client.delete("/api/v1/skills/b?force=true")
    assert forced.status_code == 204

    graph = client.get("/api/v1/graph")
    assert graph.status_code == 200
    skills = {item["id"] for item in graph.json()["skills"]}
    assert "b" not in skills


def test_validate_graph_endpoint():
    client = _make_client()

    valid_resp = client.post(
        "/api/v1/graph/validate",
        json={
            "skills": [
                {"id": "x", "title": "", "description": "", "difficulty": 1, "prerequisites": []}
            ]
        },
    )
    assert valid_resp.status_code == 200
    assert valid_resp.json() == {"valid": True}

    invalid_resp = client.post(
        "/api/v1/graph/validate",
        json={
            "skills": [
                {
                    "id": "x",
                    "title": "",
                    "description": "",
                    "difficulty": 1,
                    "prerequisites": ["missing"],
                }
            ]
        },
    )
    assert invalid_resp.status_code == 400
