from pydantic import BaseModel, Field


class CronJobSchema(BaseModel):
    username: str = Field(description="Username for the cron job")
    thread_id: str = Field(description="Thread ID for the cron job")
