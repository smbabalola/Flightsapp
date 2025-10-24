from pathlib import Path

path = Path("app/models/models.py")
text = path.read_text()
text = text.replace(
    "    metadata: Mapped[dict | None] = mapped_column(JSON)\n",
    "    extra: Mapped[dict | None] = mapped_column(JSON)\n"
)
text = text.replace(
    "    metadata: Mapped[dict | None] = mapped_column(JSON)\n    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)\n    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)\n",
    "    payload: Mapped[dict | None] = mapped_column(JSON)\n    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)\n    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)\n"
)
text = text.replace(
    "    metadata: Mapped[dict | None] = mapped_column(JSON)\n    submitted_at: Mapped[datetime | None] = mapped_column(DateTime)\n",
    "    custom_fields: Mapped[dict | None] = mapped_column(JSON)\n    submitted_at: Mapped[datetime | None] = mapped_column(DateTime)\n"
)
text = text.replace(
    "    metadata: Mapped[dict | None] = mapped_column(JSON)\n    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)\n    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)\n",
    "    context: Mapped[dict | None] = mapped_column(JSON)\n    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)\n    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)\n"
)
text = text.replace(
    "    metadata: Mapped[dict | None] = mapped_column(JSON)\n    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)\n",
    "    extra: Mapped[dict | None] = mapped_column(JSON)\n    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)\n"
)
path.write_text(text)
