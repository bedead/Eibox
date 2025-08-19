from typing import Optional
from pydantic import Field, BaseModel, EmailStr


class RegisterSchema(BaseModel):
    user_id: str = Field(description="The unique identifier of the user")
    account_created: str = Field(
        description="The date and time when the user account was created"
    )
    # account_updated: str = Field(description="The date and time when the user account was last updated")
    username: str = Field(description="The username of the user")
    full_name: Optional[str] = Field(description="The full name of the user")
    email: Optional[EmailStr] = Field(description="The email address of the user")
    password: str = Field(description="The password for the user account")
