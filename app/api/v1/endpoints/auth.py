from fastapi import APIRouter, HTTPException
from app.schemas.google_access_token import GoogleAccessTokens
from app.schemas.register import RegisterSchema
from app.schemas.login import LoginSchema
from app.db.repos.auth.register_user import register_user as ru
from app.db.repos.auth.login_user import login_user as lu
from app.db.repos.gmail.add_gmail_accounts import add_gmail_account
from dotenv import load_dotenv


load_dotenv()


router = APIRouter()
namespace_for_memory = ("auth", "user")


@router.post("/register/")
def register_user(user: RegisterSchema):
    return ru(user, namespace_for_memory)


@router.post("/login/")
def login_user(user: LoginSchema):
    return lu(user, namespace_for_memory)

