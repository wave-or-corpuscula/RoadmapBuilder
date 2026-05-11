import pytest

from backend.domain.learning_goal import LearningGoal
from backend.domain.learning_plan import LearningPlan
from backend.domain.enums import KnowledgeStatus, LearningMode
from backend.domain.learning_step import LearningStep


@pytest.fixture
def plan_with_steps():
    goal = LearningGoal(target_skill_ids=["python"], mode=LearningMode.SURFACE)
    steps = [
        LearningStep(id="s1", skill_id="python", title="Изучить синтаксис"),
        LearningStep(id="s2", skill_id="python", title="Функции"),
    ]
    return LearningPlan(
        id="plan1",
        user_id="u1",
        goal=goal,
        ordered_skill_ids=["python"],
        steps=steps,
    )


def test_get_skill_steps(plan_with_steps):
    steps = plan_with_steps.get_skill_steps("python")
    assert len(steps) == 2
    assert steps[0].id == "s1"


def test_get_skill_steps_not_found(plan_with_steps):
    steps = plan_with_steps.get_skill_steps("js")
    assert steps == []


def test_get_step_by_id_found(plan_with_steps):
    step = plan_with_steps.get_step_by_id("s2")
    assert step is not None
    assert step.title == "Функции"


def test_get_step_by_id_not_found(plan_with_steps):
    step = plan_with_steps.get_step_by_id("nonexistent")
    assert step is None


def test_get_step_by_id_in_substeps():
    goal = LearningGoal(target_skill_ids=["python"], mode=LearningMode.SURFACE)
    sub = LearningStep(id="sub1", skill_id="python", title="Sub step")
    main = LearningStep(id="s1", skill_id="python", title="Main", substeps=[sub])
    plan = LearningPlan(
        id="plan1",
        user_id="u1",
        goal=goal,
        ordered_skill_ids=["python"],
        steps=[main],
    )
    found = plan.get_step_by_id("sub1")
    assert found is not None
    assert found.title == "Sub step"


def test_with_step_status(plan_with_steps):
    updated = plan_with_steps.with_step_status("s1", KnowledgeStatus.LEARNING)
    step = updated.get_step_by_id("s1")
    assert step.status == KnowledgeStatus.LEARNING
    assert plan_with_steps.get_step_by_id("s1").status == KnowledgeStatus.UNKNOWN


def test_with_step_status_updates_substep():
    goal = LearningGoal(target_skill_ids=["python"], mode=LearningMode.SURFACE)
    sub = LearningStep(id="sub1", skill_id="python", title="Sub", status=KnowledgeStatus.UNKNOWN)
    main = LearningStep(id="s1", skill_id="python", title="Main", substeps=[sub])
    plan = LearningPlan(
        id="plan1",
        user_id="u1",
        goal=goal,
        ordered_skill_ids=["python"],
        steps=[main],
    )
    updated = plan.with_step_status("sub1", KnowledgeStatus.MASTERED)
    sub_updated = updated.get_step_by_id("sub1")
    assert sub_updated.status == KnowledgeStatus.MASTERED


def test_add_skill_steps(plan_with_steps):
    new_steps = [LearningStep(id="s3", skill_id="python", title="Classes")]
    updated = plan_with_steps.add_skill_steps("python", new_steps)
    ids = [s.id for s in updated.steps]
    assert "s3" in ids
    assert "s1" not in ids
    assert "s2" not in ids


def test_split_step_success(plan_with_steps):
    substeps = [
        LearningStep(id="s1_sub1", skill_id="python", title="Переменные"),
        LearningStep(id="s1_sub2", skill_id="python", title="Типы данных"),
    ]
    updated = plan_with_steps.split_step("s1", substeps)
    main_step = updated.get_step_by_id("s1")
    assert main_step.is_split is True
    assert len(main_step.substeps) == 2


def test_split_step_already_split_raises(plan_with_steps):
    substeps = [LearningStep(id="s1_sub1", skill_id="python", title="Sub")]
    updated = plan_with_steps.split_step("s1", substeps)
    with pytest.raises(ValueError, match="already split"):
        updated.split_step("s1", substeps)


def test_next_unstarted_step(plan_with_steps):
    step = plan_with_steps.next_unstarted_step()
    assert step is not None
    assert step.id == "s1"


def test_next_unstarted_step_all_completed():
    goal = LearningGoal(target_skill_ids=["python"], mode=LearningMode.SURFACE)
    steps = [LearningStep(id="s1", skill_id="python", title="Test", status=KnowledgeStatus.MASTERED)]
    plan = LearningPlan(
        id="plan1",
        user_id="u1",
        goal=goal,
        ordered_skill_ids=["python"],
        steps=steps,
    )
    step = plan.next_unstarted_step()
    assert step is None