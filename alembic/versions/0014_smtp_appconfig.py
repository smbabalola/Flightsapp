"""add smtp_settings and app_config tables

Revision ID: 0014_smtp_appconfig
Revises: 0013_messaging_settings
Create Date: 2025-10-22
"""

from alembic import op
import sqlalchemy as sa


revision = '0014_smtp_appconfig'
down_revision = '0013_messaging_settings'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else "postgresql"
    true_default = sa.text('1') if dialect == 'sqlite' else sa.text('TRUE')

    op.create_table(
        'smtp_settings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('host', sa.String(length=255), nullable=True),
        sa.Column('port', sa.Integer(), nullable=True),
        sa.Column('user', sa.String(length=255), nullable=True),
        sa.Column('password', sa.String(length=255), nullable=True),
        sa.Column('from_email', sa.String(length=255), nullable=True),
        sa.Column('from_name', sa.String(length=255), nullable=True),
        sa.Column('use_tls', sa.Boolean(), nullable=False, server_default=true_default),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    op.create_table(
        'app_config',
        sa.Column('key', sa.String(length=100), primary_key=True),
        sa.Column('value', sa.String(length=500), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )


def downgrade() -> None:
    op.drop_table('app_config')
    op.drop_table('smtp_settings')
