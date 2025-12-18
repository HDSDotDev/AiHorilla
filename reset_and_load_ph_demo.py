#!/usr/bin/env python
"""
Reset SQLite database and load comprehensive Philippines demo data

This script:
1. Deletes the SQLite database file
2. Runs migrations to recreate schema
3. Loads comprehensive Philippines demo data

Use this for local development to get rich, testable data.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("=" * 80)
    print("RESET & LOAD PHILIPPINES DEMO DATA (SQLite)")
    print("=" * 80)
    
    # Get project root
    project_root = Path(__file__).parent.absolute()
    os.chdir(project_root)
    
    # Find SQLite database file
    db_files = list(project_root.glob("*.sqlite3"))
    
    if db_files:
        db_file = db_files[0]
        print(f"\n[1/4] Found database: {db_file.name}")
        
        # Step 1: Delete database
        print(f"[2/4] Deleting {db_file.name}...")
        try:
            db_file.unlink()
            print(f"  [OK] Database deleted")
        except Exception as e:
            print(f"  [ERROR] Error deleting database: {e}")
            return False
    else:
        print(f"\n[1/4] No existing database found (will create new)")
        print(f"[2/4] Skipping deletion step")
    
    # Step 2: Run migrations
    print(f"\n[3/4] Running migrations to recreate schema...")
    try:
        result = subprocess.run(
            [sys.executable, "manage.py", "migrate"],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            print(f"  [OK] Migrations applied successfully")
        else:
            print(f"  [ERROR] Migration failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"  [ERROR] Error running migrations: {e}")
        return False
    
    # Step 3: Load Philippines demo data
    print(f"\n[4/4] Loading comprehensive Philippines demo data...")
    print("  This may take 2-5 minutes...")
    try:
        loader_script = project_root / "load_philippines_demo.py"
        if not loader_script.exists():
            print(f"  [ERROR] Loader script not found: {loader_script}")
            return False
        
        result = subprocess.run(
            [sys.executable, str(loader_script)],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes max
        )
        
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("\n" + "=" * 80)
            print("[SUCCESS] Philippines demo data loaded")
            print("=" * 80)
            print("\nLogin with:")
            print("  Username: admin")
            print("  Password: admin")
            print("\nThe system now has:")
            print("  - 30-50 employees with complete profiles")
            print("  - Attendance data (Sept-Oct 2025)")
            print("  - Shift requests and approvals")
            print("  - Work type requests (Remote, WFH, Office)")
            print("  - Overtime approvals")
            print("  - Leave requests and balances")
            print("  - Asset allocations")
            print("  - Helpdesk tickets")
            print("  - Payroll data with Philippines taxes")
            print("=" * 80)
            return True
        else:
            print(f"  [ERROR] Demo loader failed with exit code {result.returncode}")
            return False
            
    except Exception as e:
        print(f"  [ERROR] Error loading demo data: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
