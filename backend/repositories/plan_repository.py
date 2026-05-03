from uuid import uuid4

from backend.domain.learning_plan import LearningPlan
from backend.domain.learning_goal import LearningGoal
from backend.domain.learning_step import LearningStep
from backend.domain.enums import KnowledgeStatus, LearningMode, StepStatus
from backend.core.db import SessionLocal
from backend.db_models.models import LearningPlanModel

class PostgresPlanRepository:
    def _to_domain(self, row: LearningPlanModel) -> LearningPlan:
        statuses_raw = row.skill_statuses or {}
        statuses = {skill_id: KnowledgeStatus(value) for skill_id, value in statuses_raw.items()}
        steps_raw = row.plan_steps or []
        steps = [
            LearningStep(
                id=item["id"],
                skill_id=item["skill_id"],
                title=item["title"],
                type=item["type"],
                estimate_min=int(item["estimate_min"]),
                acceptance_criteria=item["acceptance_criteria"],
            )
            for item in steps_raw
        ]
        step_statuses_raw = row.step_statuses or {}
        step_statuses = {step_id: StepStatus(value) for step_id, value in step_statuses_raw.items()}
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
            steps=steps,
            skill_statuses=statuses,
            step_statuses=step_statuses,
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
            serialized_steps = [
                {
                    "id": step.id,
                    "skill_id": step.skill_id,
                    "title": step.title,
                    "type": step.type,
                    "estimate_min": step.estimate_min,
                    "acceptance_criteria": step.acceptance_criteria,
                }
                for step in plan.steps
            ]
            serialized_step_statuses = {step_id: status.value for step_id, status in plan.step_statuses.items()}
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
                    plan_steps=serialized_steps,
                    skill_statuses=serialized_statuses,
                    step_statuses=serialized_step_statuses,
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
                row.plan_steps = serialized_steps
                row.skill_statuses = serialized_statuses
                row.step_statuses = serialized_step_statuses
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
