"""add_firebase_uid_nullable_password

Revision ID: a1b2c3d4e5f6
Revises: db24696d8563
Create Date: 2026-04-30 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'db24696d8563'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('firebase_uid', sa.String(length=255), nullable=True))
    op.create_unique_constraint('uq_users_firebase_uid', 'users', ['firebase_uid'])
    op.alter_column('users', 'hashed_password', existing_type=sa.VARCHAR(), nullable=True)


def downgrade() -> None:
    op.alter_column('users', 'hashed_password', existing_type=sa.VARCHAR(), nullable=False)
    op.drop_constraint('uq_users_firebase_uid', 'users', type_='unique')
    op.drop_column('users', 'firebase_uid')
