from uuid import uuid4

from backend.domain.learning_plan import LearningPlan
from backend.domain.learning_goal import LearningGoal
from backend.domain.enums import KnowledgeStatus, LearningMode
from backend.core.db import SessionLocal
from backend.db_models.models import LearningPlanModel

class PostgresPlanRepository:
    def _to_domain(self, row: LearningPlanModel) -> LearningPlan:
        statuses_raw = row.skill_statuses or {}
        statuses = {skill_id: KnowledgeStatus(value) for skill_id, value in statuses_raw.items()}
        return LearningPlan(
            id=row.id,
            user_id=row.user_id,
            goal=LearningGoal(
                target_skill_ids=list(row.goal_target_skill_ids or []),
                mode=LearningMode(row.goal_mode),
            ),
            ordered_skill_ids=list(row.ordered_skill_ids or []),
            title=row.title,
            parent_plan_id=row.parent_plan_id,
            root_plan_id=row.root_plan_id,
            source_skill_id=row.source_skill_id,
            fingerprint=row.fingerprint,
            skill_statuses=statuses,
            skill_notes=dict(row.skill_notes or {}),
            graph_payload=row.graph_payload,
            created_at=row.created_at,
            is_active=row.is_active,
        )

    def save(self, plan: LearningPlan) -> LearningPlan:
        if plan.id is None:
            plan = plan.with_id(str(uuid4()))

        with SessionLocal() as session:
            row = session.get(LearningPlanModel, plan.id)
            serialized_statuses = {skill_id: status.value for skill_id, status in plan.skill_statuses.items()}
            if row is None:
                row = LearningPlanModel(
                    id=plan.id,
                    user_id=plan.user_id,
                    title=plan.title,
                    parent_plan_id=plan.parent_plan_id,
                    root_plan_id=plan.root_plan_id,
                    source_skill_id=plan.source_skill_id,
                    fingerprint=plan.fingerprint,
                    goal_target_skill_ids=list(plan.goal.target_skill_ids),
                    goal_mode=plan.goal.mode.value,
                    ordered_skill_ids=list(plan.ordered_skill_ids),
                    skill_statuses=serialized_statuses,
                    skill_notes=dict(plan.skill_notes),
                    graph_payload=plan.graph_payload,
                    created_at=plan.created_at,
                    is_active=plan.is_active,
                )
                session.add(row)
            else:
                row.user_id = plan.user_id
                row.title = plan.title
                row.parent_plan_id = plan.parent_plan_id
                row.root_plan_id = plan.root_plan_id
                row.source_skill_id = plan.source_skill_id
                row.fingerprint = plan.fingerprint
                row.goal_target_skill_ids = list(plan.goal.target_skill_ids)
                row.goal_mode = plan.goal.mode.value
                row.ordered_skill_ids = list(plan.ordered_skill_ids)
                row.skill_statuses = serialized_statuses
                row.skill_notes = dict(plan.skill_notes)
                row.graph_payload = plan.graph_payload
                row.created_at = plan.created_at
                row.is_active = plan.is_active
            session.commit()
        return plan

    def get(self, plan_id: str) -> LearningPlan | None:
        with SessionLocal() as session:
            row = session.get(LearningPlanModel, plan_id)
            if row is None:
                return None
            return self._to_domain(row)

    def list_by_user(self, user_id: str) -> list[LearningPlan]:
        with SessionLocal() as session:
            rows = (
                session.query(LearningPlanModel)
                .filter(LearningPlanModel.user_id == user_id)
                .all()
            )
            return [self._to_domain(row) for row in rows]

    def find_by_user_and_fingerprint(self, user_id: str, fingerprint: str) -> LearningPlan | None:
        with SessionLocal() as session:
            row = (
                session.query(LearningPlanModel)
                .filter(
                    LearningPlanModel.user_id == user_id,
                    LearningPlanModel.fingerprint == fingerprint,
                )
                .one_or_none()
            )
            if row is None:
                return None
            return self._to_domain(row)

    def delete(self, plan_id: str) -> None:
        with SessionLocal() as session:
            (
                session.query(LearningPlanModel)
                .filter(LearningPlanModel.id == plan_id)
                .delete()
            )
            session.commit()
