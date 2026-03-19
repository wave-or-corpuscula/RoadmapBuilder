from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from backend.api.dependencies import get_user_repo, get_user_service
from backend.repositories.user_repository import InMemoryUserRepository
from backend.services.user_service import UserService


router = APIRouter(prefix="/users", tags=["users"])


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str


class UpdateMeRequest(BaseModel):
    email: str | None = Field(default=None, min_length=3)
    display_name: str | None = Field(default=None, min_length=1)


def _require_user_id(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-User-Id header is required",
        )
    return user_id


@router.get("/me", response_model=UserResponse)
def get_me(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    user_repo: InMemoryUserRepository = Depends(get_user_repo),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    user_id = _require_user_id(x_user_id)
    user = user_service.get_or_create_me(user_repo, user_id)
    return UserResponse(id=user.id, email=user.email, display_name=user.display_name)


@router.patch("/me", response_model=UserResponse)
def update_me(
    payload: UpdateMeRequest,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    user_repo: InMemoryUserRepository = Depends(get_user_repo),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    user_id = _require_user_id(x_user_id)
    user = user_service.update_me(
        repo=user_repo,
        user_id=user_id,
        email=payload.email,
        display_name=payload.display_name,
    )
    return UserResponse(id=user.id, email=user.email, display_name=user.display_name)
