"""
Railway-specific database initialization command.
Handles first-time setup for Railway deployments.
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
import sys
import os

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)


class Command(BaseCommand):
    help = 'Initialize database for Railway deployment (first-time setup)'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("Railway Database Initialization")
        self.stdout.write("=" * 80)
        self.stdout.flush()
        
        # Check database connection
        self.stdout.write("\n[0/4] Testing database connection...")
        self.stdout.flush()
        
        try:
            self.stdout.write("  Attempting database query...")
            self.stdout.flush()
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            db_engine = connection.settings_dict['ENGINE']
            db_name = connection.settings_dict.get('NAME', 'unknown')
            
            self.stdout.write(f"✓ Database connected successfully!")
            self.stdout.write(f"  Engine: {db_engine}")
            self.stdout.write(f"  Database: {db_name}")
            self.stdout.flush()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Database connection failed!"))
            self.stdout.write(self.style.ERROR(f"  Error: {e}"))
            self.stdout.write(self.style.ERROR(f"  Type: {type(e).__name__}"))
            self.stdout.flush()
            sys.exit(1)
        
        # Run migrations in correct order to avoid dependency issues
        self.stdout.write("\n[1/4] Running database migrations...")
        self.stdout.flush()
        
        # Migrate apps in dependency order
        migration_order = [
            'contenttypes',
            'auth',
            'admin',
            'sessions',
            'base',
            'employee',      # Must come before payroll
            'leave',
            'asset',
            'attendance',
            'payroll',       # Depends on employee
            'pms',
            'recruitment',
            'onboarding',
        ]
        
        try:
            for app in migration_order:
                self.stdout.write(f"  Migrating {app}...")
                self.stdout.flush()
                
                try:
                    call_command('migrate', app, '--noinput', verbosity=0)
                    self.stdout.write(self.style.SUCCESS(f"    ✓ {app}"))
                    self.stdout.flush()
                except Exception as app_error:
                    self.stdout.write(self.style.WARNING(f"    ⚠ {app}: {app_error}"))
                    self.stdout.flush()
            
            # Migrate any remaining apps
            self.stdout.write("  Migrating remaining apps...")
            self.stdout.flush()
            
            call_command('migrate', '--noinput', verbosity=0)
            self.stdout.write(self.style.SUCCESS("✓ All migrations completed"))
            self.stdout.flush()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Migration failed: {e}"))
            self.stdout.flush()
            
            # Try with syncdb as fallback
            self.stdout.write("Trying with --run-syncdb...")
            self.stdout.flush()
            
            try:
                call_command('migrate', '--run-syncdb', '--noinput', verbosity=1)
                self.stdout.write(self.style.SUCCESS("✓ Migrations completed with syncdb"))
                self.stdout.flush()
            except Exception as e2:
                self.stdout.write(self.style.ERROR(f"✗ Syncdb also failed: {e2}"))
                self.stdout.flush()
                sys.exit(1)
        
        # Create admin user
        self.stdout.write("\n[2/4] Creating admin user...")
        self.stdout.flush()
        
        try:
            call_command(
                'createhorillauser',
                '--first_name', 'admin',
                '--last_name', 'admin',
                '--username', 'admin',
                '--password', 'admin',
                '--email', 'admin@example.com',
                '--phone', '1234567890'
            )
            self.stdout.write(self.style.SUCCESS("✓ Admin user created"))
            self.stdout.flush()
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"ℹ Admin user: {e}"))
            self.stdout.flush()
        
        # Initialize Philippines payroll data (if available)
        self.stdout.write("\n[3/4] Setting up Philippines payroll data...")
        self.stdout.flush()
        
        try:
            # Check if Philippines setup command exists
            from django.core.management import get_commands
            commands = get_commands()
            if 'setup_philippines_payroll' in commands:
                call_command('setup_philippines_payroll', verbosity=1)
                self.stdout.write(self.style.SUCCESS("✓ Philippines payroll data loaded"))
            else:
                self.stdout.write(self.style.WARNING("ℹ Philippines setup command not found, skipping"))
            self.stdout.flush()
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"ℹ Philippines setup: {e}"))
            self.stdout.flush()
        
        # Collect static files
        self.stdout.write("\n[4/4] Collecting static files...")
        self.stdout.flush()
        
        try:
            call_command('collectstatic', '--noinput', '--clear', verbosity=0)
            self.stdout.write(self.style.SUCCESS("✓ Static files collected"))
            self.stdout.flush()
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"ℹ Static files: {e}"))
            self.stdout.flush()
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("✓✓✓ Railway initialization complete!"))
        self.stdout.write("=" * 80)
        self.stdout.write("\nDefault credentials:")
        self.stdout.write("  Username: admin")
        self.stdout.write("  Password: admin")
        self.stdout.write("  ⚠️  CHANGE PASSWORD IMMEDIATELY AFTER FIRST LOGIN!\n")
        self.stdout.flush()
