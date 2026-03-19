from backend.domain.user import User


class InMemoryUserRepository:
    def __init__(self):
        self._users: dict[str, User] = {}

    def get(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    def save(self, user: User) -> User:
        self._users[user.id] = user
        return user
