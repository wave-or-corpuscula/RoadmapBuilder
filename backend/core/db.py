from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.core.config import settings


Base = declarative_base()
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db() -> None:
    import backend.db_models.models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def reset_db() -> None:
    import backend.db_models.models  # noqa: F401

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
