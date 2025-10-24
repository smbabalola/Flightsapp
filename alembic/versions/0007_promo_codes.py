"""promo codes

Revision ID: 0007
Revises: 0006
Create Date: 2025-10-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create promo_codes table
    op.create_table(
        'promo_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('discount_type', sa.String(20), nullable=False),
        sa.Column('discount_value', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=True),
        sa.Column('max_uses', sa.Integer(), nullable=True),
        sa.Column('times_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('min_purchase_amount', sa.Float(), nullable=True),
        sa.Column('valid_from', sa.DateTime(), nullable=False),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_promo_codes_code', 'promo_codes', ['code'], unique=True)

    # Create promo_code_usage table
    op.create_table(
        'promo_code_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('promo_code_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('trip_id', sa.Integer(), nullable=True),
        sa.Column('discount_amount', sa.Float(), nullable=False),
        sa.Column('original_amount', sa.Float(), nullable=False),
        sa.Column('final_amount', sa.Float(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['promo_code_id'], ['promo_codes.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('promo_code_usage')
    op.drop_index('ix_promo_codes_code', table_name='promo_codes')
    op.drop_table('promo_codes')
