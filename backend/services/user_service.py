from backend.domain.user import User
from backend.repositories.user_repository import PostgresUserRepository


class UserService:
    def get_or_create_me(self, repo: PostgresUserRepository, user_id: str) -> User:
        existing = repo.get(user_id)
        if existing is not None:
            return existing

        created = User(
            id=user_id,
            email=f"{user_id}@local.dev",
            display_name=user_id,
            hashed_password="",
        )
        return repo.save(created)

    def update_me(
        self,
        repo: PostgresUserRepository,
        user_id: str,
        email: str | None = None,
        display_name: str | None = None,
    ) -> User:
        current = self.get_or_create_me(repo, user_id)
        updated = User(
            id=current.id,
            email=email if email is not None else current.email,
            display_name=display_name if display_name is not None else current.display_name,
            hashed_password=current.hashed_password,
        )
        return repo.save(updated)
