from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.api.dependencies import get_graph_repo, get_graph_service
from backend.repositories.graph_repository import PostgresGraphRepository
from backend.services.graph_service import GraphService, GraphValidationError


router = APIRouter(prefix="/graph", tags=["graph"])


class ValidateGraphResponse(BaseModel):
    valid: bool


@router.get("")
def get_graph(
    graph_repo: PostgresGraphRepository = Depends(get_graph_repo),
    graph_service: GraphService = Depends(get_graph_service),
) -> dict:
    return graph_service.graph_to_payload(graph_repo.get())


@router.post("/validate", response_model=ValidateGraphResponse)
def validate_graph(
    payload: dict,
    graph_service: GraphService = Depends(get_graph_service),
) -> ValidateGraphResponse:
    try:
        graph_service.validate_graph_payload(payload)
    except GraphValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ValidateGraphResponse(valid=True)
