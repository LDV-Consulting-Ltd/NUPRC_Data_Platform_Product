#!/bin/bash
# Bash script to restart the FastAPI backend (Linux/Mac)

echo "Restarting FastAPI backend..."

# Navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_ROOT"

# Kill any existing uvicorn processes
echo "Stopping existing backend processes..."
pkill -f "uvicorn app.main:app" || echo "No existing backend processes found"
sleep 2

# Navigate to backend directory
cd backend

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Start the backend
echo "Starting FastAPI backend on http://0.0.0.0:8000..."
echo "Press Ctrl+C to stop"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
