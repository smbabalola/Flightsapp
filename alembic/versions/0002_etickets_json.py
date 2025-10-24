"""add etickets_json column and backfill"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
import json

revision = "0002_etickets_json"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("trips", sa.Column("etickets_json", sa.JSON, nullable=True))
    conn = op.get_bind()
    res = conn.execute(text("SELECT id, etickets FROM trips WHERE etickets IS NOT NULL AND etickets <> ''"))
    for row in res:
        csv = row.etickets or ''
        arr = [x for x in csv.split(',') if x]
        conn.execute(text("UPDATE trips SET etickets_json=:j WHERE id=:i"), {"j": json.dumps(arr), "i": row.id})


def downgrade():
    op.drop_column("trips", "etickets_json")
