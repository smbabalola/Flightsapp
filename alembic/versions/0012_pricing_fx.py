"""add pricing config and pricing audit tables

Revision ID: 0012_pricing_fx
Revises: 0011_b2b_multitenant
Create Date: 2025-10-22
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0012_pricing_fx'
down_revision = '0011_b2b_multitenant'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'pricing_config',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('base_pricing_currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('default_display_currency', sa.String(length=3), nullable=False, server_default='NGN'),
        sa.Column('markup_percentage', sa.Float(), nullable=False, server_default='10'),
        sa.Column('booking_fee_fixed', sa.Integer(), nullable=False, server_default='5000'),
        sa.Column('payment_fee_percentage', sa.Float(), nullable=False, server_default='1.5'),
        sa.Column('fx_safety_margin_pct', sa.Float(), nullable=False, server_default='4.0'),
        sa.Column('supported_currencies', sa.JSON(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    op.create_table(
        'pricing_audit',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('event_date', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('base_currency', sa.String(length=3), nullable=False),
        sa.Column('display_currency', sa.String(length=3), nullable=False),
        sa.Column('raw_rate', sa.Float(), nullable=False),
        sa.Column('effective_rate', sa.Float(), nullable=False),
        sa.Column('margin_pct', sa.Float(), nullable=False),
        sa.Column('source', sa.String(length=32), nullable=True),
        sa.Column('context', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )


def downgrade() -> None:
    op.drop_table('pricing_audit')
    op.drop_table('pricing_config')

