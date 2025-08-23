from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr


class GmailAccount(BaseModel):
    """
    Schema class for gmail account data storage.
    """

    username: str
    email: EmailStr
    refresh_token: Optional[str]
    token_last_refresh_time: Optional[datetime]
    access_token: str
    expires_in: Optional[int]
    token_type: Optional[str]
    scope: Optional[List[str]]
