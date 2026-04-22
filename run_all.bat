@echo off
setlocal
set SKIP_LOAD=0
if /I "%~1"=="--skip-load" set SKIP_LOAD=1

echo ==========================================
echo   Graphene Trace - Setup and Run
echo ==========================================

where python >nul 2>nul || (echo [ERROR] Python not found in PATH.& exit /b 1)

if not exist ".env" (
  if exist ".env.example" (
    echo [INFO] .env not found, creating from .env.example
    copy /Y ".env.example" ".env" >nul
  ) else (
    echo [ERROR] .env and .env.example not found.
    exit /b 1
  )
)

if not exist ".venv" (
  echo [INFO] Creating virtual environment...
  python -m venv .venv || (echo [ERROR] Failed to create virtual environment.& exit /b 1)
)

echo [INFO] Activating virtual environment...
call ".venv\Scripts\activate.bat" || (echo [ERROR] Failed to activate virtual environment.& exit /b 1)

echo [INFO] Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt || (echo [ERROR] Dependency installation failed.& exit /b 1)

set USE_SQLITE_FALLBACK=True
echo [INFO] SQLite mode enabled (no admin install needed).

echo [INFO] Running migrations...
python manage.py makemigrations || (echo [ERROR] makemigrations failed.& exit /b 1)
python manage.py migrate || (echo [ERROR] migrate failed.& exit /b 1)

if "%SKIP_LOAD%"=="1" (
  echo [INFO] Skipping CSV load by request.
) else if exist "GTLB-Data" (
  echo [INFO] Loading CSV sensor data from GTLB-Data...
  python manage.py load_sensor_csv --data-dir "GTLB-Data"
  if errorlevel 1 echo [WARN] CSV load encountered issues. Continuing to start server.
) else (
  echo [WARN] GTLB-Data folder not found, skipping CSV import.
)

echo.
echo [INFO] Starting Django dev server at http://127.0.0.1:8000
echo Press Ctrl+C to stop.
python manage.py runserver

endlocal
