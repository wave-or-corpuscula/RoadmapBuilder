from backend.domain.skill_graph import SkillGraph


def test_from_file_creation():
    graph = SkillGraph()
    path = "backend/data.testing/skills.json"

    graph.from_json(path)