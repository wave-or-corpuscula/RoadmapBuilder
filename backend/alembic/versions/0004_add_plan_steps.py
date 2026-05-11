"""add plan steps

Revision ID: 0004_add_plan_steps
Revises: 0003_remove_learning_steps
Create Date: 2025-05-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0004_add_plan_steps'
down_revision: Union[str, None] = '0003_remove_learning_steps'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'learning_plans',
        sa.Column('plan_steps', sa.JSON(), nullable=False, server_default='[]')
    )


def downgrade() -> None:
    op.drop_column('learning_plans', 'plan_steps')