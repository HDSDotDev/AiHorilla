@echo off
echo ========================================
echo   Starting Horilla HR System
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo ? Virtual environment not found!
    echo Please run setup.bat first
    pause
    exit /b 1
)

echo ?? Activating virtual environment...
call venv\Scripts\activate.bat

echo ?? Starting Horilla server...
echo.
echo ? Server will start at: http://127.0.0.1:8000
echo ? Admin login: admin / admin123
echo ? Handbook Chat: http://127.0.0.1:8000/handbook/
echo.
echo Press Ctrl+C to stop the server
echo.

python manage.py runserver 127.0.0.1:8000
pause