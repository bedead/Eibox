from pydantic import Field, BaseModel


class LoginSchema(BaseModel):
    username: str = Field(description="The username of the user")
    password: str = Field(description="The password for the user account")
