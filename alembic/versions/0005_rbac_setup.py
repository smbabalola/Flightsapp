"""rbac setup - add created_at to users and create initial admin"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision = "0005_rbac_setup"
down_revision = "0004_cancellations"
branch_labels = None
depends_on = None

def upgrade():
    # Add created_at column to users table
    op.add_column("users", sa.Column("created_at", sa.DateTime, nullable=True, server_default=sa.func.now()))

    # Backfill created_at for existing users (cross-DB safe)
    conn = op.get_bind()
    dialect = conn.engine.dialect.name
    now_expr = "datetime('now')" if dialect == "sqlite" else "NOW()"
    conn.execute(sa.text(f"""
        UPDATE users
        SET created_at = {now_expr}
        WHERE created_at IS NULL
    """))

    # Create initial admin user if no users exist
    # Email: admin@sureflights.ng
    # Password: admin123 (MUST be changed immediately!)
    conn.execute(sa.text(f"""
        INSERT INTO users (email, name, role, hash_password, status, created_at)
        SELECT 'admin@sureflights.ng', 'System Administrator', 'admin',
               '$2b$12$G4ZyUAAs/7t0ntBhI/U6huPux8yH4byS/.ydJJS4Srl3snNvCas1a',
               'active', {now_expr}
        WHERE NOT EXISTS (SELECT 1 FROM users WHERE role = 'admin')
    """))

def downgrade():
    op.drop_column("users", "created_at")
