"""initial schema"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255)),
        sa.Column("phone", sa.String(64)),
        sa.Column("channel", sa.String(32)),
        sa.Column("external_id", sa.String(128)),
        sa.Column("created_at", sa.DateTime),
    )
    op.create_table(
        "travelers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("customer_id", sa.Integer, sa.ForeignKey("customers.id")),
        sa.Column("title", sa.String(16)),
        sa.Column("first", sa.String(100), nullable=False),
        sa.Column("last", sa.String(100), nullable=False),
        sa.Column("dob", sa.String(16)),
        sa.Column("nationality", sa.String(3)),
        sa.Column("doc_hash", sa.String(128)),
        sa.Column("doc_last4", sa.String(8)),
    )
    op.create_table(
        "quotes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("offer_id", sa.String(100), nullable=False),
        sa.Column("price_minor", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("ngn_snapshot_rate", sa.String(16)),
        sa.Column("email", sa.String(255)),
        sa.Column("phone", sa.String(64)),
        sa.Column("channel", sa.String(32)),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("paystack_reference", sa.String(100)),
        sa.Column("raw_offer", sa.JSON),
        sa.Column("created_at", sa.DateTime),
    )
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("quote_id", sa.Integer, sa.ForeignKey("quotes.id")),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("reference", sa.String(100), nullable=False),
        sa.Column("amount_minor", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("raw", sa.JSON),
        sa.Column("created_at", sa.DateTime),
    )
    op.create_table(
        "trips",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("quote_id", sa.Integer, sa.ForeignKey("quotes.id")),
        sa.Column("supplier_order_id", sa.String(100)),
        sa.Column("pnr", sa.String(16)),
        sa.Column("etickets", sa.Text),
        sa.Column("email", sa.String(255)),
        sa.Column("phone", sa.String(64)),
        sa.Column("created_at", sa.DateTime),
        sa.Column("raw_order", sa.JSON),
    )
    op.create_table(
        "ancillaries",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("trip_id", sa.Integer, sa.ForeignKey("trips.id")),
        sa.Column("type", sa.String(16)),
        sa.Column("amount_minor", sa.Integer),
        sa.Column("currency", sa.String(3)),
        sa.Column("details", sa.JSON),
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("event", sa.String(64)),
        sa.Column("actor", sa.String(64)),
        sa.Column("details", sa.JSON),
        sa.Column("created_at", sa.DateTime),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(100)),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("hash_password", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
    )
    op.create_table(
        "fees",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("rule", sa.JSON),
        sa.Column("flat_minor", sa.Integer),
        sa.Column("percent", sa.Float),
    )

def downgrade():
    for t in ["fees","users","audit_logs","ancillaries","trips","payments","quotes","travelers","customers"]:
        op.drop_table(t)
