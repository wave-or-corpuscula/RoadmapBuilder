import hashlib
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.api.security import get_current_user_id
from backend.api.dependencies import (
    get_graph_repo,
    get_knowledge_repo,
    get_plan_repo,
    get_plan_service,
)
from backend.domain.enums import KnowledgeStatus, LearningMode
from backend.domain.learning_goal import LearningGoal
from backend.domain.learning_plan import LearningPlan
from backend.domain.skill_graph import SkillGraph
from backend.domain.user_knowledge import UserKnowledge
from backend.repositories.graph_repository import InMemoryGraphRepository
from backend.repositories.knowledge_repository import InMemoryKnowledgeRepository
from backend.repositories.plan_repository import InMemoryPlanRepository
from backend.services.plan_service import PlanService


router = APIRouter(prefix="/plans", tags=["plans"])
IMPORT_SCHEMA_VERSION = "1.0"


class CreatePlanRequest(BaseModel):
    target_skill_ids: list[str] = Field(..., min_length=1)
    mode: LearningMode = LearningMode.BALANCED
    mastered_skill_ids: list[str] | None = None


class GoalResponse(BaseModel):
    target_skill_ids: list[str]
    mode: LearningMode


class PlanResponse(BaseModel):
    id: str
    user_id: str
    title: str
    fingerprint: str | None = None
    goal: GoalResponse
    ordered_skill_ids: list[str]
    skill_statuses: dict[str, KnowledgeStatus]
    skill_notes: dict[str, str]
    created_at: datetime
    is_active: bool


class RebuildPlanRequest(BaseModel):
    target_skill_ids: list[str] | None = None
    mode: LearningMode | None = None
    mastered_skill_ids: list[str] | None = None


class UpdatePlanSkillStatusRequest(BaseModel):
    status: KnowledgeStatus


class UpdatePlanSkillNoteRequest(BaseModel):
    note: str


class UpdatePlanTitleRequest(BaseModel):
    title: str = Field(..., min_length=1)


class ImportSkillItem(BaseModel):
    id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    description: str = ""
    difficulty: int = Field(..., ge=1, le=10)
    prerequisites: list[str] = Field(default_factory=list)


class ImportPlanRequest(BaseModel):
    schema_version: str | None = None
    title: str | None = None
    skills: list[ImportSkillItem] = Field(..., min_length=1)
    target_skill_ids: list[str] = Field(..., min_length=1)
    mode: LearningMode = LearningMode.BALANCED
    mastered_skill_ids: list[str] | None = None


class ImportTemplateResponse(BaseModel):
    schema_version: str
    title: str
    skills: list[ImportSkillItem]
    target_skill_ids: list[str]
    mode: LearningMode
    mastered_skill_ids: list[str]


class ImportPromptRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=200)


class ImportPromptResponse(BaseModel):
    schema_version: str
    topic: str
    prompt: str


def _to_response(plan: LearningPlan) -> PlanResponse:
    return PlanResponse(
        id=plan.id or "",
        user_id=plan.user_id,
        title=plan.title,
        fingerprint=plan.fingerprint,
        goal=GoalResponse(target_skill_ids=plan.goal.target_skill_ids, mode=plan.goal.mode),
        ordered_skill_ids=plan.ordered_skill_ids,
        skill_statuses=plan.skill_statuses,
        skill_notes=plan.skill_notes,
        created_at=plan.created_at,
        is_active=plan.is_active,
    )


def _graph_to_payload(graph: SkillGraph) -> dict:
    skills = []
    for skill_id in sorted(graph.skills.keys()):
        skill = graph.skills[skill_id]
        skills.append(
            {
                "id": skill.id,
                "title": skill.title,
                "description": skill.description,
                "difficulty": skill.difficulty,
                "prerequisites": sorted(graph.prerequisites_map[skill_id]),
            }
        )
    return {"skills": skills}


def _enrich_plan_statuses(
    plan: LearningPlan,
    knowledge: UserKnowledge,
    skill_ids: list[str] | None = None,
) -> LearningPlan:
    enriched = plan
    status_scope = skill_ids if skill_ids is not None else enriched.ordered_skill_ids
    for skill_id in status_scope:
        status_value = knowledge.get_status(skill_id)
        if status_value != KnowledgeStatus.UNKNOWN:
            enriched = enriched.with_skill_status(skill_id, status_value)
    return enriched


