@echo off
cd /d "%~dp0"

if not exist .env (
    echo ERROR: .env file not found.
    echo Create a .env file with your OPENROUTER_API_KEY.
    pause
    exit /b 1
)

echo.
echo Starting Precio...
echo Open in your browser: http://localhost:8000
echo.

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
