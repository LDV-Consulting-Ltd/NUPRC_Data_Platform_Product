# NUPRC Upstream Pipeline Product

A full-stack application for the **NUPRC Data Platform** that manages upstream pipeline runs, quality metrics, warehouse metadata, and diagrams. It consists of a FastAPI backend and a Next.js frontend.

---

## Quick start

### Backend (API)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload
```

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

- **Backend:** Optional `DATABASE_URL`. Defaults to `sqlite:///./nuprc.db` for local development (no Docker required).
- **Frontend:** Standard Next.js env; point `NEXT_PUBLIC_API_URL` at the backend if needed.

---

## Tech stack

- **Backend:** Python 3.x, FastAPI, SQLAlchemy, Pandas, Uvicorn. SQLite (dev) or PostgreSQL (e.g. via `DATABASE_URL`).
- **Frontend:** Next.js 16, React 19, TypeScript.

For more context and goals, see [ABOUT.md](./ABOUT.md).

---

## PetroCore Tanna Connector (v0.2.1)

PetroCore exposes a **read-only connector surface** at `/api/v1/tanna/*` from `backend/app/tanna_connector/`. Tanna must consume PetroCore **only** through this API — never direct database access.

v0.2.1 adds contract validation, sync readiness metadata, stable external_ids, and `/api/v1/tanna/status`. See connector README for maturity matrix and sync rules.

### Setup

Copy `backend/.env.example` and set:

```bash
TANNA_CONNECTOR_TOKEN=your-secret-service-token
```

All `/api/v1/tanna/*` requests require `Authorization: Bearer <TANNA_CONNECTOR_TOKEN>`.

### Connector endpoints

| Endpoint | Maturity |
|----------|----------|
| `GET /api/v1/tanna/manifest` | implemented |
| `GET /api/v1/tanna/health` | partial |
| `GET /api/v1/tanna/status` | implemented |
| `GET /api/v1/tanna/data-products` | implemented |
| `GET /api/v1/tanna/entities` | partial |
| `GET /api/v1/tanna/relationships` | partial |
| `GET /api/v1/tanna/signals` | partial |
| `GET /api/v1/tanna/patterns` | not_implemented |
| `GET /api/v1/tanna/illuminations` | partial |
| `GET /api/v1/tanna/decision-products` | placeholder |
| `GET /api/v1/tanna/knowledge-assets` | partial |

See [backend/app/tanna_connector/README.md](./backend/app/tanna_connector/README.md) for authentication, operational signal scope, and maturity notes.
