"""
Google access token schema definition.

This module defines the `GoogleAccessTokens` model, which represents the
structure for storing Google account access tokens associated with a
user. It includes the username, account email, and the raw token data.
"""

from pydantic import BaseModel, EmailStr


class GoogleAccessTokens(BaseModel):
    username: str
    account_email: EmailStr
    token: dict
