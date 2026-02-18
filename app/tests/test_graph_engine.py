import json
import tempfile
import pytest

from typing import Callable

from app.core.models import Skill
from app.core.graph_engine import SkillGraph


@pytest.fixture
def simple_graph_json():
    return {
        "skills": [
            {
                "id": "A",
                "title": "A",
                "description": "",
                "difficulty": 1,
                "prerequisites": []
            },
            {
                "id": "B",
                "title": "B",
                "description": "",
                "difficulty": 1,
                "prerequisites": ["A"]
            },
            {
                "id": "C",
                "title": "C",
                "description": "",
                "difficulty": 1,
                "prerequisites": ["B"]
            }
        ]
    }



def build_graph(data) -> SkillGraph:
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
        json.dump(data, f)
        f.flush()
        return SkillGraph.from_json(f.name)


def test_topological_sort(simple_graph_json):
    graph = build_graph(simple_graph_json)
    order = graph.topological_sort()

    assert order == ["A", "B", "C"]


def test_transitive_prerequisites(simple_graph_json):
    graph = build_graph(simple_graph_json)

    prereqs = graph.get_transitive_prerequisites("C")

    assert prereqs == {"A", "B"}


def test_cycle_detection():
    data = {
        "skills": [
            {
                "id": "A",
                "title": "A",
                "description": "",
                "difficulty": 1,
                "prerequisites": ["B"]
            },
            {
                "id": "B",
                "title": "B",
                "description": "",
                "difficulty": 1,
                "prerequisites": ["A"]
            }
        ]
    }

    with pytest.raises(ValueError):
        build_graph(data)

@pytest.fixture
def skill_factory() -> Callable[[str], Skill]:
    def _factory(skill_id: str) -> Skill:
        return Skill(
            id=skill_id,
            title=f"{skill_id} title",
            description=f"{skill_id} description",
            difficulty=1,
        )
    return _factory

def test_add_new_skill(simple_graph_json, skill_factory):
    graph = build_graph(simple_graph_json)
    before_len = len(graph.skills)

    new_skill = skill_factory("New skill")
    graph.add_skill(new_skill)
    
    assert new_skill.id in graph.skills
    assert len(graph.skills) == before_len + 1
    assert graph.get_prerequisites(new_skill.id) == set()
    assert graph.get_dependents(new_skill.id) == set()

def test_add_same_skill(simple_graph_json, skill_factory):
    graph = build_graph(simple_graph_json)
    before_keys = list(graph.skills.keys())

    same_skill = skill_factory(before_keys[0])
    
    with pytest.raises(ValueError):
        graph.add_skill(same_skill)


def test_add_prerequisite(simple_graph_json, skill_factory):
    graph = build_graph(simple_graph_json)

    root = next(iter(graph.get_roots()))
    
    s1 = skill_factory("s1")
    graph.add_skill(s1)

    print(graph.get_roots())
    print(root)

    graph.add_prerequisite(s1.id, root)

    assert root in graph.get_prerequisites(s1.id)
    assert s1.id in graph.get_dependents(root)

def test_cycle_detection_on_add(simple_graph_json):
    graph = build_graph(simple_graph_json)

    order = graph.topological_sort()
    first = order[0]
    last = order[-1]

    with pytest.raises(ValueError):
        graph.add_prerequisite(first, last)

def test_depth_root_is_zero(simple_graph_json):
    graph = build_graph(simple_graph_json)

    for root in graph.get_roots():
        assert graph.calculate_depth(root) == 0

def test_depth_linear_chain():
    data = {
        "skills": [
            {"id": "A", "title": "", "description": "", "difficulty": 1, "prerequisites": []},
            {"id": "B", "title": "", "description": "", "difficulty": 1, "prerequisites": ["A"]},
            {"id": "C", "title": "", "description": "", "difficulty": 1, "prerequisites": ["B"]},
        ]
    }

    graph = build_graph(data)

    assert graph.calculate_depth("A") == 0
    assert graph.calculate_depth("B") == 1
    assert graph.calculate_depth("C") == 2


def test_depth_cache():
    data = {
        "skills": [
            {"id": "A", "title": "", "description": "", "difficulty": 1, "prerequisites": []},
            {"id": "B", "title": "", "description": "", "difficulty": 1, "prerequisites": ["A"]},
            {"id": "C", "title": "", "description": "", "difficulty": 1, "prerequisites": ["A"]},
            {"id": "D", "title": "", "description": "", "difficulty": 1, "prerequisites": ["C", "B"]},
            {"id": "E", "title": "", "description": "", "difficulty": 1, "prerequisites": ["D"]},
        ]
    }

    graph = build_graph(data)
    assert graph.calculate_depth("E") == 3
