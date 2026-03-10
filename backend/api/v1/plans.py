from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.domain.enums import KnowledgeStatus, LearningMode
from backend.domain.learning_goal import LearningGoal
from backend.domain.learning_plan import LearningPlan
from backend.domain.user_knowledge import UserKnowledge
from backend.repositories.graph_repository import InMemoryGraphRepository
from backend.repositories.plan_repository import InMemoryPlanRepository
from backend.services.plan_service import PlanService


router = APIRouter(prefix="/plans", tags=["plans"])


class CreatePlanRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    target_skill_ids: list[str] = Field(..., min_length=1)
    mode: LearningMode = LearningMode.BALANCED
    mastered_skill_ids: list[str] = Field(default_factory=list)


class GoalResponse(BaseModel):
    target_skill_ids: list[str]
    mode: LearningMode


class PlanResponse(BaseModel):
    id: str
    user_id: str
    goal: GoalResponse
    ordered_skill_ids: list[str]
    created_at: datetime
    is_active: bool


def get_plan_service() -> PlanService:
    return PlanService()


def get_graph_repo() -> InMemoryGraphRepository:
    # Overridden in app factory; fallback for import-time safety.
    raise RuntimeError("Graph repository dependency not configured")


def get_plan_repo() -> InMemoryPlanRepository:
    # Overridden in app factory; fallback for import-time safety.
    raise RuntimeError("Plan repository dependency not configured")


@router.post("", response_model=PlanResponse)
def create_plan(
    payload: CreatePlanRequest,
    plan_service: PlanService = Depends(get_plan_service),
    graph_repo: InMemoryGraphRepository = Depends(get_graph_repo),
    plan_repo: InMemoryPlanRepository = Depends(get_plan_repo),
) -> PlanResponse:
    graph = graph_repo.get()
    goal = LearningGoal(target_skill_ids=payload.target_skill_ids, mode=payload.mode)

    statuses = {skill_id: KnowledgeStatus.MASTERED for skill_id in payload.mastered_skill_ids}
    knowledge = UserKnowledge(user_id=payload.user_id, statuses=statuses)

    plan: LearningPlan = plan_service.build_plan(graph=graph, goal=goal, knowledge=knowledge)
    plan = plan_repo.save(plan)

    return PlanResponse(
        id=plan.id or "",
        user_id=plan.user_id,
        goal=GoalResponse(target_skill_ids=plan.goal.target_skill_ids, mode=plan.goal.mode),
        ordered_skill_ids=plan.ordered_skill_ids,
        created_at=plan.created_at,
        is_active=plan.is_active,
    )
