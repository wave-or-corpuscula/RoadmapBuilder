from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Skill:
    id: str
    title: str
    description: str
    difficulty: int
