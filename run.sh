#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# Check for .env
if [ ! -f .env ]; then
    echo "ERROR: .env file not found."
    echo "Create a .env file with your OPENROUTER_API_KEY."
    exit 1
fi

# Create venv if it doesn't exist
if [ ! -d .venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install deps if needed (check for fastapi as a proxy)
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo ""
echo "Starting Precio..."
echo "Open in your browser: http://localhost:8000"
echo ""

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
