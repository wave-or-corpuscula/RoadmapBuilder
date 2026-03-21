from uuid import uuid4

from backend.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from backend.domain.user import User
from backend.repositories.user_repository import InMemoryUserRepository


class AuthConflictError(ValueError):
    pass


class AuthValidationError(ValueError):
    pass


class AuthUnauthorizedError(ValueError):
    pass


class AuthService:
    def register(
        self,
        repo: InMemoryUserRepository,
        email: str,
        password: str,
        display_name: str | None = None,
    ) -> User:
        normalized_email = email.strip().lower()
        if repo.get_by_email(normalized_email) is not None:
            raise AuthConflictError("Email already registered")

        if len(password) < 8:
            raise AuthValidationError("Password must be at least 8 characters")

        user = User(
            id=str(uuid4()),
            email=normalized_email,
            display_name=display_name or normalized_email.split("@")[0],
            hashed_password=hash_password(password),
        )
        return repo.save(user)

    def login(self, repo: InMemoryUserRepository, email: str, password: str) -> User:
        user = repo.get_by_email(email.strip().lower())
        if user is None or not verify_password(password, user.hashed_password):
            raise AuthUnauthorizedError("Invalid email or password")
        return user

    def issue_tokens(self, user_id: str) -> dict[str, str]:
        return {
            "access_token": create_access_token(user_id),
            "refresh_token": create_refresh_token(user_id),
            "token_type": "bearer",
        }

    def refresh(self, repo: InMemoryUserRepository, refresh_token: str) -> dict[str, str]:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise AuthUnauthorizedError("Invalid refresh token")

        user_id = payload.get("sub")
        if not user_id or repo.get(user_id) is None:
            raise AuthUnauthorizedError("Invalid refresh token")
        return self.issue_tokens(user_id)

    def get_user_id_from_access_token(self, token: str) -> str:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise AuthUnauthorizedError("Invalid access token")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthUnauthorizedError("Invalid access token")
        return user_id
