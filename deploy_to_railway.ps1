# Deploy Production Data to Railway
# This script automates the entire deployment process

Write-Host ""
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host " DEPLOY PRODUCTION DATA TO RAILWAY " -ForegroundColor Yellow
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if production data exists
$dataFile = "load_data\production_data.json"
if (-not (Test-Path $dataFile)) {
    Write-Host "❌ Production data not found!" -ForegroundColor Red
    Write-Host "Run this first: python export_production_data.py" -ForegroundColor Yellow
    exit 1
}

$sizeMB = (Get-Item $dataFile).Length / 1MB
Write-Host "✅ Production data found: $($sizeMB.ToString('F2')) MB" -ForegroundColor Green
Write-Host ""

# Step 2: Check git status
Write-Host "Checking git status..." -ForegroundColor Cyan
git status --short

Write-Host ""
Write-Host "Files to deploy:" -ForegroundColor Yellow
Write-Host "  - load_data/production_data.json ($($sizeMB.ToString('F2')) MB)" -ForegroundColor Gray
Write-Host "  - export_production_data.py" -ForegroundColor Gray
Write-Host "  - base/management/commands/load_production_data.py" -ForegroundColor Gray
Write-Host "  - base/management/commands/railway_init_db.py" -ForegroundColor Gray
Write-Host ""

# Step 3: Confirm
$confirm = Read-Host "Deploy to Railway? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "Deployment cancelled." -ForegroundColor Yellow
    exit 0
}

# Step 4: Add files
Write-Host ""
Write-Host "Adding files to git..." -ForegroundColor Cyan
git add load_data/production_data.json
git add export_production_data.py
git add base/management/commands/load_production_data.py
git add base/management/commands/railway_init_db.py

# Step 5: Commit
Write-Host "Committing..." -ForegroundColor Cyan
git commit -m "Deploy production data to Railway"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "⚠️  Nothing to commit (files already committed)" -ForegroundColor Yellow
    Write-Host "Proceeding with push..." -ForegroundColor Cyan
}

# Step 6: Push to Railway
Write-Host ""
Write-Host "Pushing to Railway..." -ForegroundColor Cyan
Write-Host ("=" * 80) -ForegroundColor Cyan
git push railway main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host ("=" * 80) -ForegroundColor Green
    Write-Host " ✅ DEPLOYMENT STARTED! " -ForegroundColor Green
    Write-Host ("=" * 80) -ForegroundColor Green
    Write-Host ""
    Write-Host "Railway is now deploying your application with production data." -ForegroundColor White
    Write-Host ""
    Write-Host "What happens next:" -ForegroundColor Yellow
    Write-Host "1. Railway builds your app" -ForegroundColor Gray
    Write-Host "2. Runs database migrations" -ForegroundColor Gray
    Write-Host "3. Loads your production data (30+ MB)" -ForegroundColor Gray
    Write-Host "4. Starts the application" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Monitor deployment:" -ForegroundColor Yellow
    Write-Host "  https://railway.app/dashboard" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "❌ Push failed!" -ForegroundColor Red
    Write-Host "Check the error above and try again." -ForegroundColor Yellow
    exit 1
}
