from pydantic import BaseModel, EmailStr


class GoogleAccessTokens(BaseModel):
    username: str
    account_email: EmailStr
    token: dict
