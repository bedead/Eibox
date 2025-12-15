"""
Cron job schema definition.

This module defines the `CronJobSchema` model, which represents the data
required to manage cron jobs for a user. It includes the username and
thread ID as required fields, with descriptive metadata for validation
and documentation.
"""

from typing import Any, Dict, List
from pydantic import BaseModel, Field


class CronJobSchema(BaseModel):
    username: str = Field(description="Username for the cron job")
    thread_id: str = Field(description="Thread ID for the cron job")
    preferences: Dict[str, Any] = Field(
        description="Preferences and settings for cron job"
    )


class CronJobResponseSchema(BaseModel):
    job_id: str = Field(description="Unique identifier for the cron job")
    status: str = Field(description="Current status of the cron job")
    details: Dict[str, Any] = Field(description="Additional details about the cron job")


class CronJobDelete_CheckSchema(BaseModel):
    username: str = Field(description="Username for the cron job to be deleted")
    thread_id: str = Field(description="Thread ID for the cron job to be deleted")


class CronJobListResponseSchema(BaseModel):
    jobs: List[CronJobResponseSchema] = Field(description="List of cron jobs")
