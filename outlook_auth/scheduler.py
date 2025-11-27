"""
outlook_auth/scheduler.py

"""

import logging
import os
import sys

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)


def refresh_outlook_auth_token():
    """
    scheduler method to refresh token
    """
    from django.db.utils import OperationalError, ProgrammingError
    from outlook_auth.models import AzureApi
    from outlook_auth.views import refresh_outlook_token

    try:
        apis = AzureApi.objects.filter(token__isnull=False)
    except (OperationalError, ProgrammingError) as e:
        print(f"refresh_outlook_auth_token: Database not ready - {e}")
        return
    for api in apis:
        try:
            refresh_outlook_token(api)
            logger.info(f"Updated token for {api} outlook auth")
            print(f"Updated token for {api} outlook auth")
        except Exception as e:
            logger.error(e)


if not any(
    cmd in sys.argv
    for cmd in ["makemigrations", "migrate", "compilemessages", "flush", "shell"]
) and not os.getenv("SKIP_SCHEDULERS"):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        refresh_outlook_auth_token,
        "interval",
        minutes=50,
        id="refresh_outlook_auth_token",
    )
    scheduler.start()
