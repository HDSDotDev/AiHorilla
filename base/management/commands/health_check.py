"""
Health check management command for Railway deployment monitoring
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError
import sys


class Command(BaseCommand):
    help = 'Performs health check of the application'

    def add_arguments(self, parser):
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output result as JSON',
        )

    def handle(self, *args, **options):
        checks = {
            'database': self.check_database(),
            'migrations': self.check_migrations(),
        }
        
        all_passed = all(checks.values())
        
        if options['json']:
            import json
            result = {
                'status': 'healthy' if all_passed else 'unhealthy',
                'checks': checks
            }
            self.stdout.write(json.dumps(result))
        else:
            if all_passed:
                self.stdout.write(self.style.SUCCESS('✓ Health check passed'))
            else:
                self.stdout.write(self.style.ERROR('✗ Health check failed'))
                for check, status in checks.items():
                    icon = '✓' if status else '✗'
                    self.stdout.write(f'  {icon} {check}')
        
        sys.exit(0 if all_passed else 1)

    def check_database(self):
        """Check if database connection is working"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except OperationalError:
            return False

    def check_migrations(self):
        """Check if all migrations are applied"""
        try:
            from django.db.migrations.executor import MigrationExecutor
            executor = MigrationExecutor(connection)
            targets = executor.loader.graph.leaf_nodes()
            plan = executor.migration_plan(targets)
            return len(plan) == 0
        except Exception:
            return False
