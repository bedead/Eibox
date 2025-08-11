from pydantic import BaseModel, EmailStr


class GoogleAccessTokens(BaseModel):
    user_id: str
    username: str
    account_email: EmailStr
    token: dict
