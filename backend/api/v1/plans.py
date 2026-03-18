from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.api.dependencies import (
    get_graph_repo,
    get_knowledge_repo,
    get_plan_repo,
    get_plan_service,
)
from backend.domain.enums import KnowledgeStatus, LearningMode
from backend.domain.learning_goal import LearningGoal
from backend.domain.learning_plan import LearningPlan
from backend.domain.user_knowledge import UserKnowledge
from backend.repositories.graph_repository import InMemoryGraphRepository
from backend.repositories.knowledge_repository import InMemoryKnowledgeRepository
from backend.repositories.plan_repository import InMemoryPlanRepository
from backend.services.plan_service import PlanService


router = APIRouter(prefix="/plans", tags=["plans"])


class CreatePlanRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    target_skill_ids: list[str] = Field(..., min_length=1)
    mode: LearningMode = LearningMode.BALANCED
    mastered_skill_ids: list[str] | None = None


class GoalResponse(BaseModel):
    target_skill_ids: list[str]
    mode: LearningMode


class PlanResponse(BaseModel):
    id: str
    user_id: str
    goal: GoalResponse
    ordered_skill_ids: list[str]
    skill_statuses: dict[str, KnowledgeStatus]
    created_at: datetime
    is_active: bool


class RebuildPlanRequest(BaseModel):
    target_skill_ids: list[str] | None = None
    mode: LearningMode | None = None
    mastered_skill_ids: list[str] | None = None


class UpdatePlanSkillStatusRequest(BaseModel):
    status: KnowledgeStatus


def _to_response(plan: LearningPlan) -> PlanResponse:
    return PlanResponse(
        id=plan.id or "",
        user_id=plan.user_id,
        goal=GoalResponse(target_skill_ids=plan.goal.target_skill_ids, mode=plan.goal.mode),
        ordered_skill_ids=plan.ordered_skill_ids,
        skill_statuses=plan.skill_statuses,
        created_at=plan.created_at,
        is_active=plan.is_active,
    )


@router.post("", response_model=PlanResponse)
def create_plan(
    payload: CreatePlanRequest,
    plan_service: PlanService = Depends(get_plan_service),
    graph_repo: InMemoryGraphRepository = Depends(get_graph_repo),
    knowledge_repo: InMemoryKnowledgeRepository = Depends(get_knowledge_repo),
    plan_repo: InMemoryPlanRepository = Depends(get_plan_repo),
) -> PlanResponse:
    graph = graph_repo.get()
    goal = LearningGoal(target_skill_ids=payload.target_skill_ids, mode=payload.mode)

    base_knowledge = knowledge_repo.get_or_create(payload.user_id)
    statuses = dict(base_knowledge.statuses)
    if payload.mastered_skill_ids is not None:
        for skill_id in payload.mastered_skill_ids:
            statuses[skill_id] = KnowledgeStatus.MASTERED

    knowledge = UserKnowledge(user_id=payload.user_id, statuses=statuses)

    plan: LearningPlan = plan_service.build_plan(graph=graph, goal=goal, knowledge=knowledge)
    for skill_id in plan.ordered_skill_ids:
        status_value = knowledge.get_status(skill_id)
        if status_value != KnowledgeStatus.UNKNOWN:
            plan = plan.with_skill_status(skill_id, status_value)
    plan = plan_repo.save(plan)
    return _to_response(plan)


@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(
    plan_id: str,
    plan_repo: InMemoryPlanRepository = Depends(get_plan_repo),
) -> PlanResponse:
    plan = plan_repo.get(plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return _to_response(plan)


@router.patch("/{plan_id}/rebuild", response_model=PlanResponse)
def rebuild_plan(
    plan_id: str,
    payload: RebuildPlanRequest,
    plan_service: PlanService = Depends(get_plan_service),
    graph_repo: InMemoryGraphRepository = Depends(get_graph_repo),
    knowledge_repo: InMemoryKnowledgeRepository = Depends(get_knowledge_repo),
    plan_repo: InMemoryPlanRepository = Depends(get_plan_repo),
) -> PlanResponse:
    current = plan_repo.get(plan_id)
    if current is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    target_skill_ids = payload.target_skill_ids or current.goal.target_skill_ids
    mode = payload.mode or current.goal.mode
    goal = LearningGoal(target_skill_ids=target_skill_ids, mode=mode)

    base_knowledge = knowledge_repo.get_or_create(current.user_id)
    statuses = dict(base_knowledge.statuses)
    if payload.mastered_skill_ids is not None:
        for skill_id in payload.mastered_skill_ids:
            statuses[skill_id] = KnowledgeStatus.MASTERED

    knowledge = UserKnowledge(user_id=current.user_id, statuses=statuses)

    rebuilt = plan_service.build_plan(graph=graph_repo.get(), goal=goal, knowledge=knowledge)
    for skill_id in rebuilt.ordered_skill_ids:
        status_value = knowledge.get_status(skill_id)
        if status_value != KnowledgeStatus.UNKNOWN:
            rebuilt = rebuilt.with_skill_status(skill_id, status_value)
    rebuilt = rebuilt.with_id(plan_id)
    rebuilt = plan_repo.save(rebuilt)
    return _to_response(rebuilt)


@router.patch("/{plan_id}/skills/{skill_id}/status", response_model=PlanResponse)
def update_plan_skill_status(
    plan_id: str,
    skill_id: str,
    payload: UpdatePlanSkillStatusRequest,
    knowledge_repo: InMemoryKnowledgeRepository = Depends(get_knowledge_repo),
    plan_repo: InMemoryPlanRepository = Depends(get_plan_repo),
) -> PlanResponse:
    plan = plan_repo.get(plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    try:
        updated = plan.with_skill_status(skill_id=skill_id, status=payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    user_knowledge = knowledge_repo.get_or_create(plan.user_id)
    user_knowledge.set_status(skill_id, payload.status)
    knowledge_repo.save(user_knowledge)

    updated = plan_repo.save(updated)
    return _to_response(updated)
