from fastapi import APIRouter, HTTPException
from api.schema.GoogleAccessToken import GoogleAccessTokens
from api.schema.RegisterSchema import RegisterSchema
from api.schema.LoginSchema import LoginSchema
from api.auth.register_user import register_user as ru
from api.auth.login_user import login_user as lu
from core.storage.gmail.token_store import save_user_token

router = APIRouter()
namespace_for_memory = ("auth", "user")


@router.post("/save-google-tokens/v1")
def handle_google_oauth(token: GoogleAccessTokens):
    try:
        # Replace this with actual DB logic
        save_user_token(
            user_id=token.user_id,
            openid=token.openid,
            access_token=token.access_token,
            refresh_token=token.refresh_token,
            id_token=token.id_token,
            expires_in=token.expires_in,
            token_type=token.token_type,
            scope=token.scope,
        )
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
