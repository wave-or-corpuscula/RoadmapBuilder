from enum import Enum
from dataclasses import dataclass
from typing import Dict, Set

from app.core.graph_engine import SkillGraph


class SkillStatus(Enum):
    UNKNOWN = "unknown"
    LEARNING = "learning"
    MASTERED = "mastered"


@dataclass
class UserSkillState:
    skill_id: str
    state: SkillStatus


class KnowledgeEngine:

    def __init__(self, graph: SkillGraph) -> None:
        self.graph = graph
        self.user_status: Dict[str, SkillStatus] = {}

    def set_status(self, skill_id: str, status: SkillStatus) -> None:
        if skill_id not in self.graph.skills:
            raise ValueError(f"No such skill: {skill_id}")
        
        self.user_status[skill_id] = status
    
    def get_status(self, skill_id: str) -> SkillStatus:

        if skill_id not in self.graph.skills:
            raise ValueError(f"No such skill: {skill_id}")
        
        return self.user_status.get(skill_id, SkillStatus.UNKNOWN)

    def is_skill_available(self, skill_id: str) -> bool:

        if skill_id not in self.graph.skills:
            raise ValueError(f"No such skill: {skill_id}")
        
        if self.get_status(skill_id) is SkillStatus.MASTERED:
            return False

        return all(self.get_status(prereq) is SkillStatus.MASTERED 
                   for prereq 
                   in self.graph.get_prerequisites(skill_id))

    def get_available_skills(self) -> Set[str]:
        return {
            skill 
            for skill in self.graph.skills
            if self.is_skill_available(skill)
        }

    def gap_analysis(self, target_skill: str) -> Set[str]:
        
        if target_skill not in self.graph.skills:
            raise ValueError(f"No such skill: {target_skill}")

        required_skills = (
            self.graph.get_transitive_prerequisites(target_skill)
            | {target_skill}
        )

        return {
            skill
            for skill in required_skills
            if self.get_status(skill) is not SkillStatus.MASTERED
        }
    
    def get_next_best_skill(self) -> str | None:
        available = self.get_available_skills()

        if not available:
            return None

        def score(skill_id: str) -> int:
            depth = self.graph.calculate_depth(skill_id)
            difficulty = self.graph.skills[skill_id].difficulty
            return depth + difficulty

        return min(available, key=score)
