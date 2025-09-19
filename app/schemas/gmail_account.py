"""
Gmail account schema definition.

This module defines the `GmailAccount` model, which represents the structure
for storing Gmail account credentials and metadata. It includes details such
as username, email, access/refresh tokens, token expiry, and scopes.
"""

from typing import List, Optional
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
