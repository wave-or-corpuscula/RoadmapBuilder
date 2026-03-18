from backend.domain.user_knowledge import UserKnowledge


class InMemoryKnowledgeRepository:
    def __init__(self):
        self._knowledge_by_user: dict[str, UserKnowledge] = {}

    def get(self, user_id: str) -> UserKnowledge | None:
        return self._knowledge_by_user.get(user_id)

    def get_or_create(self, user_id: str) -> UserKnowledge:
        knowledge = self.get(user_id)
        if knowledge is None:
            knowledge = UserKnowledge(user_id=user_id)
            self._knowledge_by_user[user_id] = knowledge
        return knowledge

    def save(self, knowledge: UserKnowledge) -> UserKnowledge:
        self._knowledge_by_user[knowledge.user_id] = knowledge
        return knowledge
