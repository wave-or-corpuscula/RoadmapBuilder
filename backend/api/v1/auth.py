from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.api.dependencies import get_auth_service, get_user_repo
from backend.repositories.user_repository import InMemoryUserRepository
from backend.services.auth_service import (
    AuthConflictError,
    AuthService,
    AuthUnauthorizedError,
    AuthValidationError,
)


router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)
    display_name: str | None = Field(default=None, min_length=1)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)


class RefreshRequest(BaseModel):
    refresh_token: str


class AuthTokensResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


@router.post("/register", response_model=AuthTokensResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    user_repo: InMemoryUserRepository = Depends(get_user_repo),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthTokensResponse:
    try:
        user = auth_service.register(
            repo=user_repo,
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
        )
    except AuthConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except AuthValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return AuthTokensResponse(**auth_service.issue_tokens(user.id))


@router.post("/login", response_model=AuthTokensResponse)
def login(
    payload: LoginRequest,
    user_repo: InMemoryUserRepository = Depends(get_user_repo),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthTokensResponse:
    try:
        user = auth_service.login(repo=user_repo, email=payload.email, password=payload.password)
    except AuthUnauthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return AuthTokensResponse(**auth_service.issue_tokens(user.id))


@router.post("/refresh", response_model=AuthTokensResponse)
def refresh(
    payload: RefreshRequest,
    user_repo: InMemoryUserRepository = Depends(get_user_repo),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthTokensResponse:
    try:
        tokens = auth_service.refresh(repo=user_repo, refresh_token=payload.refresh_token)
    except (AuthUnauthorizedError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return AuthTokensResponse(**tokens)
