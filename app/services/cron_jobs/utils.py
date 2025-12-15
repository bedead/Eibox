from app.core import scheduler


def check_job_exists_by_details(username: str, thread_id: str) -> bool:
    """Check if a job with the given ID exists in the scheduler."""
    job_id = f"email-fetch-job-{username}-{thread_id}"
    job = scheduler.get_job(job_id)
    return job is not None
