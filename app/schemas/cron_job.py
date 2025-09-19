"""
Cron job schema definition.

This module defines the `CronJobSchema` model, which represents the data
required to manage cron jobs for a user. It includes the username and
thread ID as required fields, with descriptive metadata for validation
and documentation.
"""

from pydantic import BaseModel, Field


class CronJobSchema(BaseModel):
    username: str = Field(description="Username for the cron job")
    thread_id: str = Field(description="Thread ID for the cron job")
