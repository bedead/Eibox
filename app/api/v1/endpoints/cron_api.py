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

from app.db import GmailAccount, CronJobSchema, CronJobDelete_CheckSchema
from app.utils import job_to_dict
from app.services import (
    start_email_scheduler_job,
    modify_email_scheduler_job,
    delete_email_scheduler_job,
    GmailToolKit,
    delete_session,
    store_session,
    get_gmail_account,
    check_job_exists_by_details,
)

router = APIRouter()
namespace_for_memory = ("auth", "user")


@router.post("/gmail/start")
def start_gmail_cron(input: CronJobSchema):
    # get gmail_account data create gmail_toolkit
    print("Input received for starting gmail cron job:", input)

    # data: List[GmailAccount] = get_gmail_account(
    #     username=input.username, namespace_for_memory=namespace_for_memory
    # )
    # print("Gmail account data retrieved:", data)
    # gmail_toolkit = GmailToolKit(gmail_account=data[0])

    if check_job_exists_by_details(username=input.username, thread_id=input.thread_id):
        resp = {"status": "job already exists"}
        print("Job already exists for user:", input.username)
        return resp

    job = start_email_scheduler_job(
        username=input.username,
        thread_id=input.thread_id,
        interval=input.preferences.get("interval_seconds"),
    )

    # if job already exists, update job configuration if new preferences are provided

    # TODO: add cron job to session

    return job_to_dict(job)
    # return job


@router.post("/gmail/delete")
def delete_gmail_cron(input: CronJobDelete_CheckSchema):
    # TODO: remove cron job from session
    return delete_email_scheduler_job(
        username=input.username, thread_id=input.thread_id
    )


@router.post("/gmail/modify")
def modify_gmail_cron(input: CronJobSchema):
    new_job = modify_email_scheduler_job(
        username=input.username,
        thread_id=input.thread_id,
        interval=input.preferences.get("interval_seconds"),
    )

    return job_to_dict(new_job)


@router.post("/gmail/check_status")
def check_gmail_cron_status(input: CronJobDelete_CheckSchema):
    # TODO: add more details about job.
    if check_job_exists_by_details(username=input.username, thread_id=input.thread_id):
        return {"status": "Email cron job running."}
    else:
        return {"status": "Email cron job not running."}
