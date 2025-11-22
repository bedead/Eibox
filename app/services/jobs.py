import asyncio
from datetime import datetime
from typing import Optional

from langchain_core.runnables import RunnableConfig
from apscheduler.job import Job

from app.services import EmailAgent, EmailState
from app.core import logger
from app.core import scheduler


async def fetch_email_data(username: str, thread_id: str, config: RunnableConfig):
    logger.debug(f"[{datetime.now()}] Running email agent job...")
    if "configurable" not in config:
        config["configurable"] = {}
    config["configurable"]["username"] = username
    config["configurable"]["thread_id"] = thread_id
    result = await EmailAgent.ainvoke(input=EmailState(), config=config)
    return result


def schedule_fetch_email_data(username: str, thread_id: str, config: RunnableConfig):
    """Wrapper to run async fetch in the right event loop."""
    try:
        loop = asyncio.get_running_loop()
        # If we’re already inside FastAPI’s event loop, just create a task
        loop.create_task(fetch_email_data(username, thread_id, config))
    except RuntimeError:
        # No running loop (standalone mode, or APScheduler thread) → run new loop
        asyncio.run(fetch_email_data(username, thread_id, config))


def start_email_scheduler_job(
    username: str, thread_id: str, interval: Optional[int] = 30
) -> Job:
    config = RunnableConfig(configurable={"thread_id": thread_id})
    job = scheduler.add_job(
        schedule_fetch_email_data,
        args=(username, thread_id, config),
        trigger="interval",
        seconds=interval, # in secondds
        coalesce=True,  # skip backlog, run latest if jobs pile up
        max_instances=1,  # prevent overlapping runs
        misfire_grace_time=30,  # if late by <30s, run
        id=f"email-fetch-job-{username}-{thread_id}",
    )
    return job


def delete_email_scheduler_job(username: str, thread_id: str):
    try:
        scheduler.remove_job(job_id=f"email-fetch-job-{username}-{thread_id}")
        return {"status": "success"}
    except Exception as e:
        e = f"Exception occured : {e}"
        logger.error(e, exc_info=True)
        return {"status": e}
