"""add payment method to payments

Revision ID: 0008
Revises: 0007
Create Date: 2025-10-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('payments', sa.Column('method', sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column('payments', 'method')
