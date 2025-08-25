from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr


class GmailAccount(BaseModel):
    """
    Schema class for gmail account data storage.
    """

    username: str
    email: EmailStr
    refresh_token: str
    token_last_refresh_time: Optional[str] = None
    access_token: str
    expires_in: int
    token_type: Optional[str] = None
    scope: List[str]
