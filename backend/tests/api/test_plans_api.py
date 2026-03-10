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
