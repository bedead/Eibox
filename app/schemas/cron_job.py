from pydantic import BaseModel, Field


class CronJobSchema(BaseModel):
    id: str = Field(description="The unique identifier for the cron job")
    job_created: str = Field(
        description="The date and time when the cron job was created"
    )
    username: str = Field(description="Username for the cron job")
    thread_id: str = Field(description="Thread ID for the cron job")
