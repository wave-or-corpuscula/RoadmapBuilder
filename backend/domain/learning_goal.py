from dataclasses import dataclass

from backend.domain.enums import LearningMode


@dataclass(frozen=True)
class LearningGoal:
    target_skill_ids: list[str]
    mode: LearningMode = LearningMode.BALANCED

    def __post_init__(self):
        if not self.target_skill_ids:
            raise ValueError("Learning goal cannot be empty")

        unique_ids = list(dict.fromkeys(self.target_skill_ids)) # Keeps goals order
        if len(unique_ids) != len(self.target_skill_ids):
            object.__setattr__(self, "target_skill_ids", unique_ids)
