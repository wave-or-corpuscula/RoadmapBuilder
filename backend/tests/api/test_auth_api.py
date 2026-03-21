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


def test_register_login_refresh_flow():
    client = _make_client()

    registered = client.post(
        "/api/v1/auth/register",
        json={"email": "u1@example.com", "password": "supersecret", "display_name": "U1"},
    )
    assert registered.status_code == 201
    register_body = registered.json()
    assert register_body["token_type"] == "bearer"
    assert register_body["access_token"]
    assert register_body["refresh_token"]

    logged = client.post(
        "/api/v1/auth/login",
        json={"email": "u1@example.com", "password": "supersecret"},
    )
    assert logged.status_code == 200
    login_body = logged.json()
    assert login_body["access_token"]
    assert login_body["refresh_token"]

    refreshed = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login_body["refresh_token"]},
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]


def test_login_rejects_invalid_credentials():
    client = _make_client()
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "unknown@example.com", "password": "supersecret"},
    )
    assert resp.status_code == 401
