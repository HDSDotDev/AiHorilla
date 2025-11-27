"""
This module contains the configuration for the 'base' app.
"""

from django.apps import AppConfig


class BaseConfig(AppConfig):
    """
    Configuration class for the 'base' app.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "base"

    def ready(self) -> None:
        from base import signals

        super().ready()
        
        # Skip database operations during initial setup
        import os
        if os.environ.get('SKIP_DB_INIT_IN_READY'):
            return
            
        try:
            from base.models import EmployeeShiftDay
            from django.db import connection
            from django.db.utils import OperationalError, ProgrammingError
            
            # Check if table exists before querying
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'base_employeeshiftday')"
                )
                table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                return  # Skip if table doesn't exist yet (migrations haven't run)

            if not EmployeeShiftDay.objects.exists():
                days = [
                    ("monday", "Monday"),
                    ("tuesday", "Tuesday"),
                    ("wednesday", "Wednesday"),
                    ("thursday", "Thursday"),
                    ("friday", "Friday"),
                    ("saturday", "Saturday"),
                    ("sunday", "Sunday"),
                ]

                EmployeeShiftDay.objects.bulk_create(
                    [EmployeeShiftDay(day=day[0]) for day in days]
                )
        except (OperationalError, ProgrammingError):
            # Database/table doesn't exist yet - skip initialization
            pass
        except Exception as e:
            pass
