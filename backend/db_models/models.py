from datetime import datetime, UTC

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.db import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)


class UserKnowledgeStatusModel(Base):
    __tablename__ = "user_knowledge_statuses"
    __table_args__ = (
        UniqueConstraint("user_id", "skill_id", name="uq_user_knowledge_skill"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)


class LearningPlanModel(Base):
    __tablename__ = "learning_plans"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_plan_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    root_plan_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    source_skill_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    goal_target_skill_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    goal_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    ordered_skill_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    skill_statuses: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    skill_notes: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    graph_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class GraphStateModel(Base):
    __tablename__ = "graph_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
