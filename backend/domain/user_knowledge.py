from dataclasses import dataclass, field

from backend.domain.enums import KnowledgeStatus


@dataclass
class UserKnowledge:
    user_id: str
    statuses: dict[str, KnowledgeStatus] = field(default_factory=dict)

    def get_status(self, skill_id: str) -> KnowledgeStatus:
        return self.statuses.get(skill_id, KnowledgeStatus.UNKNOWN)

    def set_status(self, skill_id: str, status: KnowledgeStatus):
        self.statuses[skill_id] = status

    def is_mastered(self, skill_id: str) -> bool:
        return self.get_status(skill_id) == KnowledgeStatus.MASTERED

    def mastered_ids(self) -> set[str]:
        return {
            skill_id
            for skill_id, status in self.statuses.items()
            if status == KnowledgeStatus.MASTERED
        }
