import pytest

from backend.domain.enums import KnowledgeStatus, LearningMode
from backend.domain.learning_goal import LearningGoal
from backend.domain.learning_plan import LearningPlan
from backend.domain.user_knowledge import UserKnowledge


def test_learning_goal_requires_non_empty_targets():
    with pytest.raises(ValueError):
        LearningGoal(target_skill_ids=[])


def test_learning_goal_deduplicates_targets():
    goal = LearningGoal(target_skill_ids=["a", "b", "a"], mode=LearningMode.BALANCED)
    assert goal.target_skill_ids == ["a", "b"]


def test_user_knowledge_mastered_helpers():
    knowledge = UserKnowledge(user_id="u1")
    knowledge.set_status("python", KnowledgeStatus.MASTERED)
    knowledge.set_status("sql", KnowledgeStatus.LEARNING)

    assert knowledge.is_mastered("python") is True
    assert knowledge.is_mastered("sql") is False
    assert knowledge.mastered_ids() == {"python"}


def test_learning_plan_next_unmastered():
    goal = LearningGoal(target_skill_ids=["async"])
    plan = LearningPlan(
        id=None,
        user_id="u1",
        goal=goal,
        ordered_skill_ids=["python", "functions", "async"],
    )
    knowledge = UserKnowledge(
        user_id="u1",
        statuses={
            "python": KnowledgeStatus.MASTERED,
            "functions": KnowledgeStatus.MASTERED,
        },
    )

    assert plan.next_unmastered(knowledge) == "async"
