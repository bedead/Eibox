from fastapi import FastAPI, APIRouter
from api._helper import job_to_dict
from pydantic import BaseModel
from core.job_scheduler.jobs import (
    start_email_scheduler_job,
    delete_email_scheduler_job,
)

router = APIRouter()


class Job(BaseModel):
    user_id: str
    thread_id: str


@router.post("/gmail/start/v1")
def chat(input: Job):
    job = start_email_scheduler_job(user_id=input.user_id, thread_id=input.thread_id)
    return job_to_dict(job)
    # return job


@router.post("/gmail/delete/v1")
def chat(input: Job):
    return delete_email_scheduler_job(user_id=input.user_id, thread_id=input.thread_id)


@router.get("/")
def test():
    return {"success": 200}
