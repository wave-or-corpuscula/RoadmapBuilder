from enum import Enum


class KnowledgeStatus(Enum):
    UNKNOWN = "unknown"
    LEARNING = "learning"
    MASTERED = "mastered"


class LearningMode(Enum):
    SURFACE = "surface"
    BALANCED = "balanced"
    DEEP = "deep"


class StepStatus(Enum):
    NOT_STARTED = "not_started"
    LEARNING = "learning"
    COMPLETED = "completed"
