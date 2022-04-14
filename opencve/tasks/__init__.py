from datetime import timedelta

from celery import chain

from opencve.extensions import cel
from opencve.tasks.alerts import handle_alerts
from opencve.tasks.events import handle_events
from opencve.tasks.reports import handle_reports

# Celery Beat configuration
CELERYBEAT_SCHEDULE = {}

# Periodic CVE check
# Provisional and set only for testing purpose, needs to be set to a better value in a production environment (15 minutes or more for example)
CELERYBEAT_SCHEDULE["cve-updates-15-mn"] = {
    "task": "CVE_UPDATES",
    "schedule": timedelta(minutes=15),
}


@cel.task(bind=True, name="CVE_UPDATES")
def cve_updates(self):
    return chain(handle_events.si(), handle_alerts.si(), handle_reports.si())()
