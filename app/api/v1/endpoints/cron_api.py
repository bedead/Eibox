"""
API endpoints for managing Gmail cron jobs.
This module provides endpoints to start and delete scheduled Gmail email jobs,
as well as a test endpoint for health checks. It interacts with Gmail accounts,
session management, and job scheduling services.
Endpoints:
- POST /gmail/start/: Start a Gmail cron job for a user.
- POST /gmail/delete/: Delete a Gmail cron job for a user.
Author: Satyam Mishra
Date: 14-09-2025
"""

from typing import List

from fastapi import APIRouter

from app.db import GmailAccount, CronJobSchema
from app.utils import job_to_dict
from app.services import (
    start_email_scheduler_job,
    delete_email_scheduler_job,
    GmailToolKit,
    delete_session,
    store_session,
    get_gmail_account,
)

router = APIRouter()
namespace_for_memory = ("auth", "user")


@router.post("/gmail/start/")
def start_gmail_cron(input: CronJobSchema):
    # get gmail_account data create gmail_toolkit
    print("Input received for starting gmail cron job:", input)

    data: List[GmailAccount] = get_gmail_account(
        username=input.username, namespace_for_memory=namespace_for_memory
    )
    gmail_toolkit = GmailToolKit(gmail_account=data[0])

    job = start_email_scheduler_job(
        username=input.username,
        thread_id=input.thread_id,
        interval=input.preferences.get("interval_seconds"),
    )

    # TODO: add cron job to session

    return job_to_dict(job)
    # return job


@router.post("/gmail/delete/")
def delete_gmail_cron(input: CronJobSchema):
    # TODO: remove cron job from session
    return delete_email_scheduler_job(
        username=input.username, thread_id=input.thread_id
    )


@router.post("/gmail/modify/")
def modify_gmail_cron(input: CronJobSchema):

    pass  # TODO: implement modify gmail cron job functionality
