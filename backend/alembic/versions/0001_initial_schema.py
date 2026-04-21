"""initial schema

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-04-21 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "graph_state",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "learning_plans",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("parent_plan_id", sa.String(length=64), nullable=True),
        sa.Column("root_plan_id", sa.String(length=64), nullable=True),
        sa.Column("source_skill_id", sa.String(length=128), nullable=True),
        sa.Column("fingerprint", sa.String(length=64), nullable=True),
        sa.Column("goal_target_skill_ids", sa.JSON(), nullable=False),
        sa.Column("goal_mode", sa.String(length=32), nullable=False),
        sa.Column("ordered_skill_ids", sa.JSON(), nullable=False),
        sa.Column("skill_statuses", sa.JSON(), nullable=False),
        sa.Column("skill_notes", sa.JSON(), nullable=False),
        sa.Column("graph_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_learning_plans_fingerprint"), "learning_plans", ["fingerprint"], unique=False)
    op.create_index(op.f("ix_learning_plans_parent_plan_id"), "learning_plans", ["parent_plan_id"], unique=False)
    op.create_index(op.f("ix_learning_plans_root_plan_id"), "learning_plans", ["root_plan_id"], unique=False)
    op.create_index(op.f("ix_learning_plans_user_id"), "learning_plans", ["user_id"], unique=False)

    op.create_table(
        "user_knowledge_statuses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("skill_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "skill_id", name="uq_user_knowledge_skill"),
    )
    op.create_index(
        op.f("ix_user_knowledge_statuses_user_id"),
        "user_knowledge_statuses",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_knowledge_statuses_user_id"), table_name="user_knowledge_statuses")
    op.drop_table("user_knowledge_statuses")
    op.drop_index(op.f("ix_learning_plans_user_id"), table_name="learning_plans")
    op.drop_index(op.f("ix_learning_plans_root_plan_id"), table_name="learning_plans")
    op.drop_index(op.f("ix_learning_plans_parent_plan_id"), table_name="learning_plans")
    op.drop_index(op.f("ix_learning_plans_fingerprint"), table_name="learning_plans")
    op.drop_table("learning_plans")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_table("graph_state")

