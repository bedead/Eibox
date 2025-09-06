from typing import Any, Dict, List, Literal, Optional
from pydantic import Field, BaseModel, EmailStr


class UserModel(BaseModel):
    # Basic user information
    user_id: str = Field(description="The unique identifier of the user")
    account_created: str = Field(
        description="The date and time when the user account was created"
    )
    username: str = Field(description="The username of the user")
    email: EmailStr = Field(description="The email address of the user")
    password: str = Field(description="The password for the user account")

    full_name: Optional[str] = Field(description="The full name of the user")
    account_details_updated: Optional[str] = Field(
        description="The date and time when the user account details was last updated"
    )

    # User type
    user_type: Literal[
        "admin", "test_user", "free_user", "simple_paid_user", "premium_paid_user"
    ] = Field(
        description="The type of user (must be one of: admin, test_user, free_user, simple_paid_user, premium_paid_user)",
        default="free_user",
    )

    # Application settings
    app_settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "auto_email_monitoring": False,
            "email_monitoring_frequency": 30,
            "email_notifications": False,
            "connected_gmail_accounts_email": [],
        },
        description="Flexible application settings, can include any future parameters",
    )
