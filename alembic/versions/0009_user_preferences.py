"""user preferences - add country and currency to users"""
from alembic import op
import sqlalchemy as sa

revision = "0009_user_preferences"
down_revision = "0008"
branch_labels = None
depends_on = None

def upgrade():
    # Add country and preferred_currency columns to users table
    op.add_column("users", sa.Column("country", sa.String(2), nullable=True, server_default="GB"))
    op.add_column("users", sa.Column("preferred_currency", sa.String(3), nullable=True, server_default="GBP"))

    # Update existing users to have default values
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE users
        SET country = 'GB', preferred_currency = 'GBP'
        WHERE country IS NULL OR preferred_currency IS NULL
    """))

def downgrade():
    op.drop_column("users", "preferred_currency")
    op.drop_column("users", "country")
