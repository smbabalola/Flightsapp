from pathlib import Path

path = Path("alembic/versions/0011_b2b_multitenant.py")
text = path.read_text()
text = text.replace('sa.Column("metadata", sa.JSON(), nullable=True),', 'sa.Column("extra", sa.JSON(), nullable=True),', 1)
text = text.replace('sa.Column("metadata", sa.JSON(), nullable=True),', 'sa.Column("payload", sa.JSON(), nullable=True),', 1)
text = text.replace('sa.Column("metadata", sa.JSON(), nullable=True),', 'sa.Column("custom_fields", sa.JSON(), nullable=True),', 1)
text = text.replace('sa.Column("metadata", sa.JSON(), nullable=True),', 'sa.Column("context", sa.JSON(), nullable=True),', 1)
text = text.replace('sa.Column("metadata", sa.JSON(), nullable=True),', 'sa.Column("extra", sa.JSON(), nullable=True),', 1)
path.write_text(text)