def _build_import_prompt(topic: str) -> str:
    return (
        "Ты эксперт по обучающим дорожным картам. "
        "Сгенерируй строго валидный JSON (без markdown, без комментариев, без лишнего текста) "
        "для темы: "
        f'"{topic}".\n\n'
        "Требования к формату JSON:\n"
        f'1) schema_version должен быть "{IMPORT_SCHEMA_VERSION}".\n'
        "2) Корневой объект должен содержать ключи:\n"
        '   - "schema_version": string\n'
        f'   - "title": string (название плана, строго: "{topic}")\n'
        '   - "skills": array of skill objects\n'
        '   - "target_skill_ids": array[string]\n'
        '   - "mode": one of "surface" | "balanced" | "deep"\n'
        '   - "mastered_skill_ids": array[string]\n'
        "3) Skill object:\n"
        '   - "id": string (snake_case, уникальный)\n'
        '   - "title": string\n'
        '   - "description": string\n'
        '   - "difficulty": integer от 1 до 10\n'
        '   - "prerequisites": array[string] (id навыков-предпосылок)\n'
        "4) Граф должен быть ацикличным.\n"
        "5) Все id из prerequisites должны существовать в skills.\n"
        "6) target_skill_ids должны существовать в skills и соответствовать конечной цели обучения.\n"
        "7) Сформируй 15-35 навыков, от базовых к продвинутым.\n"
        "8) Учитывай практическую последовательность изучения.\n"
        "9) mastered_skill_ids оставь пустым массивом.\n\n"
        "Проверь JSON перед ответом:\n"
        "- синтаксис валиден;\n"
        "- нет дубликатов id;\n"
        "- нет циклов;\n"
        "- target_skill_ids не пустой.\n\n"
        "Ответ: только JSON объект."
    )


def _build_plan_fingerprint(payload: ImportPlanRequest) -> str:
    schema_version = payload.schema_version or IMPORT_SCHEMA_VERSION

    normalized_skills = []
    for item in sorted(payload.skills, key=lambda skill: skill.id):
        normalized_skills.append(
            {
                "id": item.id,
                "title": item.title,
                "description": item.description,
                "difficulty": item.difficulty,
                "prerequisites": sorted(item.prerequisites),
            }
        )

    canonical_payload = {
        "schema_version": schema_version,
        "skills": normalized_skills,
        "target_skill_ids": sorted(payload.target_skill_ids),
        "mode": payload.mode.value,
    }
    canonical_json = json.dumps(
        canonical_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


@router.post("", response_model=PlanResponse)
def create_plan(
    payload: CreatePlanRequest,
    current_user_id: str = Depends(get_current_user_id),
    plan_service: PlanService = Depends(get_plan_service),
    graph_repo: InMemoryGraphRepository = Depends(get_graph_repo),
    knowledge_repo: InMemoryKnowledgeRepository = Depends(get_knowledge_repo),
    plan_repo: InMemoryPlanRepository = Depends(get_plan_repo),
) -> PlanResponse:
    graph = graph_repo.get()
    goal = LearningGoal(target_skill_ids=payload.target_skill_ids, mode=payload.mode)

    base_knowledge = knowledge_repo.get_or_create(current_user_id)
    statuses = dict(base_knowledge.statuses)
    if payload.mastered_skill_ids is not None:
        for skill_id in payload.mastered_skill_ids:
            statuses[skill_id] = KnowledgeStatus.MASTERED

    knowledge = UserKnowledge(user_id=current_user_id, statuses=statuses)

    plan: LearningPlan = plan_service.build_plan(graph=graph, goal=goal, knowledge=knowledge)
    generated_title = ", ".join(payload.target_skill_ids[:2]) or "Learning Plan"
    plan = plan.with_title(f"Plan: {generated_title}")
    plan = _enrich_plan_statuses(plan, knowledge)
    plan = plan_repo.save(plan)
    return _to_response(plan)


@router.get("", response_model=list[PlanResponse])
def list_plans(
    current_user_id: str = Depends(get_current_user_id),
    plan_repo: InMemoryPlanRepository = Depends(get_plan_repo),
) -> list[PlanResponse]:
    plans = plan_repo.list_by_user(current_user_id)
    plans.sort(key=lambda item: item.created_at, reverse=True)
    return [_to_response(plan) for plan in plans]


@router.get("/import-template", response_model=ImportTemplateResponse)
def get_import_template() -> ImportTemplateResponse:
    return ImportTemplateResponse(
        schema_version=IMPORT_SCHEMA_VERSION,
        title="Python API Roadmap",
        skills=[
            ImportSkillItem(
                id="python_basics",
                title="Python Basics",
                description="Syntax and control flow",
                difficulty=1,
                prerequisites=[],
            ),
            ImportSkillItem(
                id="functions",
                title="Functions",
                description="Function definitions and scope",
                difficulty=2,
                prerequisites=["python_basics"],
            ),
            ImportSkillItem(
                id="api_design",
                title="API Design",
                description="REST basics and resource modeling",
                difficulty=3,
                prerequisites=["functions"],
            ),
        ],
        target_skill_ids=["api_design"],
        mode=LearningMode.BALANCED,
        mastered_skill_ids=[],
    )


@router.post("/import-prompt", response_model=ImportPromptResponse)
def build_import_prompt(payload: ImportPromptRequest) -> ImportPromptResponse:
    topic = payload.topic.strip()
    if not topic:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="topic must not be empty")
    return ImportPromptResponse(
        schema_version=IMPORT_SCHEMA_VERSION,
        topic=topic,
        prompt=_build_import_prompt(topic),
    )


