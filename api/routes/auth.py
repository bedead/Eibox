from fastapi import APIRouter
from api.schema.RegisterSchema import RegisterSchema
from api.schema.LoginSchema import LoginSchema
from api.auth.register_user import register_user as ru
from api.auth.login_user import login_user as lu

router = APIRouter()
namespace_for_memory = ("auth", "user")


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
