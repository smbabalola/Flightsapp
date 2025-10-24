"""create messaging_settings table

Revision ID: 0013_messaging_settings
Revises: 0012_pricing_fx
Create Date: 2025-10-22
"""

from alembic import op
import sqlalchemy as sa


revision = '0013_messaging_settings'
down_revision = '0012_pricing_fx'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'messaging_settings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('welcome_subject', sa.String(length=255), nullable=True),
        sa.Column('welcome_body', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )


def downgrade() -> None:
    op.drop_table('messaging_settings')

