# Local setup (PostgreSQL)

1) Start PostgreSQL and create database `sureflights`
2) Set `DATABASE_URL` (or edit `.env`):
   - PowerShell: `$Env:DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/sureflights"`
3) Install deps: `pip install -r requirements.txt`
4) Run migrations: `python -m alembic upgrade head`
5) Run API: `uvicorn app.main:app --reload`

