"""remove learning steps columns

Revision ID: 0003_remove_learning_steps
Revises: 0002_learning_steps_schema
Create Date: 2026-05-04 12:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0003_remove_learning_steps"
down_revision: Union[str, Sequence[str], None] = "0002_learning_steps_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("learning_plans", "step_statuses")
    op.drop_column("learning_plans", "plan_steps")


def downgrade() -> None:
    op.add_column(
        "learning_plans",
        op.column("plan_steps", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
    )
    op.add_column(
        "learning_plans",
        op.column("step_statuses", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )