@echo off
echo ========================================
echo   Horilla HR + Handbook Chatbot Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ? Python is not installed or not in PATH
    echo Please install Python 3.8+ first
    echo Download from: https://python.org/downloads/
    pause
    exit /b 1
)

echo ? Python found
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo ?? Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ? Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ? Virtual environment created
) else (
    echo ? Virtual environment already exists
)

echo.
echo ?? Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo ?? Installing Python packages...
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ? Failed to install requirements
    pause
    exit /b 1
)

echo.
echo ??? Setting up database...
python manage.py makemigrations
python manage.py migrate
if errorlevel 1 (
    echo ? Database setup failed
    pause
    exit /b 1
)

echo.
echo ?? Creating admin user...
echo from django.contrib.auth.models import User; User.objects.filter(username='admin').delete(); User.objects.create_superuser('admin', 'admin@example.com', 'admin123') | python manage.py shell
if errorlevel 1 (
    echo ?? Admin user creation failed, but continuing...
)

echo.
echo ?? Setting up handbook data...
python manage.py setup_handbook --create-sample-data
if errorlevel 1 (
    echo ?? Handbook setup failed, but continuing...
)

echo.
echo ?? Setup Complete!
echo.
echo To start the server:
echo   1. Run: start.bat
echo   2. Open browser to: http://127.0.0.1:8000
echo   3. Login with: admin / admin123
echo   4. Go to: Handbook ? Chat Assistant
echo.
pause