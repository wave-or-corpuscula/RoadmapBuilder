from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.api.security import get_current_user_id
from backend.api.dependencies import get_user_repo, get_user_service
from backend.repositories.user_repository import PostgresUserRepository
from backend.services.user_service import UserService


router = APIRouter(prefix="/users", tags=["users"])


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str


class UpdateMeRequest(BaseModel):
    email: str | None = Field(default=None, min_length=3)
    display_name: str | None = Field(default=None, min_length=1)


@router.get("/me", response_model=UserResponse)
def get_me(
    user_id: str = Depends(get_current_user_id),
    user_repo: PostgresUserRepository = Depends(get_user_repo),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    user = user_service.get_or_create_me(user_repo, user_id)
    return UserResponse(id=user.id, email=user.email, display_name=user.display_name)


@router.patch("/me", response_model=UserResponse)
def update_me(
    payload: UpdateMeRequest,
    user_id: str = Depends(get_current_user_id),
    user_repo: PostgresUserRepository = Depends(get_user_repo),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    user = user_service.update_me(
        repo=user_repo,
        user_id=user_id,
        email=payload.email,
        display_name=payload.display_name,
    )
    return UserResponse(id=user.id, email=user.email, display_name=user.display_name)
