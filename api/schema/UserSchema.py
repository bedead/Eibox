from typing import Optional
from pydantic import Field, BaseModel, EmailStr


class UserSchema(BaseModel):
    username: str = Field(description="The username of the user")
    full_name: Optional[str] = Field(description="The full name of the user")
    email: Optional[EmailStr] = Field(description="The email address of the user")
    password: str = Field(description="The password for the user account")
