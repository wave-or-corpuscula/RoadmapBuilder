from fastapi.testclient import TestClient

from backend.domain.skill_graph import SkillGraph
from backend.main import create_app


def _make_client() -> TestClient:
    raw_graph = {
        "skills": [
            {"id": "a", "title": "", "description": "", "difficulty": 1, "prerequisites": []},
        ]
    }
    return TestClient(create_app(graph=SkillGraph.from_dict(raw_graph)))


def test_get_me_creates_default_user():
    client = _make_client()

    resp = client.get("/api/v1/users/me", headers={"X-User-Id": "u1"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "u1"
    assert body["email"] == "u1@local.dev"
    assert body["display_name"] == "u1"


def test_patch_me_updates_user():
    client = _make_client()

    updated = client.patch(
        "/api/v1/users/me",
        headers={"X-User-Id": "u1"},
        json={"email": "u1@example.com", "display_name": "Andrey"},
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["email"] == "u1@example.com"
    assert body["display_name"] == "Andrey"

    fetched = client.get("/api/v1/users/me", headers={"X-User-Id": "u1"})
    assert fetched.status_code == 200
    assert fetched.json()["email"] == "u1@example.com"
    assert fetched.json()["display_name"] == "Andrey"


def test_get_me_requires_header():
    client = _make_client()

    resp = client.get("/api/v1/users/me")
    assert resp.status_code == 400
