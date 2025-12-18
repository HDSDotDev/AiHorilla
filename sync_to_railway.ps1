# Railway Database Sync - PowerShell Version
# This script guides you through syncing SQLite to Railway PostgreSQL

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host ("=" * 80) -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Yellow
    Write-Host ("=" * 80) -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error-Message {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Warning-Message {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

# Main script
Clear-Host
Write-Step "RAILWAY DATABASE SYNC - AUTOMATED PROCESS"
Write-Host ""
Write-Warning-Message "This will sync your local SQLite database to Railway PostgreSQL."
Write-Warning-Message "ALL existing data in PostgreSQL will be DELETED!"
Write-Host ""

$continue = Read-Host "Do you want to continue? (yes/no)"
if ($continue -ne "yes") {
    Write-Host "Sync cancelled." -ForegroundColor Yellow
    exit 0
}

# Step 1: Check migrations
Write-Step "STEP 1: Checking Local Database Migrations"
Write-Host "Running migration checker..." -ForegroundColor Cyan

$result = python check_migrations.py
$exitCode = $LASTEXITCODE

if ($exitCode -ne 0) {
    Write-Error-Message "Migration check failed!"
    Write-Host "Please fix the issues above before continuing."
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Success "Migration check passed!"
Start-Sleep -Seconds 2

# Step 2: Get DATABASE_URL
Write-Step "STEP 2: Configure Railway DATABASE_URL"
Write-Host ""
Write-Host "To get your DATABASE_URL from Railway:" -ForegroundColor White
Write-Host "1. Go to https://railway.app/dashboard" -ForegroundColor Gray
Write-Host "2. Open your project" -ForegroundColor Gray
Write-Host "3. Click on the PostgreSQL service (not your app)" -ForegroundColor Gray
Write-Host "4. Click the 'Variables' tab" -ForegroundColor Gray
Write-Host "5. Find and copy the DATABASE_URL value" -ForegroundColor Gray
Write-Host ""
Write-Host "The URL should look like:" -ForegroundColor White
Write-Host "postgresql://postgres:password@region.railway.app:port/railway" -ForegroundColor DarkGray
Write-Host ""

$databaseUrl = Read-Host "Paste your Railway DATABASE_URL here"

if ([string]::IsNullOrWhiteSpace($databaseUrl)) {
    Write-Error-Message "No DATABASE_URL provided!"
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not ($databaseUrl -match "^postgres(ql)?://")) {
    Write-Warning-Message "URL doesn't look like a PostgreSQL connection string."
    $proceed = Read-Host "Do you want to proceed anyway? (yes/no)"
    if ($proceed -ne "yes") {
        Write-Host "Sync cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# Set environment variable
$env:DATABASE_URL = $databaseUrl
Write-Success "DATABASE_URL configured for this session"
Write-Host "   Database URL set: $($databaseUrl.Substring(0, [Math]::Min(40, $databaseUrl.Length)))..." -ForegroundColor DarkGray

# Step 3: Run sync
Write-Step "STEP 3: Running Database Sync"
Write-Host ""
Write-Warning-Message "Starting sync process..."
Write-Warning-Message "You will be asked to confirm data deletion."
Write-Host ""
Start-Sleep -Seconds 2

python sync_db_simple.py
$syncExitCode = $LASTEXITCODE

if ($syncExitCode -ne 0) {
    Write-Error-Message "Sync failed!"
    Write-Host "Check the error messages above for details."
    Read-Host "Press Enter to exit"
    exit 1
}

# Success!
Write-Step "SYNC COMPLETE!"
Write-Host ""
Write-Success "Your Railway PostgreSQL database now matches your local SQLite database!"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "1. Test your Railway deployment" -ForegroundColor Gray
Write-Host "2. Verify data through Railway dashboard or admin panel" -ForegroundColor Gray
Write-Host "3. Check application logs for any issues" -ForegroundColor Gray
Write-Host ""
Write-Host "Backup file created: full_database_dump.json" -ForegroundColor DarkGray
Write-Host ""

Read-Host "Press Enter to exit"
