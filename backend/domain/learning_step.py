from dataclasses import dataclass, field

from backend.domain.enums import KnowledgeStatus


@dataclass(frozen=True)
class LearningStep:
    id: str
    skill_id: str
    title: str
    status: KnowledgeStatus = KnowledgeStatus.UNKNOWN
    parent_step_id: str | None = None
    substeps: list["LearningStep"] = field(default_factory=list)
    is_split: bool = False

    def with_status(self, status: KnowledgeStatus) -> "LearningStep":
        return LearningStep(
            id=self.id,
            skill_id=self.skill_id,
            title=self.title,
            status=status,
            parent_step_id=self.parent_step_id,
            substeps=list(self.substeps),
            is_split=self.is_split,
        )

    def with_substeps(self, substeps: list["LearningStep"]) -> "LearningStep":
        return LearningStep(
            id=self.id,
            skill_id=self.skill_id,
            title=self.title,
            status=self.status,
            parent_step_id=self.parent_step_id,
            substeps=substeps,
            is_split=True,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "skill_id": self.skill_id,
            "title": self.title,
            "status": self.status.value,
            "parent_step_id": self.parent_step_id,
            "substeps": [s.to_dict() for s in self.substeps],
            "is_split": self.is_split,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LearningStep":
        substeps = [cls.from_dict(s) for s in data.get("substeps", [])]
        return cls(
            id=data["id"],
            skill_id=data["skill_id"],
            title=data["title"],
            status=KnowledgeStatus(data.get("status", "unknown")),
            parent_step_id=data.get("parent_step_id"),
            substeps=substeps,
            is_split=data.get("is_split", False),
        )