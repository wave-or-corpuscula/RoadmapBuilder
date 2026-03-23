from dataclasses import dataclass, field
from datetime import datetime, UTC

from backend.domain.enums import KnowledgeStatus
from backend.domain.learning_goal import LearningGoal
from backend.domain.user_knowledge import UserKnowledge


@dataclass(frozen=True)
class LearningPlan:
    id: str | None
    user_id: str
    goal: LearningGoal
    ordered_skill_ids: list[str]
    skill_statuses: dict[str, KnowledgeStatus] = field(default_factory=dict)
    graph_payload: dict | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    is_active: bool = True

    def __post_init__(self):
        statuses = {}
        for skill_id in self.ordered_skill_ids:
            statuses[skill_id] = self.skill_statuses.get(skill_id, KnowledgeStatus.UNKNOWN)
        object.__setattr__(self, "skill_statuses", statuses)

    def contains(self, skill_id: str) -> bool:
        return skill_id in self.ordered_skill_ids

    def get_status(self, skill_id: str) -> KnowledgeStatus:
        if skill_id not in self.skill_statuses:
            raise ValueError(f"Skill is not in plan: {skill_id}")
        return self.skill_statuses[skill_id]

    def with_skill_status(self, skill_id: str, status: KnowledgeStatus) -> "LearningPlan":
        if skill_id not in self.skill_statuses:
            raise ValueError(f"Skill is not in plan: {skill_id}")

        updated = dict(self.skill_statuses)
        updated[skill_id] = status
        return LearningPlan(
            id=self.id,
            user_id=self.user_id,
            goal=self.goal,
            ordered_skill_ids=self.ordered_skill_ids,
            skill_statuses=updated,
            graph_payload=self.graph_payload,
            created_at=self.created_at,
            is_active=self.is_active,
        )

    def next_unmastered(self, knowledge: UserKnowledge) -> str | None:
        for skill_id in self.ordered_skill_ids:
            if not knowledge.is_mastered(skill_id):
                return skill_id
        return None

    def with_id(self, plan_id: str) -> "LearningPlan":
        return LearningPlan(
            id=plan_id,
            user_id=self.user_id,
            goal=self.goal,
            ordered_skill_ids=self.ordered_skill_ids,
            skill_statuses=dict(self.skill_statuses),
            graph_payload=self.graph_payload,
            created_at=self.created_at,
            is_active=self.is_active,
        )

    def with_graph_payload(self, graph_payload: dict) -> "LearningPlan":
        return LearningPlan(
            id=self.id,
            user_id=self.user_id,
            goal=self.goal,
            ordered_skill_ids=self.ordered_skill_ids,
            skill_statuses=dict(self.skill_statuses),
            graph_payload=graph_payload,
            created_at=self.created_at,
            is_active=self.is_active,
        )
