from dataclasses import dataclass, field
from datetime import datetime, UTC

from backend.domain.learning_goal import LearningGoal
from backend.domain.user_knowledge import UserKnowledge


@dataclass(frozen=True)
class LearningPlan:
    user_id: str
    goal: LearningGoal
    ordered_skill_ids: list[str]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    is_active: bool = True

    def contains(self, skill_id: str) -> bool:
        return skill_id in self.ordered_skill_ids

    def next_unmastered(self, knowledge: UserKnowledge) -> str | None:
        for skill_id in self.ordered_skill_ids:
            if not knowledge.is_mastered(skill_id):
                return skill_id
        return None
