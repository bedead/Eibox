from datetime import datetime
from app.services.agents.email_agent import EmailAgent, EmailState
from langchain_core.runnables import RunnableConfig
from app.core.logging import logger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.job import Job


def fetch_email_data(username: str, thread_id: str, config: RunnableConfig):
    logger.info(f"[{datetime.now()}] Running email agent job...")
    config["configurable"]["username"] = username
    config["configurable"]["thread_id"] = thread_id
    result = EmailAgent.invoke(input=EmailState(), config=config)
    logger.info(result)

    # return result


scheduler = BackgroundScheduler()


def start_email_scheduler_job(username: str, thread_id: str, interval: int) -> Job:
    config = RunnableConfig(configurable={"thread_id": thread_id})
    job = scheduler.add_job(
        fetch_email_data,
        args=(username, thread_id, config),
        trigger="interval",
        seconds=interval,
        id=f"email-fetch-job-{username}-{thread_id}",
    )
    scheduler.start()
    return job


def delete_email_scheduler_job(username: str, thread_id: str):
    try:
        scheduler.remove_job(job_id=f"email-fetch-job-{username}-{thread_id}")
        return {"status": "success"}
    except Exception as e:
        e = f"Exception occured : {e}"
        logger.error(e, exc_info=True)
        return {"status": e}
