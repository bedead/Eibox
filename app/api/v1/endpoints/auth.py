from fastapi import APIRouter, HTTPException
import requests
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


@router.post("/oauth_gmail_access_token/v1")
def handle_google_oauth(token: GoogleAccessTokens):
    try:
        add_gmail_account(token=token, namespace_for_memory=namespace_for_memory)
        return {"message": "Tokens saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save tokens: {str(e)}")


@router.post("/register/v1")
def register_user(user: RegisterSchema):
    return ru(user, namespace_for_memory)


@router.post("/login/v1")
def login_user(user: LoginSchema):
    return lu(user, namespace_for_memory)


@router.get("/health")
def health_check():
    """
    Health check endpoint to verify the service is running.
    """
    return {"status": "ok", "message": "Auth service is running"}
