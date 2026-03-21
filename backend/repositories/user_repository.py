from backend.domain.user import User


class InMemoryUserRepository:
    def __init__(self):
        self._users: dict[str, User] = {}
        self._email_to_user_id: dict[str, str] = {}

    def get(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        user_id = self._email_to_user_id.get(email)
        if user_id is None:
            return None
        return self._users.get(user_id)

    def save(self, user: User) -> User:
        existing = self.get(user.id)
        if existing is not None and existing.email != user.email:
            self._email_to_user_id.pop(existing.email, None)

        self._users[user.id] = user
        self._email_to_user_id[user.email] = user.id
        return user
