@echo FRONTEND (Next.js) - do not use venv/uvicorn; that is for the backend.
cd frontend
npm install
set BACKEND_URL=http://127.0.0.1:8001
npm run dev -- --hostname 0.0.0.0 --port 3000

