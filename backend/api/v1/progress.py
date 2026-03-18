from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.api.dependencies import (
    get_graph_repo,
    get_knowledge_repo,
    get_progress_service,
)
from backend.domain.enums import KnowledgeStatus
from backend.repositories.graph_repository import InMemoryGraphRepository
from backend.repositories.knowledge_repository import InMemoryKnowledgeRepository
from backend.services.progress_service import ProgressService


router = APIRouter(prefix="/progress", tags=["progress"])


class UpdateSkillStatusRequest(BaseModel):
    status: KnowledgeStatus


class ProgressResponse(BaseModel):
    user_id: str
    statuses: dict[str, KnowledgeStatus]


@router.get("/{user_id}", response_model=ProgressResponse)
def get_progress(
    user_id: str,
    knowledge_repo: InMemoryKnowledgeRepository = Depends(get_knowledge_repo),
    progress_service: ProgressService = Depends(get_progress_service),
) -> ProgressResponse:
    knowledge = progress_service.get_user_knowledge(repo=knowledge_repo, user_id=user_id)
    return ProgressResponse(user_id=knowledge.user_id, statuses=knowledge.statuses)


@router.patch("/{user_id}/skills/{skill_id}/status", response_model=ProgressResponse)
def update_progress_skill_status(
    user_id: str,
    skill_id: str,
    payload: UpdateSkillStatusRequest,
    graph_repo: InMemoryGraphRepository = Depends(get_graph_repo),
    knowledge_repo: InMemoryKnowledgeRepository = Depends(get_knowledge_repo),
    progress_service: ProgressService = Depends(get_progress_service),
) -> ProgressResponse:
    if skill_id not in graph_repo.get().skills:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found in graph")

    knowledge = progress_service.update_skill_status(
        repo=knowledge_repo,
        user_id=user_id,
        skill_id=skill_id,
        status=payload.status,
    )
    return ProgressResponse(user_id=knowledge.user_id, statuses=knowledge.statuses)
