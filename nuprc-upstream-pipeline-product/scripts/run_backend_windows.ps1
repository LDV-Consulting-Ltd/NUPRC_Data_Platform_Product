cd $PSScriptRoot\..
docker compose up -d

cd .\backend

if (!(Test-Path .\.venv)) { python -m venv .venv }
.\.venv\Scripts\Activate.ps1

$env:DATABASE_URL = if ($env:DATABASE_URL) { $env:DATABASE_URL } else { "postgresql+psycopg://postgres:postgres@localhost:5432/nuprc" }

python -m pip install --upgrade pip
pip install -r requirements.txt

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
