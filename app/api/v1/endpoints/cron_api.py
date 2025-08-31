from typing import List
from fastapi import APIRouter
from app.db.repos.gmail.get_gmail_accounts import get_gmail_account
from app.schemas.gmail_account import GmailAccount
from app.services.gmail.gmail_toolkit import GmailToolKit
from app.services.session.get_session import get_session
from app.services.session.delete_session import delete_session
from app.services.session.store_session import store_session
from app.utils._api_helper import _job_to_dict
from app.schemas.cron_job import CronJobSchema
from app.services.job_scheduler.jobs import (
    start_email_scheduler_job,
    delete_email_scheduler_job,
)

router = APIRouter()
namespace_for_memory = ("auth", "user")


@router.post("/gmail/start/")
def start_gmail_cron(input: CronJobSchema):
    # get gmail_account data create gmail_toolkit
    data: List[GmailAccount] = get_gmail_account(
        username=input.username, namespace_for_memory=namespace_for_memory
    )
    gmail_toolkit = GmailToolKit(gmail_account=data[0])

    # store session
    store_session(
        username=input.username,
        thread_id=input.thread_id,
        gmail_toolkit=gmail_toolkit,
    )
    job = start_email_scheduler_job(
        username=input.username,
        thread_id=input.thread_id,
        interval=30,
    )
    return _job_to_dict(job)
    # return job


@router.post("/gmail/delete/")
def delete_gmail_cron(input: CronJobSchema):
    # delete session
    delete_session(username=input.username, thread_id=input.thread_id)

    return delete_email_scheduler_job(
        username=input.username, thread_id=input.thread_id
    )


@router.get("/")
def test():
    return {"success": 200}
