from typing import Optional
from pydantic import BaseModel, EmailStr


class GoogleAccessTokens(BaseModel):
    user_id: str  # Optional: if you want to associate it with your user
    user_email: EmailStr
    openid: str
    access_token: str
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    expires_in: Optional[int] = None
    token_type: Optional[str] = None
    scope: Optional[str] = None
