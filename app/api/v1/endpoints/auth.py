from typing import Dict, List
from fastapi import APIRouter
from app.db.repos.gmail.get_gmail_accounts import get_gmail_account
from app.schemas.gmail_account import GmailAccount
from app.schemas.register import RegisterSchema
from app.schemas.login import LoginSchema
from app.db.repos.auth.register_user import register_user as ru
from app.db.repos.auth.login_user import login_user as lu
from dotenv import load_dotenv


load_dotenv()


router = APIRouter()
namespace_for_memory = ("auth", "user")


@router.post("/register")
def register_user(user: RegisterSchema):
    return ru(user, namespace_for_memory)


@router.post("/login")
def login_user(user: LoginSchema):
    gmail_accounts_data: List[GmailAccount] = get_gmail_account(
        username=user.username, namespace_for_memory=namespace_for_memory
    )
    login_data: Dict[str, any] = lu(user, namespace_for_memory)
    return {**login_data, "gmail_accounts": gmail_accounts_data}
