from backend.domain.enums import KnowledgeStatus
from backend.domain.user_knowledge import UserKnowledge
from backend.repositories.knowledge_repository import InMemoryKnowledgeRepository


class ProgressService:
    def get_user_knowledge(self, repo: InMemoryKnowledgeRepository, user_id: str) -> UserKnowledge:
        return repo.get_or_create(user_id)

    def update_skill_status(
        self,
        repo: InMemoryKnowledgeRepository,
        user_id: str,
        skill_id: str,
        status: KnowledgeStatus,
    ) -> UserKnowledge:
        knowledge = repo.get_or_create(user_id)
        knowledge.set_status(skill_id, status)
        return repo.save(knowledge)
