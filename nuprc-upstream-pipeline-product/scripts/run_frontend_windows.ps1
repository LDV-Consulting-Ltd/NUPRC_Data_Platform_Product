# FRONTEND (Next.js) - do not use venv/uvicorn; that is for the backend.
cd $PSScriptRoot\..
cd .\frontend

$env:BACKEND_URL="http://127.0.0.1:8000"
npm install
npm run dev -- --hostname 0.0.0.0 --port 3000
