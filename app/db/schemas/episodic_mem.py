from typing import List

from pydantic import BaseModel


class EpisodicMemSchema(BaseModel):
    last_summary: str
    important_events: List[str] = []
    mistakes_to_avoid: List[str] = []
    user_feedback: List[str] = []
