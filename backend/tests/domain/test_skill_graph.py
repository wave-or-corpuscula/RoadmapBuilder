import json

import pytest
from pytest import raises

from backend.domain.skill_graph import SkillGraph


skills_path = "backend/tests/data/skills.json"


@pytest.fixture
def graph_from_json():
    return SkillGraph.from_json(skills_path)


@pytest.fixture
def sample_graph():
    raw_graph = {
        "skills": [
            {
                "id": "python_basics",
                "title": "Python Basics",
                "description": "Basic syntax and data types",
                "difficulty": 1,
                "prerequisites": []
            },
            {
                "id": "functions",
                "title": "Functions",
                "description": "Function definition and scope",
                "difficulty": 2,
                "prerequisites": ["python_basics"]
            },
            {
                "id": "decorators",
                "title": "Decorators",
                "description": "Function decorators",
                "difficulty": 3,
                "prerequisites": ["functions"]
            },
            {
                "id": "async_advanced",
                "title": "Async Advanced",
                "description": "Advanced asyncio patterns",
                "difficulty": 5,
                "prerequisites": ["decorators"]
            },
            {
                "id": "data_structures",
                "title": "Data Structures",
                "description": "Lists, dicts, sets",
                "difficulty": 2,
                "prerequisites": ["python_basics"]
            },
            {
                "id": "algorithms",
                "title": "Algorithms",
                "description": "Common algorithms",
                "difficulty": 4,
                "prerequisites": ["data_structures", "functions"]
            }
        ]
    }
    return SkillGraph.from_dict(raw_graph)


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


def test_get_transitive_deps_single_chain(sample_graph):
    """Linear chain of dependencies."""
    deps = sample_graph.get_transitive_deps("async_advanced")
    assert deps == {"decorators", "functions", "python_basics"}


def test_get_transitive_deps_multiple_branches(sample_graph):
    """Skill with dependencies from different branches."""
    deps = sample_graph.get_transitive_deps("algorithms")
    assert deps == {"data_structures", "python_basics", "functions"}


def test_get_transitive_deps_no_dependencies(sample_graph):
    """Skill with no prerequisites."""
    deps = sample_graph.get_transitive_deps("python_basics")
    assert deps == set()


def test_get_transitive_deps_nonexistent_skill(sample_graph):
    """Non-existent skill ID."""
    deps = sample_graph.get_transitive_deps("nonexistent")
    assert deps == set()


def test_create_graph_with_missing_prereq():
    """Create graph with a non-existent prerequisite."""
    raw_graph = {
        "skills": [
            {
                "id": "skill_a",
                "title": "Skill A",
                "description": "",
                "difficulty": 1,
                "prerequisites": []
            },
            {
                "id": "skill_b",
                "title": "Skill B",
                "description": "",
                "difficulty": 2,
                "prerequisites": ["skill_a", "nonexistent"]
            }
        ]
    }

    with raises(ValueError):
        SkillGraph.from_dict(raw_graph)
    


def test_get_transitive_deps_complex_graph():
    """Complex graph with overlapping dependencies."""
    raw_graph = {
        "skills": [
            {
                "id": "A",
                "title": "Skill A",
                "description": "",
                "difficulty": 1,
                "prerequisites": []
            },
            {
                "id": "B",
                "title": "Skill B",
                "description": "",
                "difficulty": 2,
                "prerequisites": ["A"]
            },
            {
                "id": "C",
                "title": "Skill C",
                "description": "",
                "difficulty": 2,
                "prerequisites": ["A"]
            },
            {
                "id": "D",
                "title": "Skill D",
                "description": "",
                "difficulty": 3,
                "prerequisites": ["B", "C"]
            },
            {
                "id": "E",
                "title": "Skill E",
                "description": "",
                "difficulty": 4,
                "prerequisites": ["D"]
            }
        ]
    }
    graph = SkillGraph.from_dict(raw_graph)
    
    deps = graph.get_transitive_deps("E")
    assert deps == {"D", "B", "C", "A"}


def test_get_transitive_deps_does_not_include_self(sample_graph):
    """Method should not include the skill itself in results."""
    deps = sample_graph.get_transitive_deps("decorators")
    assert "decorators" not in deps
    assert deps == {"functions", "python_basics"}


def test_get_transitive_deps_order_does_not_matter(sample_graph):
    """Return order doesn't matter, only the set content."""
    deps1 = sample_graph.get_transitive_deps("algorithms")
    deps2 = sample_graph.get_transitive_deps("algorithms")
    
    # Sets should be identical
    assert deps1 == deps2


def test_get_transitive_deps_deep_nesting():
    """Deep nested dependencies."""
    raw_graph = {
        "skills": [
            {
                "id": "1",
                "title": "Level 1",
                "description": "",
                "difficulty": 1,
                "prerequisites": []
            },
            {
                "id": "2",
                "title": "Level 2",
                "description": "",
                "difficulty": 2,
                "prerequisites": ["1"]
            },
            {
                "id": "3",
                "title": "Level 3",
                "description": "",
                "difficulty": 3,
                "prerequisites": ["2"]
            },
            {
                "id": "4",
                "title": "Level 4",
                "description": "",
                "difficulty": 4,
                "prerequisites": ["3"]
            },
            {
                "id": "5",
                "title": "Level 5",
                "description": "",
                "difficulty": 5,
                "prerequisites": ["4"]
            }
        ]
    }
    graph = SkillGraph.from_dict(raw_graph)
    
    deps = graph.get_transitive_deps("5")
    print(deps)
    assert deps == {"4", "3", "2", "1"}