"""add cancellations table and trip status"""
from alembic import op
import sqlalchemy as sa

revision = "0004_cancellations"
down_revision = "0003_admin_dashboard_columns"
branch_labels = None
depends_on = None

def upgrade():
    # Create cancellations table
    op.create_table(
        "cancellations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("trip_id", sa.Integer, sa.ForeignKey("trips.id"), nullable=False),
        sa.Column("quote_id", sa.Integer, sa.ForeignKey("quotes.id"), nullable=False),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("refund_amount_minor", sa.Integer, nullable=True),
        sa.Column("refund_currency", sa.String(3), nullable=True),
        sa.Column("refund_status", sa.String(32), nullable=True),
        sa.Column("refund_reference", sa.String(100), nullable=True),
        sa.Column("supplier_cancellation_id", sa.String(100), nullable=True),
        sa.Column("cancelled_by", sa.String(64), nullable=True),  # customer, admin, system
        sa.Column("raw_cancellation", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )

    # Add trip_status to trips table
    op.add_column("trips", sa.Column("status", sa.String(32), nullable=True, server_default="active"))

    # Backfill existing trips as active
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE trips
        SET status = 'active'
        WHERE status IS NULL
    """))

def downgrade():
    op.drop_column("trips", "status")
    op.drop_table("cancellations")
