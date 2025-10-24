"""add admin dashboard columns to quotes table"""
from alembic import op
import sqlalchemy as sa

revision = "0003_admin_dashboard_columns"
down_revision = "0002_etickets_json"
branch_labels = None
depends_on = None

def upgrade():
    # Add columns needed for admin dashboard
    op.add_column("quotes", sa.Column("pnr", sa.String(20), nullable=True))
    op.add_column("quotes", sa.Column("total_price_ngn", sa.Float, nullable=True))
    op.add_column("quotes", sa.Column("route_summary", sa.String(255), nullable=True))
    op.add_column("quotes", sa.Column("passenger_info", sa.Text, nullable=True))
    op.add_column("quotes", sa.Column("updated_at", sa.DateTime, nullable=True))

    # Backfill total_price_ngn from price_minor and currency
    # For existing records, calculate NGN equivalent
    conn = op.get_bind()

    # Set default updated_at to created_at for existing rows
    conn.execute(sa.text("""
        UPDATE quotes
        SET updated_at = created_at
        WHERE updated_at IS NULL
    """))

    # Calculate total_price_ngn for existing records
    # NGN: price_minor / 100
    # USD: price_minor / 100 * ngn_snapshot_rate (if available)
    conn.execute(sa.text("""
        UPDATE quotes
        SET total_price_ngn = CASE
            WHEN currency = 'NGN' THEN CAST(price_minor AS FLOAT) / 100
            WHEN currency = 'USD' AND ngn_snapshot_rate IS NOT NULL
                THEN (CAST(price_minor AS FLOAT) / 100) * CAST(ngn_snapshot_rate AS FLOAT)
            ELSE CAST(price_minor AS FLOAT) / 100
        END
        WHERE total_price_ngn IS NULL
    """))


def downgrade():
    op.drop_column("quotes", "updated_at")
    op.drop_column("quotes", "passenger_info")
    op.drop_column("quotes", "route_summary")
    op.drop_column("quotes", "total_price_ngn")
    op.drop_column("quotes", "pnr")
