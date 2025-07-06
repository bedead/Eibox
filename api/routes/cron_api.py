from fastapi import FastAPI, APIRouter
from api.helper._helper import job_to_dict
from core import EmailAgent, EmailState
from pydantic import BaseModel
from core.job_scheduler.jobs import (
    start_email_scheduler_job,
    delete_email_scheduler_job,
)

router = APIRouter()


class Job(BaseModel):
    thread_id: str


@router.post("/gmail/start/v1")
def chat(input: Job):
    job = start_email_scheduler_job(thread_id=input.thread_id)
    return job_to_dict(job)
    # return job


@router.get("/gmail/delete/v1")
def chat(input: Job):
    delete_email_scheduler_job(thread_id=input.thread_id)
    return {"success": 200}


@router.get("/")
def test():
    return {"success": 200}
