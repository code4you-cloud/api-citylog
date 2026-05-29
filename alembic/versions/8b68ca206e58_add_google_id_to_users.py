"""add_google_id_to_users

Revision ID: 8b68ca206e58
Revises: 8483117d2787
Create Date: 2026-03-31 16:14:21.866957

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '8b68ca206e58'
down_revision: Union[str, None] = '8483117d2787'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('google_id', sa.String(length=50), nullable=True))
    op.create_index(op.f('ix_users_google_id'), 'users', ['google_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_google_id'), table_name='users')
    op.drop_column('users', 'google_id')
