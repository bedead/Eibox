from typing import List, Optional
from pydantic import BaseModel, EmailStr


class GmailAccount(BaseModel):
    email: EmailStr
    refresh_token: Optional[str]
    access_token: str
    expires_in: Optional[int]
    token_type: Optional[str]
    scope: Optional[List[str]]
