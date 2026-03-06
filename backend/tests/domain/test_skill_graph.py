import json

from pytest import raises

from backend.domain.skill_graph import SkillGraph


skills_path = "backend/data.testing/skills.json"


def test_graph_from_json_creation():

    with open(skills_path) as file:
        data = json.load(file)

    graph = SkillGraph.from_json(skills_path)
    assert len(graph.skills) > 0
    
    for skill in data["skills"]:
        assert skill["id"] in graph.skills


def test_cycle_detected():

    raw_graph = {
        "skills": [
            {"id": "1", "title": "", "description": "", "difficulty": 1, "prerequisites": ["6"]},
            {"id": "2", "title": "", "description": "", "difficulty": 1, "prerequisites": ["1"]},
            {"id": "3", "title": "", "description": "", "difficulty": 1, "prerequisites": ["1"]},
            {"id": "4", "title": "", "description": "", "difficulty": 1, "prerequisites": ["2", "3"]},
            {"id": "5", "title": "", "description": "", "difficulty": 1, "prerequisites": ["2", "3"]},
            {"id": "6", "title": "", "description": "", "difficulty": 1, "prerequisites": ["4", "5"]},
        ]
    }
    with raises(ValueError):
        SkillGraph.from_dict(raw_graph)