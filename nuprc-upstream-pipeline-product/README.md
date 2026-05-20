# NUPRC Upstream Pipeline Product

A full-stack application for the **NUPRC Data Platform** that manages upstream pipeline runs, quality metrics, warehouse metadata, and diagrams. It consists of a FastAPI backend and a Next.js frontend.

---

## Quick start

### Database (PostgreSQL)

```bash
docker compose up -d
```

Default URL: `postgresql+psycopg://postgres:postgres@localhost:5432/nuprc`  
Production: set `DATABASE_URL` to your **Supabase** connection string.

### Backend (API)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
# Windows: set DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/nuprc
uvicorn app.main:app --reload
```

Or: `.\scripts\run_backend_windows.ps1` (Docker + backend).

API runs at **http://localhost:8000**.  
Docs: **http://localhost:8000/docs**

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:3000**.

---

## Project structure

```
nuprc-upstream-pipeline-product/
├── backend/                 # FastAPI API
│   ├── app/
│   │   ├── core/            # DB and config
│   │   ├── models/          # Run store, pipeline_run, pipeline_log
│   │   ├── routers/         # runs, quality, diagrams, warehouse, health
│   │   └── main.py
│   └── requirements.txt
├── frontend/                # Next.js app (React 19, TypeScript)
│   ├── app/
│   └── package.json
├── README.md
└── ABOUT.md                 # About this project
```

---

## API overview

| Endpoint | Description |
|----------|-------------|
| `GET /` | Service info |
| `GET /health/summary` | Health check (status: green) |
| `GET /runs/` | List last 50 pipeline runs |
| `GET /runs/summary` | Run counts (total, success, failed, running) and last run |
| `GET /quality/summary` | Quality KPIs (placeholder) |
| `GET /warehouse/tables` | Warehouse table list (placeholder) |
| `GET /diagrams` | Diagram items (placeholder) |

---

## Environment

- **Backend:** `DATABASE_URL` — **PostgreSQL only** (Docker Postgres locally; Supabase in production). See `backend/env.example`.
- **Frontend:** `BACKEND_URL` for API proxy (default `http://127.0.0.1:8000`).

---

## Tech stack

- **Backend:** Python 3.x, FastAPI, SQLAlchemy, Pandas, Uvicorn, **PostgreSQL** (JSONB, schemas, identity columns).
- **Frontend:** Next.js 16, React 19, TypeScript.

For more context and goals, see [ABOUT.md](./ABOUT.md).
