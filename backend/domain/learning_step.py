from dataclasses import dataclass


@dataclass(frozen=True)
class LearningStep:
    id: str
    skill_id: str
    title: str
    type: str
    estimate_min: int
    acceptance_criteria: str
