@echo off
REM Railway Database Sync - Complete Process
REM This batch file guides you through the entire database sync process

echo.
echo ================================================================================
echo              RAILWAY DATABASE SYNC - AUTOMATED PROCESS
echo ================================================================================
echo.
echo This script will sync your local SQLite database to Railway PostgreSQL.
echo.
echo WARNING: This will DELETE ALL data in your Railway PostgreSQL database!
echo.
pause

echo.
echo Step 1: Checking local database...
echo ================================================================================
python check_migrations.py
if errorlevel 1 (
    echo.
    echo ERROR: Migration check failed!
    echo Please fix issues before continuing.
    pause
    exit /b 1
)

echo.
echo.
echo Step 2: Configure Railway DATABASE_URL
echo ================================================================================
echo.
echo Please get your DATABASE_URL from Railway:
echo 1. Go to Railway dashboard
echo 2. Click on PostgreSQL service
echo 3. Go to Variables tab
echo 4. Copy the DATABASE_URL value
echo.
set /p DATABASE_URL="Paste your Railway DATABASE_URL here: "

if "%DATABASE_URL%"=="" (
    echo.
    echo ERROR: No DATABASE_URL provided!
    pause
    exit /b 1
)

echo.
echo Setting DATABASE_URL for this session...
set DATABASE_URL=%DATABASE_URL%

echo.
echo.
echo Step 3: Running database sync...
echo ================================================================================
python sync_db_simple.py
if errorlevel 1 (
    echo.
    echo ERROR: Sync failed!
    echo Check the errors above and try again.
    pause
    exit /b 1
)

echo.
echo.
echo ================================================================================
echo                         SYNC COMPLETE!
echo ================================================================================
echo.
echo Your Railway PostgreSQL database now matches your local SQLite database.
echo.
echo Next steps:
echo 1. Test your Railway deployment
echo 2. Verify data in Railway dashboard
echo 3. Run any post-deployment checks
echo.
pause
