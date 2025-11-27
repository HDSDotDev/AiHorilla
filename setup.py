#!/usr/bin/env python
"""
HORILLA HRMS - UNIVERSAL SETUP SCRIPT
Handles fresh installs AND updates on existing installations

This script automatically detects your database state and:
- Fresh install: Runs all migrations normally
- Existing install: Only applies new Philippines payroll migrations
- Broken install: Repairs migration state and continues

Usage:
    python setup.py                    # Interactive mode
    python setup.py --auto             # Auto-detect and run
    python setup.py --fresh            # Force fresh install
    python setup.py --philippines-only # Only setup Philippines features

NO MANUAL INTERVENTION NEEDED!
"""

import os
import sys
import django
import argparse
from pathlib import Path

# Setup Django environment
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from django.core.management import call_command
from django.db import connection


class HorillaSetup:
    """Smart setup handler for Horilla HRMS"""
    
    def __init__(self, auto_mode=False, fresh_install=False, philippines_only=False):
        self.auto_mode = auto_mode
        self.fresh_install = fresh_install
        self.philippines_only = philippines_only
        self.db_state = None
        
    def print_banner(self):
        """Print welcome banner"""
        print("\n" + "=" * 80)
        print("  🚀 HORILLA HRMS - PHILIPPINES PAYROLL EDITION")
        print("  📦 Universal Setup & Installation Script")
        print("=" * 80)
        print("\n  Features:")
        print("  ✅ Auto-detects database state")
        print("  ✅ Handles fresh installs and updates")
        print("  ✅ Repairs broken migration states")
        print("  ✅ One-command setup for all scenarios")
        print("\n" + "=" * 80 + "\n")
    
    def detect_database_state(self):
        """
        Detect current database state to determine installation type
        
        Returns:
            'fresh': No tables exist - fresh installation
            'partial': Some tables exist - needs repair
            'complete': All base tables exist - update only
        """
        print("\n🔍 Detecting database state...")
        print("-" * 80)
        
        cursor = connection.cursor()
        
        # Check for core Horilla tables
        core_tables = [
            'payroll_allowance',
            'payroll_deduction', 
            'payroll_payslip',
            'employee_employee',
        ]
        
        # Check for Philippines tables
        philippines_tables = [
            'payroll_philippinesregion',
            'payroll_philippinesssscontribution',
            'payroll_philippinesbirform2316',
            'payroll_philippinesfinalpay',
            'payroll_philippinesgovernmentremittance',
        ]
        
        existing_core = []
        existing_philippines = []
        
        # SQLite table check
        for table in core_tables:
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';"
            )
            if cursor.fetchone():
                existing_core.append(table)
        
        for table in philippines_tables:
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';"
            )
            if cursor.fetchone():
                existing_philippines.append(table)
        
        # Determine state
        if len(existing_core) == 0:
            state = 'fresh'
            print(f"  📊 Status: FRESH INSTALLATION")
            print(f"  ℹ️  No existing tables found")
        elif len(existing_core) == len(core_tables):
            if len(existing_philippines) == len(philippines_tables):
                state = 'complete'
                print(f"  📊 Status: COMPLETE INSTALLATION")
                print(f"  ✅ All core tables: {len(existing_core)}/{len(core_tables)}")
                print(f"  ✅ All Philippines tables: {len(existing_philippines)}/{len(philippines_tables)}")
            else:
                state = 'update'
                print(f"  📊 Status: UPDATE REQUIRED")
                print(f"  ✅ Core tables: {len(existing_core)}/{len(core_tables)}")
                print(f"  ⚠️  Philippines tables: {len(existing_philippines)}/{len(philippines_tables)}")
        else:
            state = 'partial'
            print(f"  📊 Status: PARTIAL/BROKEN INSTALLATION")
            print(f"  ⚠️  Core tables: {len(existing_core)}/{len(core_tables)}")
            print(f"  ⚠️  Philippines tables: {len(existing_philippines)}/{len(philippines_tables)}")
        
        self.db_state = state
        return state
    
    def run_fresh_install(self):
        """Run complete fresh installation"""
        print("\n" + "=" * 80)
        print("  🆕 FRESH INSTALLATION MODE")
        print("=" * 80)
        
        steps = [
            ("Applying ALL database migrations", lambda: call_command('migrate', verbosity=1)),
            ("Populating Philippines payroll data", lambda: call_command('populate_ph_payroll')),
            ("Marking USA deductions", lambda: self.mark_usa_deductions()),
        ]
        
        for i, (desc, func) in enumerate(steps, 1):
            print(f"\n[{i}/{len(steps)}] {desc}...")
            print("-" * 80)
            try:
                func()
                print(f"  ✅ Success!")
            except Exception as e:
                print(f"  ⚠️  Warning: {str(e)}")
                if not self.auto_mode:
                    response = input("  Continue anyway? (y/n): ")
                    if response.lower() != 'y':
                        print("\n❌ Setup aborted by user")
                        sys.exit(1)
    
    def run_update(self):
        """Run update for existing installation"""
        print("\n" + "=" * 80)
        print("  🔄 UPDATE MODE - Adding Philippines Features")
        print("=" * 80)
        
        steps = [
            ("Applying new migrations only", lambda: call_command('migrate', verbosity=1)),
            ("Populating Philippines payroll data", lambda: call_command('populate_ph_payroll')),
        ]
        
        for i, (desc, func) in enumerate(steps, 1):
            print(f"\n[{i}/{len(steps)}] {desc}...")
            print("-" * 80)
            try:
                func()
                print(f"  ✅ Success!")
            except Exception as e:
                print(f"  ⚠️  Warning: {str(e)}")
    
    def repair_and_continue(self):
        """Repair broken migration state and continue"""
        print("\n" + "=" * 80)
        print("  🔧 REPAIR MODE - Fixing Migration State")
        print("=" * 80)
        
        print("\n[1/2] Faking existing migrations...")
        print("-" * 80)
        try:
            # Mark base migrations as applied
            call_command('migrate', 'payroll', '--fake-initial', verbosity=1)
            print("  ✅ Base migrations marked as applied")
        except Exception as e:
            print(f"  ⚠️  Warning: {str(e)}")
        
        print("\n[2/2] Applying new migrations...")
        print("-" * 80)
        try:
            call_command('migrate', verbosity=1)
            print("  ✅ New migrations applied")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            print("\n  Manual intervention may be required.")
            print("  Please contact support with the error message above.")
            sys.exit(1)
        
        # Run Philippines setup
        print("\n[3/3] Populating Philippines data...")
        print("-" * 80)
        try:
            call_command('populate_ph_payroll')
            print("  ✅ Philippines data populated")
        except Exception as e:
            print(f"  ⚠️  Warning: {str(e)}")
    
    def mark_usa_deductions(self):
        """Mark existing deductions as USA country"""
        try:
            from payroll.models.models import Deduction
            from payroll.models.country_models import PayrollCountryConfig
            
            # Only mark if USA config exists
            if PayrollCountryConfig.objects.filter(country='USA').exists():
                usa_deductions = Deduction.objects.filter(country__isnull=True)
                count = usa_deductions.update(country='USA')
                if count > 0:
                    print(f"  ✅ Marked {count} deductions as USA-specific")
        except Exception as e:
            print(f"  ⚠️  Could not mark deductions: {str(e)}")
    
    def run_setup(self):
        """Main setup orchestration"""
        self.print_banner()
        
        # Detect state
        state = self.detect_database_state()
        
        # Decide action
        if self.fresh_install:
            action = 'fresh'
        elif self.philippines_only:
            action = 'philippines'
        elif state == 'fresh':
            action = 'fresh'
        elif state == 'complete':
            print("\n  ℹ️  Installation is already complete!")
            if not self.auto_mode:
                response = input("\n  Re-run Philippines setup anyway? (y/n): ")
                if response.lower() == 'y':
                    action = 'philippines'
                else:
                    print("\n  ✅ Nothing to do. Exiting.")
                    return
            else:
                print("  ✅ Nothing to do. Exiting.")
                return
        elif state == 'update':
            action = 'update'
        else:  # partial
            action = 'repair'
        
        # Execute action
        print("\n" + "=" * 80)
        print(f"  🎯 Selected Action: {action.upper()}")
        print("=" * 80)
        
        if not self.auto_mode and action != 'fresh':
            response = input("\n  Proceed? (y/n): ")
            if response.lower() != 'y':
                print("\n  ❌ Setup cancelled by user")
                return
        
        # Run appropriate setup
        if action == 'fresh':
            self.run_fresh_install()
        elif action == 'update':
            self.run_update()
        elif action == 'repair':
            self.repair_and_continue()
        elif action == 'philippines':
            print("\n[1/1] Populating Philippines payroll data...")
            print("-" * 80)
            call_command('populate_ph_payroll')
            print("  ✅ Success!")
        
        # Success message
        self.print_success()
    
    def print_success(self):
        """Print success message"""
        print("\n" + "=" * 80)
        print("  ✅ SETUP COMPLETE!")
        print("=" * 80)
        print("\n  Next steps:")
        print("  1. Create admin user: python manage.py createsuperuser")
        print("  2. Start server:      python manage.py runserver")
        print("  3. Visit:             http://127.0.0.1:8000")
        print("\n  📚 Documentation: See README.md for more details")
        print("\n" + "=" * 80 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Horilla HRMS Universal Setup Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup.py                    # Interactive mode (recommended)
  python setup.py --auto             # Auto-detect and run
  python setup.py --fresh            # Force fresh install
  python setup.py --philippines-only # Only setup Philippines data
        """
    )
    
    parser.add_argument('--auto', action='store_true',
                       help='Auto-detect and run without prompts')
    parser.add_argument('--fresh', action='store_true',
                       help='Force fresh installation (ignore existing data)')
    parser.add_argument('--philippines-only', action='store_true',
                       help='Only populate Philippines payroll data')
    
    args = parser.parse_args()
    
    # Run setup
    setup = HorillaSetup(
        auto_mode=args.auto,
        fresh_install=args.fresh,
        philippines_only=args.philippines_only
    )
    
    try:
        setup.run_setup()
    except KeyboardInterrupt:
        print("\n\n  ⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n  ❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
