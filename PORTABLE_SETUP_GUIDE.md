# ?? Portable Horilla Setup Guide

## Making Your Horilla + Handbook Chatbot Portable

### Step 1: Create Requirements File
```bash
# On your current machine, generate requirements
pip freeze > requirements.txt
```

### Step 2: Create Portable Environment Script
```bash
# Windows (create setup.bat)
@echo off
echo Setting up Horilla with Handbook Chatbot...

# Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    echo Please install Python 3.8+ first
    pause
    exit /b 1
)

# Create virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

# Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

# Install requirements
echo Installing requirements...
pip install -r requirements.txt

# Run migrations
echo Setting up database...
python manage.py migrate

# Create superuser (optional)
echo Creating admin user...
python manage.py createsuperuser --noinput --username admin --email admin@example.com
python manage.py shell -c "from django.contrib.auth.models import User; u=User.objects.get(username='admin'); u.set_password('admin123'); u.save()"

# Setup handbook data
echo Setting up handbook data...
python manage.py setup_handbook --create-sample-data

echo Setup complete!
echo Run 'start.bat' to start the server
pause
```

### Step 3: Create Startup Script
```bash
# Windows (create start.bat)
@echo off
echo Starting Horilla with Handbook Chatbot...
call venv\Scripts\activate.bat
python manage.py runserver 127.0.0.1:8000
pause
```

### Step 4: Environment Configuration
Create `.env` file with all required settings:
```env
# Basic Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Database (use relative path)
DATABASE_URL=sqlite:///./db.sqlite3

# Handbook AI Configuration  
GROQ_API_KEY=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
HANDBOOK_AI_BACKEND=groq
HANDBOOK_AI_MAX_TOKENS=700

# Media and Static files (relative paths)
MEDIA_ROOT=./media/
STATIC_ROOT=./staticfiles/
```

### Step 5: Update Settings for Portability
```python
# In horilla/settings.py, ensure relative paths:
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Database with relative path
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # Relative path
    }
}

# Media files with relative path
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'
```

### Step 6: Package Structure
```
?? Horilla-Portable/
??? ?? setup.bat           # Setup script
??? ?? start.bat           # Startup script  
??? ?? requirements.txt    # Python dependencies
??? ?? .env               # Environment variables
??? ?? README_PORTABLE.md # Setup instructions
??? ?? horilla/           # Your project files
??? ?? handbook/          # Handbook app
??? ?? media/             # Uploaded files
??? ?? manage.py
??? ?? db.sqlite3         # Database file
```