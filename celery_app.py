"""
BOLAYETU — Celery Application
Skill: BOLAYETU_DOCKER_DEVOPS_SKILL

Tasks:
- Notifications (email, push)
- PDF generation and reports
- Media processing (image resize, video thumbnails)
- Scheduled jobs (rankings recalculation, stats aggregation)
"""

import os
from celery import Celery

# Settings module defaults to development
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('bolayetu')

# Use Django settings for Celery configuration
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Health check task for Celery worker."""
    print(f'Request: {self.request!r}')
