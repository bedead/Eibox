"""
Login schema definition.

This module defines the `LoginSchema` model used for user authentication.
It contains the username and password fields required for login requests.
"""

from pydantic import Field, BaseModel


class LoginSchema(BaseModel):
    username: str = Field(description="The username of the user")
    password: str = Field(description="The password for the user account")
