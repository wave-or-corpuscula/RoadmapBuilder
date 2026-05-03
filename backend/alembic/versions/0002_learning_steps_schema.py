"""add learning steps columns

Revision ID: 0002_learning_steps_schema
Revises: 0001_initial_schema
Create Date: 2026-05-03 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_learning_steps_schema"
down_revision: Union[str, Sequence[str], None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "learning_plans",
        sa.Column("plan_steps", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
    )
    op.add_column(
        "learning_plans",
        sa.Column("step_statuses", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )
    op.alter_column("learning_plans", "plan_steps", server_default=None)
    op.alter_column("learning_plans", "step_statuses", server_default=None)


def downgrade() -> None:
    op.drop_column("learning_plans", "step_statuses")
    op.drop_column("learning_plans", "plan_steps")
