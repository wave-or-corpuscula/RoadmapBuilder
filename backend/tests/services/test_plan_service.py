import pytest

from backend.domain.enums import KnowledgeStatus
from backend.domain.enums import LearningMode
from backend.domain.learning_goal import LearningGoal
from backend.domain.skill_graph import SkillGraph
from backend.domain.user_knowledge import UserKnowledge
from backend.domain.learning_plan import LearningPlan
from backend.services.plan_service import PlanService


branchy_graph_path = "backend/tests/data/branchy_skills.json"


@pytest.fixture
def plan_service():
    return PlanService()

@pytest.fixture
def branchy_graph():
    return SkillGraph.from_json(branchy_graph_path)


@pytest.fixture
def sample_graph():
    raw_graph = {
        "skills": [
            {
                "id": "python_basics",
                "title": "Python Basics",
                "description": "",
                "difficulty": 1,
                "prerequisites": [],
            },
            {
                "id": "functions",
                "title": "Functions",
                "description": "",
                "difficulty": 2,
                "prerequisites": ["python_basics"],
            },
            {
                "id": "decorators",
                "title": "Decorators",
                "description": "",
                "difficulty": 3,
                "prerequisites": ["functions"],
            },
            {
                "id": "async_advanced",
                "title": "Async Advanced",
                "description": "",
                "difficulty": 5,
                "prerequisites": ["decorators"],
            },
            {
                "id": "data_structures",
                "title": "Data Structures",
                "description": "",
                "difficulty": 2,
                "prerequisites": ["python_basics"],
            },
            {
                "id": "algorithms",
                "title": "Algorithms",
                "description": "",
                "difficulty": 4,
                "prerequisites": ["data_structures", "functions"],
            },
        ]
    }
    return SkillGraph.from_dict(raw_graph)


def test_build_plan_single_goal_chain(plan_service, sample_graph):
    goal = LearningGoal(target_skill_ids=["async_advanced"], mode=LearningMode.SURFACE)
    knowledge = UserKnowledge(user_id="u1")
    plan: LearningPlan = plan_service.build_plan(sample_graph, goal=goal, knowledge=knowledge)

    assert plan.ordered_skill_ids == [
        "python_basics",
        "functions",
        "decorators",
        "async_advanced",
    ]
    assert plan.user_id == "u1"


def test_build_plan_branching_goal(plan_service, sample_graph):
    goal = LearningGoal(target_skill_ids=["algorithms"], mode=LearningMode.SURFACE)
    knowledge = UserKnowledge(user_id="u1")
    plan = plan_service.build_plan(sample_graph, goal=goal, knowledge=knowledge)
    position = {skill_id: idx for idx, skill_id in enumerate(plan.ordered_skill_ids)}

    assert set(plan.ordered_skill_ids) == {"python_basics", "functions", "data_structures", "algorithms"}
    assert position["python_basics"] < position["functions"]
    assert position["python_basics"] < position["data_structures"]
    assert position["functions"] < position["algorithms"]
    assert position["data_structures"] < position["algorithms"]


def test_build_plan_excludes_mastered(plan_service, sample_graph):
    goal = LearningGoal(target_skill_ids=["decorators"], mode=LearningMode.SURFACE)
    knowledge = UserKnowledge(
        user_id="u1",
        statuses={
            "python_basics": KnowledgeStatus.MASTERED,
            "functions": KnowledgeStatus.MASTERED,
        },
    )
    plan = plan_service.build_plan(sample_graph, goal=goal, knowledge=knowledge)

    assert plan.ordered_skill_ids == ["decorators"]


def test_build_plan_unknown_goal(plan_service, sample_graph):
    goal = LearningGoal(target_skill_ids=["nonexistent"], mode=LearningMode.SURFACE)
    knowledge = UserKnowledge(user_id="u1")

    with pytest.raises(ValueError):
        plan_service.build_plan(sample_graph, goal=goal, knowledge=knowledge)


def test_build_plan_prioritizes_difficulty_when_depth_same(plan_service):
    raw_graph = {
        "skills": [
            {
                "id": "root",
                "title": "Root",
                "description": "",
                "difficulty": 1,
                "prerequisites": [],
            },
            {
                "id": "hard_branch",
                "title": "Hard Branch",
                "description": "",
                "difficulty": 5,
                "prerequisites": ["root"],
            },
            {
                "id": "harder_branch",
                "title": "Harder Branch",
                "description": "",
                "difficulty": 3,
                "prerequisites": ["root"],
            },
            {
                "id": "easy_branch",
                "title": "Easy Branch",
                "description": "",
                "difficulty": 2,
                "prerequisites": ["root"],
            },
            {
                "id": "goal",
                "title": "Goal",
                "description": "",
                "difficulty": 6,
                "prerequisites": ["hard_branch", "easy_branch", "harder_branch"],
            },
        ]
    }
    graph = SkillGraph.from_dict(raw_graph)
    goal = LearningGoal(target_skill_ids=["goal"], mode=LearningMode.SURFACE)
    knowledge = UserKnowledge(user_id="u1")

    plan: LearningPlan = plan_service.build_plan(graph, goal=goal, knowledge=knowledge)
    assert plan.ordered_skill_ids == ["root", "easy_branch", "harder_branch", "hard_branch", "goal"]


def test_brancy_graph_goals(plan_service, branchy_graph):
    goal = LearningGoal(target_skill_ids=["F"], mode=LearningMode.SURFACE)
    knowledge = UserKnowledge(user_id="u1")
    plan: LearningPlan = plan_service.build_plan(branchy_graph, goal=goal, knowledge=knowledge)
    assert plan.ordered_skill_ids == ["B1", "B2", "D1", "D2", "E1", "E2", "B", "D", "E", "F"]


def test_build_plan_balanced_adds_neighbour_branch(sample_graph, plan_service):
    goal = LearningGoal(target_skill_ids=["algorithms"], mode=LearningMode.BALANCED)
    knowledge = UserKnowledge(user_id="u1")
    plan = plan_service.build_plan(sample_graph, goal=goal, knowledge=knowledge)

    assert set(plan.ordered_skill_ids) == {
        "python_basics",
        "functions",
        "data_structures",
        "decorators",
        "algorithms",
    }


def test_build_plan_deep_returns_entire_graph(sample_graph, plan_service):
    goal = LearningGoal(target_skill_ids=["algorithms"], mode=LearningMode.DEEP)
    knowledge = UserKnowledge(user_id="u1")
    plan = plan_service.build_plan(sample_graph, goal=goal, knowledge=knowledge)

    assert set(plan.ordered_skill_ids) == set(sample_graph.skills.keys())
