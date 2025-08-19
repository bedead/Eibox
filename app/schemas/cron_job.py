from pydantic import BaseModel, Field


class CronJobSchema(BaseModel):
    user_id: str = Field(description="The unique identifier for the user")
    username: str = Field(description="Username for the cron job")
    thread_id: str = Field(description="Thread ID for the cron job")
