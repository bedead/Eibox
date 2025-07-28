from fastapi import APIRouter
from api._helper import job_to_dict
from api.schema.CronJobSchema import CronJobSchema
from core.job_scheduler.jobs import (
    start_email_scheduler_job,
    delete_email_scheduler_job,
)

router = APIRouter()


@router.post("/gmail/start/v1")
def start_gmail_cron(input: CronJobSchema):
    job = start_email_scheduler_job(
        user_id=input.user_id, thread_id=input.thread_id, interval=30
    )
    return job_to_dict(job)
    # return job


@router.post("/gmail/delete/v1")
def delete_gmail_cron(input: CronJobSchema):
    return delete_email_scheduler_job(user_id=input.user_id, thread_id=input.thread_id)


@router.get("/")
def test():
    return {"success": 200}
