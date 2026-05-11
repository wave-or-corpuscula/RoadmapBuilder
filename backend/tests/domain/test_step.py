import pytest

from backend.domain.learning_step import LearningStep
from backend.domain.enums import KnowledgeStatus


def test_step_creation():
    step = LearningStep(id="s1", skill_id="python", title="Изучить синтаксис")
    assert step.id == "s1"
    assert step.skill_id == "python"
    assert step.title == "Изучить синтаксис"
    assert step.status == KnowledgeStatus.UNKNOWN
    assert step.parent_step_id is None
    assert step.substeps == []
    assert step.is_split is False


def test_step_with_status():
    step = LearningStep(id="s1", skill_id="python", title="Test")
    updated = step.with_status(KnowledgeStatus.LEARNING)
    assert updated.status == KnowledgeStatus.LEARNING
    assert updated.id == "s1"
    assert step.status == KnowledgeStatus.UNKNOWN


def test_step_with_substeps():
    step = LearningStep(id="s1", skill_id="python", title="Test")
    sub1 = LearningStep(id="sub1", skill_id="python", title="Sub 1")
    sub2 = LearningStep(id="sub2", skill_id="python", title="Sub 2")
    updated = step.with_substeps([sub1, sub2])
    assert len(updated.substeps) == 2
    assert updated.is_split is True


def test_step_to_dict():
    step = LearningStep(
        id="s1",
        skill_id="python",
        title="Test",
        status=KnowledgeStatus.MASTERED,
        parent_step_id=None,
        is_split=False,
    )
    d = step.to_dict()
    assert d["id"] == "s1"
    assert d["skill_id"] == "python"
    assert d["status"] == "mastered"
    assert d["is_split"] is False


def test_step_from_dict():
    data = {
        "id": "s1",
        "skill_id": "python",
        "title": "Test",
        "status": "learning",
        "parent_step_id": "parent_1",
        "is_split": True,
        "substeps": [
            {"id": "sub1", "skill_id": "python", "title": "Sub", "status": "unknown"}
        ],
    }
    step = LearningStep.from_dict(data)
    assert step.id == "s1"
    assert step.status == KnowledgeStatus.LEARNING
    assert step.parent_step_id == "parent_1"
    assert step.is_split is True
    assert len(step.substeps) == 1


def test_step_from_dict_defaults():
    data = {"id": "s1", "skill_id": "python", "title": "Test"}
    step = LearningStep.from_dict(data)
    assert step.status == KnowledgeStatus.UNKNOWN
    assert step.parent_step_id is None
    assert step.is_split is False
    assert step.substeps == []