import os

from app.services.cron_jobs.jobs import delete_email_scheduler_job, start_email_scheduler_job
from app.services.session.session_utils import init_or_get_session
from app.core.config import settings


session = init_or_get_session(
    username="satyam", thread_id="test", namespace_for_memory=("auth", "user")
)
job = start_email_scheduler_job(username="satyam", thread_id="test", interval=60)
# job = delete_email_scheduler_job(username="satyam", thread_id="test")
