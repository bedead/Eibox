from typing import List, Optional

from pydantic import BaseModel


class SemanticMemSchema(BaseModel):
    full_name: Optional[str]
    users_emails: List[str] = []
    works_at: Optional[str]
    location: Optional[str]
    interests: List[str] = []
    skills: List[str] = []
    preferences: List[str] = []
