from ast import arg
from datetime import datetime
from core.agents.chatbot_agent import ChatbotState
from core.agents.email_agent import EmailAgent
from langchain_core.runnables import RunnableConfig


from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.job import Job


def fetch_email_data(user_id: str, thread_id: str, config: RunnableConfig):
    print(f"[{datetime.now()}] Running email agent job...")
    result = EmailAgent.invoke(
        input={"thread_id": thread_id, "user_id": user_id}, config=config
    )
    print(result)

    # return result


scheduler = BackgroundScheduler()


def start_email_scheduler_job(user_id: str, thread_id: str, interval: int) -> Job:
    config = RunnableConfig(configurable={"thread_id": thread_id})
    job = scheduler.add_job(
        fetch_email_data,
        args=(user_id, thread_id, config),
        trigger="interval",
        seconds=interval,
        id=f"email-fetch-job-{user_id}-{thread_id}",
    )
    scheduler.start()
    return job


def delete_email_scheduler_job(user_id: str, thread_id: str):
    try:
        scheduler.remove_job(job_id=f"email-fetch-job-{user_id}-{thread_id}")
        return {"status": "success"}
    except Exception as e:
        e = f"Exception occured : {e}"
        print(e)
        return {"status": e}
