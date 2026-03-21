from fastapi.testclient import TestClient

from backend.domain.skill_graph import SkillGraph
from backend.main import create_app


def _make_client() -> TestClient:
    raw_graph = {
        "skills": [
            {"id": "a", "title": "", "description": "", "difficulty": 1, "prerequisites": []},
            {"id": "b", "title": "", "description": "", "difficulty": 1, "prerequisites": ["a"]},
            {"id": "goal", "title": "", "description": "", "difficulty": 1, "prerequisites": ["b"]},
        ]
    }
    return TestClient(create_app(graph=SkillGraph.from_dict(raw_graph)))


def _auth_headers(client: TestClient, email: str = "u1@example.com") -> dict[str, str]:
    registered = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "supersecret", "display_name": "u1"},
    )
    token = registered.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_progress_update_and_get():
    client = _make_client()
    headers = _auth_headers(client)

    updated = client.patch("/api/v1/progress/skills/a/status", json={"status": "mastered"}, headers=headers)
    assert updated.status_code == 200
    assert updated.json()["statuses"]["a"] == "mastered"

    fetched = client.get("/api/v1/progress/me", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["statuses"]["a"] == "mastered"


def test_progress_rejects_unknown_skill():
    client = _make_client()
    headers = _auth_headers(client)

    resp = client.patch(
        "/api/v1/progress/skills/unknown/status",
        json={"status": "learning"},
        headers=headers,
    )
    assert resp.status_code == 404
