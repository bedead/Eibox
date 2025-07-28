from pydantic import BaseModel, Field


class CronJobSchema(BaseModel):
    user_id: str = Field(description="User ID for the cron job")
    thread_id: str = Field(description="Thread ID for the cron job")
