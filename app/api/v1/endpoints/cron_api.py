from fastapi import APIRouter
from app.utils._api_helper import _job_to_dict
from app.schemas.cron_job import CronJobSchema
from app.services.job_scheduler.jobs import (
    start_email_scheduler_job,
    delete_email_scheduler_job,
)

router = APIRouter()


@router.post("/gmail/start/v1")
def start_gmail_cron(input: CronJobSchema):
    job = start_email_scheduler_job(
        user_id=input.user_id,
        username=input.username,
        thread_id=input.thread_id,
        interval=30,
    )
    return _job_to_dict(job)
    # return job


@router.post("/gmail/delete/v1")
def delete_gmail_cron(input: CronJobSchema):
    return delete_email_scheduler_job(
        user_id=input.user_id, username=input.username, thread_id=input.thread_id
    )


@router.get("/")
def test():
    return {"success": 200}
