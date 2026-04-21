from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from backend.api.dependencies import get_auth_service, get_user_repo
from backend.repositories.user_repository import PostgresUserRepository
from backend.services.auth_service import AuthService, AuthUnauthorizedError


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user_id(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
    user_repo: PostgresUserRepository = Depends(get_user_repo),
) -> str:
    try:
        user_id = auth_service.get_user_id_from_access_token(token)
    except (ValueError, AuthUnauthorizedError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        ) from exc

    if user_repo.get(user_id) is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return user_id