@router.post("/import", response_model=PlanResponse)
def import_plan(
    payload: ImportPlanRequest,
    current_user_id: str = Depends(get_current_user_id),
    plan_service: PlanService = Depends(get_plan_service),
    knowledge_repo: InMemoryKnowledgeRepository = Depends(get_knowledge_repo),
    plan_repo: InMemoryPlanRepository = Depends(get_plan_repo),
) -> PlanResponse:
    if payload.schema_version is not None and payload.schema_version != IMPORT_SCHEMA_VERSION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported schema_version '{payload.schema_version}'. "
                f"Expected '{IMPORT_SCHEMA_VERSION}'."
            ),
        )

    fingerprint = _build_plan_fingerprint(payload)
    existing = plan_repo.find_by_user_and_fingerprint(current_user_id, fingerprint)

    graph_payload = {"skills": [item.model_dump() for item in payload.skills]}

    try:
        imported_graph = SkillGraph.from_dict(graph_payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    goal = LearningGoal(target_skill_ids=payload.target_skill_ids, mode=payload.mode)

    base_knowledge = knowledge_repo.get_or_create(current_user_id)
    statuses = dict(base_knowledge.statuses)
    if payload.mastered_skill_ids is not None:
        for skill_id in payload.mastered_skill_ids:
            statuses[skill_id] = KnowledgeStatus.MASTERED
    knowledge = UserKnowledge(user_id=current_user_id, statuses=statuses)

    plan = plan_service.build_plan(graph=imported_graph, goal=goal, knowledge=knowledge)
    if payload.title is not None:
        plan = plan.with_title(payload.title)
    elif existing is not None:
        plan = plan.with_title(existing.title)
    else:
        generated_title = ", ".join(payload.target_skill_ids[:2]) or "Learning Plan"
        plan = plan.with_title(f"Plan: {generated_title}")
    plan = plan.with_fingerprint(fingerprint)
    plan = plan.with_graph_payload(graph_payload)
    if existing is not None and existing.skill_notes:
        plan = plan.with_skill_notes(existing.skill_notes)
    imported_skill_ids = [skill.id for skill in payload.skills]
    plan = _enrich_plan_statuses(plan, knowledge, imported_skill_ids)
    if existing is not None and existing.id is not None:
        plan = plan.with_id(existing.id)
    plan = plan_repo.save(plan)
    return _to_response(plan)


@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(
    plan_id: str,
    current_user_id: str = Depends(get_current_user_id),
    plan_repo: InMemoryPlanRepository = Depends(get_plan_repo),
) -> PlanResponse:
    plan = plan_repo.get(plan_id)
    if plan is None or plan.user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return _to_response(plan)


@router.get("/{plan_id}/graph")
def get_plan_graph(
    plan_id: str,
    current_user_id: str = Depends(get_current_user_id),
    graph_repo: InMemoryGraphRepository = Depends(get_graph_repo),
    plan_repo: InMemoryPlanRepository = Depends(get_plan_repo),
) -> dict:
    plan = plan_repo.get(plan_id)
    if plan is None or plan.user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    if plan.graph_payload is not None:
        return plan.graph_payload

    subgraph = graph_repo.get().get_subgraph(plan.goal.target_skill_ids, plan.goal.mode)
    return _graph_to_payload(subgraph)


@router.patch("/{plan_id}/rebuild", response_model=PlanResponse)
def rebuild_plan(
    plan_id: str,
    payload: RebuildPlanRequest,
    current_user_id: str = Depends(get_current_user_id),
    plan_service: PlanService = Depends(get_plan_service),
    graph_repo: InMemoryGraphRepository = Depends(get_graph_repo),
    knowledge_repo: InMemoryKnowledgeRepository = Depends(get_knowledge_repo),
    plan_repo: InMemoryPlanRepository = Depends(get_plan_repo),
) -> PlanResponse:
    current = plan_repo.get(plan_id)
    if current is None or current.user_id != current_user_id:
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

    source_graph = graph_repo.get()
    if current.graph_payload is not None:
        source_graph = SkillGraph.from_dict(current.graph_payload)

    rebuilt = plan_service.build_plan(graph=source_graph, goal=goal, knowledge=knowledge)
    rebuilt = rebuilt.with_title(current.title)
    status_scope: list[str] | None = None
    if current.graph_payload is not None:
        status_scope = list(source_graph.skills.keys())
    rebuilt = _enrich_plan_statuses(rebuilt, knowledge, status_scope)
    if current.graph_payload is not None:
        rebuilt = rebuilt.with_graph_payload(current.graph_payload)
    rebuilt = rebuilt.with_id(plan_id)
    rebuilt = plan_repo.save(rebuilt)
    return _to_response(rebuilt)


@router.patch("/{plan_id}/skills/{skill_id}/status", response_model=PlanResponse)
def update_plan_skill_status(
    plan_id: str,
    skill_id: str,
    payload: UpdatePlanSkillStatusRequest,
    current_user_id: str = Depends(get_current_user_id),
    knowledge_repo: InMemoryKnowledgeRepository = Depends(get_knowledge_repo),
    plan_repo: InMemoryPlanRepository = Depends(get_plan_repo),
) -> PlanResponse:
    plan = plan_repo.get(plan_id)
    if plan is None or plan.user_id != current_user_id:
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


@router.patch("/{plan_id}/title", response_model=PlanResponse)
def update_plan_title(
    plan_id: str,
    payload: UpdatePlanTitleRequest,
    current_user_id: str = Depends(get_current_user_id),
    plan_repo: InMemoryPlanRepository = Depends(get_plan_repo),
) -> PlanResponse:
    plan = plan_repo.get(plan_id)
    if plan is None or plan.user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    updated = plan.with_title(payload.title)
    updated = plan_repo.save(updated)
    return _to_response(updated)


@router.patch("/{plan_id}/skills/{skill_id}/note", response_model=PlanResponse)
def update_plan_skill_note(
    plan_id: str,
    skill_id: str,
    payload: UpdatePlanSkillNoteRequest,
    current_user_id: str = Depends(get_current_user_id),
    plan_repo: InMemoryPlanRepository = Depends(get_plan_repo),
) -> PlanResponse:
    plan = plan_repo.get(plan_id)
    if plan is None or plan.user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    try:
        updated = plan.with_skill_note(skill_id=skill_id, note=payload.note)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    updated = plan_repo.save(updated)
    return _to_response(updated)
