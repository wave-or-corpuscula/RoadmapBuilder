from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from backend.api.dependencies import get_graph_repo, get_graph_service
from backend.repositories.graph_repository import InMemoryGraphRepository
from backend.services.graph_service import (
    GraphConflictError,
    GraphNotFoundError,
    GraphService,
    GraphValidationError,
    SkillDTO,
)


router = APIRouter(prefix="/skills", tags=["skills"])


class SkillResponse(BaseModel):
    id: str
    title: str
    description: str
    difficulty: int
    prerequisites: list[str]


class CreateSkillRequest(BaseModel):
    id: str = Field(..., min_length=1)
    title: str
    description: str = ""
    difficulty: int = Field(..., ge=1, le=10)
    prerequisites: list[str] = Field(default_factory=list)


class UpdateSkillRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    difficulty: int | None = Field(default=None, ge=1, le=10)
    prerequisites: list[str] | None = None


def _to_response(dto: SkillDTO) -> SkillResponse:
    return SkillResponse(
        id=dto.id,
        title=dto.title,
        description=dto.description,
        difficulty=dto.difficulty,
        prerequisites=dto.prerequisites,
    )


@router.get("", response_model=list[SkillResponse])
def list_skills(
    graph_repo: InMemoryGraphRepository = Depends(get_graph_repo),
    graph_service: GraphService = Depends(get_graph_service),
) -> list[SkillResponse]:
    graph = graph_repo.get()
    return [_to_response(dto) for dto in graph_service.list_skills(graph)]


@router.get("/{skill_id}", response_model=SkillResponse)
def get_skill(
    skill_id: str,
    graph_repo: InMemoryGraphRepository = Depends(get_graph_repo),
    graph_service: GraphService = Depends(get_graph_service),
) -> SkillResponse:
    try:
        dto = graph_service.get_skill(graph_repo.get(), skill_id)
    except GraphNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_response(dto)


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
def create_skill(
    payload: CreateSkillRequest,
    graph_repo: InMemoryGraphRepository = Depends(get_graph_repo),
    graph_service: GraphService = Depends(get_graph_service),
) -> SkillResponse:
    try:
        dto = graph_service.create_skill(
            repo=graph_repo,
            skill_id=payload.id,
            title=payload.title,
            description=payload.description,
            difficulty=payload.difficulty,
            prerequisites=payload.prerequisites,
        )
    except GraphConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except GraphValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_response(dto)


@router.patch("/{skill_id}", response_model=SkillResponse)
def update_skill(
    skill_id: str,
    payload: UpdateSkillRequest,
    graph_repo: InMemoryGraphRepository = Depends(get_graph_repo),
    graph_service: GraphService = Depends(get_graph_service),
) -> SkillResponse:
    try:
        dto = graph_service.update_skill(
            repo=graph_repo,
            skill_id=skill_id,
            title=payload.title,
            description=payload.description,
            difficulty=payload.difficulty,
            prerequisites=payload.prerequisites,
        )
    except GraphNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except GraphValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_response(dto)


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(
    skill_id: str,
    force: bool = Query(False),
    graph_repo: InMemoryGraphRepository = Depends(get_graph_repo),
    graph_service: GraphService = Depends(get_graph_service),
) -> Response:
    try:
        graph_service.delete_skill(repo=graph_repo, skill_id=skill_id, force=force)
    except GraphNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except GraphConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except GraphValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
