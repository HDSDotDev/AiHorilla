"""
Railway-specific database initialization command.
Handles first-time setup for Railway deployments.
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
import sys


class Command(BaseCommand):
    help = 'Initialize database for Railway deployment (first-time setup)'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("Railway Database Initialization")
        self.stdout.write("=" * 80)
        
        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            db_engine = connection.settings_dict['ENGINE']
            self.stdout.write(f"✓ Database connected: {db_engine}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Database connection failed: {e}"))
            sys.exit(1)
        
        # Run migrations in correct order to avoid dependency issues
        self.stdout.write("\n[1/4] Running database migrations...")
        
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
                try:
                    call_command('migrate', app, '--noinput', verbosity=0)
                    self.stdout.write(self.style.SUCCESS(f"    ✓ {app}"))
                except Exception as app_error:
                    self.stdout.write(self.style.WARNING(f"    ⚠ {app}: {app_error}"))
            
            # Migrate any remaining apps
            self.stdout.write("  Migrating remaining apps...")
            call_command('migrate', '--noinput', verbosity=0)
            self.stdout.write(self.style.SUCCESS("✓ All migrations completed"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Migration failed: {e}"))
            # Try with syncdb as fallback
            self.stdout.write("Trying with --run-syncdb...")
            try:
                call_command('migrate', '--run-syncdb', '--noinput', verbosity=1)
                self.stdout.write(self.style.SUCCESS("✓ Migrations completed with syncdb"))
            except Exception as e2:
                self.stdout.write(self.style.ERROR(f"✗ Syncdb also failed: {e2}"))
                sys.exit(1)
        
        # Create admin user
        self.stdout.write("\n[2/4] Creating admin user...")
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
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"ℹ Admin user: {e}"))
        
        # Initialize Philippines payroll data (if available)
        self.stdout.write("\n[3/4] Setting up Philippines payroll data...")
        try:
            # Check if Philippines setup command exists
            from django.core.management import get_commands
            commands = get_commands()
            if 'setup_philippines_payroll' in commands:
                call_command('setup_philippines_payroll', verbosity=1)
                self.stdout.write(self.style.SUCCESS("✓ Philippines payroll data loaded"))
            else:
                self.stdout.write(self.style.WARNING("ℹ Philippines setup command not found, skipping"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"ℹ Philippines setup: {e}"))
        
        # Collect static files
        self.stdout.write("\n[4/4] Collecting static files...")
        try:
            call_command('collectstatic', '--noinput', '--clear', verbosity=1)
            self.stdout.write(self.style.SUCCESS("✓ Static files collected"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"ℹ Static files: {e}"))
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("✓✓✓ Railway initialization complete!"))
        self.stdout.write("=" * 80)
        self.stdout.write("\nDefault credentials:")
        self.stdout.write("  Username: admin")
        self.stdout.write("  Password: admin")
        self.stdout.write("  ⚠️  CHANGE PASSWORD IMMEDIATELY AFTER FIRST LOGIN!\n")
