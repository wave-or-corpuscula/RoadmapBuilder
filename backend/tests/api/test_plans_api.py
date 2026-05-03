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
    assert body["title"]
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
            "title": "Backend Core Plan",
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
    assert imported.json()["title"] == "Backend Core Plan"
    assert imported.json()["fingerprint"]
    assert imported.json()["ordered_skill_ids"] == ["x", "y", "z"]

    graph = client.get(f"/api/v1/plans/{plan_id}/graph", headers=headers)
    assert graph.status_code == 200
    skill_ids = {item["id"] for item in graph.json()["skills"]}
    assert skill_ids == {"x", "y", "z"}


def test_import_same_payload_reuses_existing_plan_by_fingerprint():
    raw_graph = {
        "skills": [
            {"id": "seed", "title": "", "description": "", "difficulty": 1, "prerequisites": []},
        ]
    }
    app = create_app(graph=SkillGraph.from_dict(raw_graph))
    client = TestClient(app)
    headers, _ = _auth_context(client)

    payload = {
        "schema_version": "1.0",
        "title": "Data Engineering Plan",
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
    first_id = first.json()["id"]
    first_fingerprint = first.json()["fingerprint"]

    second = client.post("/api/v1/plans/import", headers=headers, json=payload)
    assert second.status_code == 200
    assert second.json()["id"] == first_id
    assert second.json()["fingerprint"] == first_fingerprint

    listed = client.get("/api/v1/plans", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1


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


def test_update_plan_title():
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
        json={"target_skill_ids": ["goal"], "mode": "surface", "mastered_skill_ids": []},
        headers=headers,
    )
    assert created.status_code == 200
    plan_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/plans/{plan_id}/title",
        json={"title": "Новый план по API"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Новый план по API"

    fetched = client.get(f"/api/v1/plans/{plan_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "Новый план по API"


def test_derive_plan_creates_child_with_hierarchy_links():
    raw_graph = {
        "skills": [
            {"id": "a", "title": "A", "description": "", "difficulty": 1, "prerequisites": []},
            {"id": "b", "title": "B", "description": "", "difficulty": 2, "prerequisites": ["a"]},
            {"id": "goal", "title": "Goal", "description": "", "difficulty": 3, "prerequisites": ["b"]},
        ]
    }
    app = create_app(graph=SkillGraph.from_dict(raw_graph))
    client = TestClient(app)
    headers, _ = _auth_context(client)

    created = client.post(
        "/api/v1/plans",
        json={"target_skill_ids": ["goal"], "mode": "surface", "mastered_skill_ids": []},
        headers=headers,
    )
    assert created.status_code == 200
    parent = created.json()

    derived = client.post(
        f"/api/v1/plans/{parent['id']}/derive",
        json={"skill_id": "b"},
        headers=headers,
    )
    assert derived.status_code == 200
    body = derived.json()
    assert body["parent_plan_id"] == parent["id"]
    assert body["root_plan_id"] == parent["id"]
    assert body["source_skill_id"] == "b"
    assert body["title"] == "B"

    listed = client.get("/api/v1/plans", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 2


def test_derive_plan_rejects_root_skill():
    raw_graph = {
        "skills": [
            {"id": "a", "title": "A", "description": "", "difficulty": 1, "prerequisites": []},
            {"id": "b", "title": "B", "description": "", "difficulty": 2, "prerequisites": ["a"]},
            {"id": "goal", "title": "Goal", "description": "", "difficulty": 3, "prerequisites": ["b"]},
        ]
    }
    app = create_app(graph=SkillGraph.from_dict(raw_graph))
    client = TestClient(app)
    headers, _ = _auth_context(client)

    created = client.post(
        "/api/v1/plans",
        json={"target_skill_ids": ["goal"], "mode": "surface", "mastered_skill_ids": []},
        headers=headers,
    )
    assert created.status_code == 200
    parent_id = created.json()["id"]

    derived = client.post(
        f"/api/v1/plans/{parent_id}/derive",
        json={"skill_id": "a"},
        headers=headers,
    )
    assert derived.status_code == 400
    assert "Root skill" in derived.json()["detail"]


def test_updating_status_in_child_plan_updates_parent_plan():
    raw_graph = {
        "skills": [
            {"id": "a", "title": "A", "description": "", "difficulty": 1, "prerequisites": []},
            {"id": "b", "title": "B", "description": "", "difficulty": 2, "prerequisites": ["a"]},
            {"id": "goal", "title": "Goal", "description": "", "difficulty": 3, "prerequisites": ["b"]},
        ]
    }
    app = create_app(graph=SkillGraph.from_dict(raw_graph))
    client = TestClient(app)
    headers, _ = _auth_context(client)

    parent_created = client.post(
        "/api/v1/plans",
        json={"target_skill_ids": ["goal"], "mode": "surface", "mastered_skill_ids": []},
        headers=headers,
    )
    assert parent_created.status_code == 200
    parent_id = parent_created.json()["id"]

    child_created = client.post(
        f"/api/v1/plans/{parent_id}/derive",
        json={"skill_id": "b"},
        headers=headers,
    )
    assert child_created.status_code == 200
    child_id = child_created.json()["id"]

    changed = client.patch(
        f"/api/v1/plans/{child_id}/skills/b/status",
        json={"status": "mastered"},
        headers=headers,
    )
    assert changed.status_code == 200
    assert changed.json()["skill_statuses"]["b"] == "mastered"

    parent_after = client.get(f"/api/v1/plans/{parent_id}", headers=headers)
    assert parent_after.status_code == 200
    assert parent_after.json()["skill_statuses"]["b"] == "mastered"


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


def test_update_plan_skill_note():
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
        f"/api/v1/plans/{plan_id}/skills/a/note",
        json={"note": "## Focus\n- practice daily"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["skill_notes"]["a"] == "## Focus\n- practice daily"


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


def test_list_next_steps_returns_next_skill_for_each_plan():
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
    assert created.status_code == 200
    plan_id = created.json()["id"]

    steps_initial = client.get("/api/v1/plans/next-steps", headers=headers)
    assert steps_initial.status_code == 200
    by_plan_initial = {item["plan_id"]: item["next_skill_id"] for item in steps_initial.json()}
    assert by_plan_initial[plan_id] == "a"

    mark_a = client.patch(
        f"/api/v1/plans/{plan_id}/skills/a/status",
        json={"status": "mastered"},
        headers=headers,
    )
    assert mark_a.status_code == 200

    steps_after_a = client.get("/api/v1/plans/next-steps", headers=headers)
    assert steps_after_a.status_code == 200
    by_plan_after_a = {item["plan_id"]: item["next_skill_id"] for item in steps_after_a.json()}
    assert by_plan_after_a[plan_id] == "b"

    mark_b = client.patch(
        f"/api/v1/plans/{plan_id}/skills/b/status",
        json={"status": "mastered"},
        headers=headers,
    )
    assert mark_b.status_code == 200
    mark_goal = client.patch(
        f"/api/v1/plans/{plan_id}/skills/goal/status",
        json={"status": "mastered"},
        headers=headers,
    )
    assert mark_goal.status_code == 200

    steps_done = client.get("/api/v1/plans/next-steps", headers=headers)
    assert steps_done.status_code == 200
    by_plan_done = {item["plan_id"]: item["next_skill_id"] for item in steps_done.json()}
    assert by_plan_done[plan_id] is None


def test_list_next_steps_returns_first_learning_when_no_unknown_available():
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
    assert created.status_code == 200
    plan_id = created.json()["id"]

    for skill_id in ["a", "b", "goal"]:
        updated = client.patch(
            f"/api/v1/plans/{plan_id}/skills/{skill_id}/status",
            json={"status": "learning"},
            headers=headers,
        )
        assert updated.status_code == 200

    steps = client.get("/api/v1/plans/next-steps", headers=headers)
    assert steps.status_code == 200
    by_plan = {item["plan_id"]: item["next_skill_id"] for item in steps.json()}
    assert by_plan[plan_id] == "a"
