from django.apps import AppConfig


class GeofencingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "geofencing"

    def ready(self):
        import os
        from django.urls import include, path

        from horilla.urls import urlpatterns

        urlpatterns.append(
            path("api/geofencing/", include("geofencing.urls")),
        )
        
        # Skip any DB operations during initial deployment
        if os.environ.get('SKIP_DB_INIT_IN_READY'):
            return
            
        super().ready()
