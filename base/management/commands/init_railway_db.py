"""
Management command to safely initialize database for Railway deployment
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = 'Initializes the database safely for Railway deployment'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Database Initialization Started ==='))
        
        # Test database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write(self.style.SUCCESS('✓ Database connection successful'))
        except OperationalError as e:
            self.stdout.write(self.style.ERROR(f'✗ Database connection failed: {e}'))
            return

        # Run migrations in order
        apps_order = [
            'contenttypes',
            'auth',
            'admin',
            'sessions',
            'base',
            'employee',
            'leave',
            'asset',
            'attendance',
            'payroll',
        ]

        for app in apps_order:
            try:
                self.stdout.write(f'Migrating {app}...')
                call_command('migrate', app, '--noinput', verbosity=0)
                self.stdout.write(self.style.SUCCESS(f'✓ {app} migrated successfully'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠ {app} migration skipped: {e}'))

        # Run any remaining migrations
        try:
            self.stdout.write('Running remaining migrations...')
            call_command('migrate', '--noinput', verbosity=0)
            self.stdout.write(self.style.SUCCESS('✓ All migrations completed'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠ Some migrations failed: {e}'))
            self.stdout.write('Trying with --fake-initial...')
            try:
                call_command('migrate', '--fake-initial', '--noinput', verbosity=0)
                self.stdout.write(self.style.SUCCESS('✓ Migrations completed with --fake-initial'))
            except Exception as e2:
                self.stdout.write(self.style.ERROR(f'✗ Migration failed: {e2}'))

        self.stdout.write(self.style.SUCCESS('=== Database Initialization Complete ==='))
