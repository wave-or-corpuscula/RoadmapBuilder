import pytest

from app.core.graph_engine import SkillGraph
from app.core.knowledge_engine import KnowledgeEngine, SkillStatus

from app.tests.test_graph_engine import simple_graph_json, build_graph


@pytest.fixture
def simple_knowladge_engine(simple_graph_json) -> KnowledgeEngine:
    graph = build_graph(simple_graph_json)
    know = KnowledgeEngine(graph)

    return know


def test_set_status(simple_knowladge_engine):
    know = simple_knowladge_engine

    root = next(iter(know.graph.get_roots()))
    know.set_status(root, SkillStatus.MASTERED)

    assert know.user_status[root] is SkillStatus.MASTERED


def test_get_status(simple_knowladge_engine):
    know = simple_knowladge_engine

    root = next(iter(know.graph.get_roots()))

    assert know.get_status(root) is SkillStatus.UNKNOWN
    
    know.set_status(root, SkillStatus.LEARNING)
    assert know.get_status(root) is SkillStatus.LEARNING


def test_root_skill_available(simple_knowladge_engine):
    know = simple_knowladge_engine
    root = next(iter(know.graph.get_roots()))

    assert know.is_skill_available(root) is True

    know.set_status(root, SkillStatus.MASTERED)

    assert know.is_skill_available(root) is False


def test_skill_avaliability():
    data = {
        "skills": [
            { "id": "A", "title": "A", "description": "", "difficulty": 1, "prerequisites": [] },
            { "id": "B", "title": "B", "description": "", "difficulty": 1, "prerequisites": ["A"] },
            { "id": "C", "title": "C", "description": "", "difficulty": 1, "prerequisites": ["A"] },
            { "id": "D", "title": "D", "description": "", "difficulty": 1, "prerequisites": ["A"] },
            { "id": "E", "title": "E", "description": "", "difficulty": 1, "prerequisites": ["B", "C", "D"] },
        ]
    }

    graph = build_graph(data)
    know = KnowledgeEngine(graph)

    know.set_status("A", SkillStatus.MASTERED)
    know.set_status("B", SkillStatus.MASTERED)
    know.set_status("C", SkillStatus.MASTERED)

    assert know.is_skill_available("E") is False

    know.set_status("D", SkillStatus.MASTERED)

    assert know.is_skill_available("E") is True


def test_get_available():
    data = {
        "skills": [
            { "id": "A", "title": "A", "description": "", "difficulty": 1, "prerequisites": [] },
            { "id": "B", "title": "B", "description": "", "difficulty": 1, "prerequisites": ["A"] },
            { "id": "C", "title": "C", "description": "", "difficulty": 1, "prerequisites": ["A"] },
            { "id": "D", "title": "D", "description": "", "difficulty": 1, "prerequisites": ["A"] },
            { "id": "E", "title": "E", "description": "", "difficulty": 1, "prerequisites": ["B", "C", "D"] },
        ]
    }

    graph = build_graph(data)
    know = KnowledgeEngine(graph)

    assert know.get_available_skills() == {"A"}

    know.set_status("A", SkillStatus.MASTERED)

    assert know.get_available_skills() == {"B", "C", "D"}

    know.set_status("C", SkillStatus.MASTERED)

    assert know.get_available_skills() == {"B", "D"}

    know.set_status("B", SkillStatus.MASTERED)
    know.set_status("D", SkillStatus.MASTERED)
    know.set_status("E", SkillStatus.MASTERED)

    assert len(know.get_available_skills()) == 0


def test_gap_analysis():
    data = {
        "skills": [
            { "id": "A", "title": "A", "description": "A", "difficulty": 1, "prerequisites": [] },
            { "id": "B", "title": "B", "description": "B", "difficulty": 1, "prerequisites": ["A"] },
            { "id": "C", "title": "C", "description": "C", "difficulty": 1, "prerequisites": ["A"] },
            { "id": "D", "title": "D", "description": "D", "difficulty": 1, "prerequisites": ["A"] },
            { "id": "E", "title": "E", "description": "E", "difficulty": 1, "prerequisites": ["B", "C", "D"] },
        ]
    }



    graph = build_graph(data)
    know = KnowledgeEngine(graph)

    assert know.gap_analysis("E") == {"A","B","C","D", "E"}

    know.set_status("E", SkillStatus.MASTERED)
    know.set_status("B", SkillStatus.MASTERED)
    assert know.gap_analysis("E") == {"A","C","D"}

    know.set_status("A", SkillStatus.MASTERED)
    know.set_status("C", SkillStatus.MASTERED)
    know.set_status("D", SkillStatus.MASTERED)

    assert know.gap_analysis("E") == set()

def test_next_best_skill():
    data = {
        "skills": [
            { "id": "A", "title": "A", "description": "", "difficulty": 5, "prerequisites": [] },
            { "id": "B", "title": "B", "description": "", "difficulty": 1, "prerequisites": ["A"] },
            { "id": "C", "title": "C", "description": "", "difficulty": 2, "prerequisites": ["A"] },
        ]
    }

    graph = build_graph(data)
    know = KnowledgeEngine(graph)

    # Сначала доступен только A
    assert know.get_next_best_skill() == "A"

    know.set_status("A", SkillStatus.MASTERED)

    # Теперь доступны B и C
    # depth одинаковый, выбирается по difficulty
    assert know.get_next_best_skill() == "B"

