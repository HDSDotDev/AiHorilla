"""
App configuration for the Horilla Automations app.
Initializes model choices and starts automation when the server runs.
"""

import os
import sys

from django.apps import AppConfig


class HorillaAutomationConfig(AppConfig):
    """Configuration class for the Horilla Automations Django app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "horilla_automations"

    def ready(self):
        """Run initialization tasks when the app is ready."""
        from base.templatetags.horillafilters import app_installed
        from employee.models import Employee
        from horilla_automations.methods.methods import get_related_models
        from horilla_automations.models import MODEL_CHOICES as model_choices

        # Build MODEL_CHOICES
        models = [Employee]
        if app_installed("recruitment"):
            from recruitment.models import Candidate

            models.append(Candidate)

        for main_model in models:
            for model in get_related_models(main_model):
                model_choices.append(
                    (f"{model.__module__}.{model.__name__}", model.__name__)
                )

        model_choices.append(("employee.models.Employee", "Employee"))
        model_choices.append(("pms.models.EmployeeKeyResult", "Employee Key Results"))
        model_choices[:] = list(set(model_choices))  # Update in-place

        # Skip automation during initial setup
        if os.environ.get('SKIP_DB_INIT_IN_READY'):
            return
        
        # Only start automation when running the server
        if not any(
            cmd in sys.argv
            for cmd in [
                "makemigrations",
                "migrate",
                "compilemessages",
                "flush",
                "shell",
            ]
        ):
            from horilla_automations.signals import start_automation
            from django.db import connection
            from django.db.utils import OperationalError, ProgrammingError

            # Check if tables exist before starting automation (PostgreSQL compatible)
            try:
                with connection.cursor() as cursor:
                    # PostgreSQL-compatible query (works with both SQLite and PostgreSQL)
                    cursor.execute(
                        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'horilla_automations_mailautomation')"
                    )
                    table_exists = cursor.fetchone()[0]
                    if table_exists:
                        start_automation()
                    else:
                        print("⚠️  Skipping automation startup: tables not yet created")
            except (OperationalError, ProgrammingError) as e:
                print(f"⚠️  Skipping automation startup: {e}")
