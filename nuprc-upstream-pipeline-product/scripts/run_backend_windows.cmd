cd /d "%~dp0.."
docker compose up -d
set DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/nuprc
cd backend
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
