"""add loyalty accounts table

Revision ID: 0010_loyalty_accounts
Revises: 0009_user_preferences
Create Date: 2025-10-04
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_loyalty_accounts"
down_revision = "0009_user_preferences"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "loyalty_accounts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("airline_iata_code", sa.String(length=8), nullable=False),
        sa.Column("programme_name", sa.String(length=128), nullable=True),
        sa.Column("loyalty_programme_id", sa.String(length=64), nullable=True),
        sa.Column("account_number_encrypted", sa.Text(), nullable=False),
        sa.Column("account_number_last4", sa.String(length=8), nullable=False),
        sa.Column("loyalty_tier", sa.String(length=64), nullable=True),
        sa.Column("perks_snapshot", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "airline_iata_code", name="uq_loyalty_user_airline"),
    )
    op.create_index("ix_loyalty_accounts_user_id", "loyalty_accounts", ["user_id"])
    op.create_index("ix_loyalty_accounts_airline", "loyalty_accounts", ["airline_iata_code"])


def downgrade():
    op.drop_index("ix_loyalty_accounts_airline", table_name="loyalty_accounts")
    op.drop_index("ix_loyalty_accounts_user_id", table_name="loyalty_accounts")
    op.drop_table("loyalty_accounts")
