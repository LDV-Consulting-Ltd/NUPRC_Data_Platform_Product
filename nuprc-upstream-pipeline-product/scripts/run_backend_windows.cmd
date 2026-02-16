docker compose up -d
set DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/nuprc
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

