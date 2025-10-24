@echo off
echo ========================================
echo   SUREFLIGHTS - Twitter DM Bot Server
echo ========================================
echo.
echo Starting server on port 8001...
echo.
echo IMPORTANT:
echo 1. Keep ngrok running in another terminal
echo 2. Your bot account: @sho87698
echo 3. Check ngrok for your HTTPS URL
echo.
echo ========================================
echo.

REM Configure Postgres connection (override here or set in .env)
set DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/sureflights
REM Run DB migrations before starting the server
python -m alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
