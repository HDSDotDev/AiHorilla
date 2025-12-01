"""
Django application configuration for the PMS (Performance Management System) app.
"""

from django.apps import AppConfig


class PmsConfig(AppConfig):
    """
    This class provides configuration settings for the PMS app, such as the default
    database field type and the app's name.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "pms"

    def ready(self):
        import os
        from django.urls import include, path

        from horilla.horilla_settings import APPS
        from horilla.urls import urlpatterns

        APPS.append("pms")
        urlpatterns.append(
            path("pms/", include("pms.urls")),
        )
        super().ready()
        
        # Skip automation and scheduler during initial deployment
        if os.environ.get('SKIP_SCHEDULERS') or os.environ.get('SKIP_DB_INIT_IN_READY'):
            return
            
        try:
            from pms.signals import start_automation

            start_automation()
        except:
            """
            Migrations are not affected yet
            """
