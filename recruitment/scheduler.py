import calendar
import datetime as dt
import os
import sys
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from dateutil.relativedelta import relativedelta

today = datetime.now()


def recruitment_close():
    """
    Closes recruitment campaigns that have reached their end date.

    """
    from django.db.utils import OperationalError, ProgrammingError
    from recruitment.models import Recruitment

    today_date = today.date()

    try:
        recruitments = Recruitment.objects.filter(closed=False)
    except (OperationalError, ProgrammingError) as e:
        print(f"recruitment_close: Database not ready - {e}")
        return

    for rec in recruitments:
        if rec.end_date:
            if rec.end_date == today_date:
                rec.closed = True
                rec.is_published = False
                rec.save()


def candidate_convert():
    """
    Converts candidates to a "converted" state if they already exist as users.
    """
    from django.db.utils import OperationalError, ProgrammingError
    from django.contrib.auth.models import User

    from recruitment.models import Candidate

    try:
        candidates = Candidate.objects.filter(is_active=True)
    except (OperationalError, ProgrammingError) as e:
        print(f"candidate_convert: Database not ready - {e}")
        return
    mails = list(Candidate.objects.values_list("email", flat=True))
    existing_emails = list(
        User.objects.filter(username__in=mails).values_list("email", flat=True)
    )
    for cand in candidates:
        if cand.email in existing_emails:
            cand.converted = True
            cand.save()


if not any(
    cmd in sys.argv
    for cmd in ["makemigrations", "migrate", "compilemessages", "flush", "shell"]
) and not os.getenv("SKIP_SCHEDULERS"):
    """
    Initializes and starts background tasks using APScheduler when the server is running.
    """
    try:
        scheduler = BackgroundScheduler()
        scheduler.add_job(candidate_convert, "interval", minutes=5)
        scheduler.add_job(recruitment_close, "interval", hours=1)
        scheduler.start()
    except Exception as e:
        print(f"⚠️  Failed to start recruitment scheduler: {e}")
