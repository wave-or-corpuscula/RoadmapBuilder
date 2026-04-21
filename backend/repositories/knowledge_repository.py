from backend.domain.user_knowledge import UserKnowledge
from backend.core.db import SessionLocal
from backend.db_models.models import UserKnowledgeStatusModel
from backend.domain.enums import KnowledgeStatus

class PostgresKnowledgeRepository:
    def get(self, user_id: str) -> UserKnowledge | None:
        with SessionLocal() as session:
            rows = (
                session.query(UserKnowledgeStatusModel)
                .filter(UserKnowledgeStatusModel.user_id == user_id)
                .all()
            )
            if not rows:
                return None
            statuses = {row.skill_id: KnowledgeStatus(row.status) for row in rows}
            return UserKnowledge(user_id=user_id, statuses=statuses)

    def get_or_create(self, user_id: str) -> UserKnowledge:
        existing = self.get(user_id)
        if existing is not None:
            return existing
        return UserKnowledge(user_id=user_id)

    def save(self, knowledge: UserKnowledge) -> UserKnowledge:
        with SessionLocal() as session:
            (
                session.query(UserKnowledgeStatusModel)
                .filter(UserKnowledgeStatusModel.user_id == knowledge.user_id)
                .delete()
            )
            for skill_id, status in knowledge.statuses.items():
                session.add(
                    UserKnowledgeStatusModel(
                        user_id=knowledge.user_id,
                        skill_id=skill_id,
                        status=status.value,
                    )
                )
            session.commit()
        return knowledge
