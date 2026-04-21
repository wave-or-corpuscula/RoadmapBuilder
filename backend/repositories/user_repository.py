from backend.domain.user import User
from backend.core.db import SessionLocal
from backend.db_models.models import UserModel

class PostgresUserRepository:
    def get(self, user_id: str) -> User | None:
        with SessionLocal() as session:
            row = session.get(UserModel, user_id)
            if row is None:
                return None
            return User(
                id=row.id,
                email=row.email,
                display_name=row.display_name,
                hashed_password=row.hashed_password,
            )

    def get_by_email(self, email: str) -> User | None:
        with SessionLocal() as session:
            row = session.query(UserModel).filter(UserModel.email == email).one_or_none()
            if row is None:
                return None
            return User(
                id=row.id,
                email=row.email,
                display_name=row.display_name,
                hashed_password=row.hashed_password,
            )

    def save(self, user: User) -> User:
        with SessionLocal() as session:
            row = session.get(UserModel, user.id)
            if row is None:
                row = UserModel(
                    id=user.id,
                    email=user.email,
                    display_name=user.display_name,
                    hashed_password=user.hashed_password,
                )
                session.add(row)
            else:
                row.email = user.email
                row.display_name = user.display_name
                row.hashed_password = user.hashed_password
            session.commit()
        return user
