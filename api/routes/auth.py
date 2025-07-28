from fastapi import APIRouter
from api.schema.UserSchema import UserSchema
from api.auth.register import register_user as ru
from api.auth.login import login_user as lu

router = APIRouter()
namespace_for_memory = ("auth", "user")


@router.post("/register/v1")
def register_user(user: UserSchema):
    return ru(user, namespace_for_memory)


@router.get("/login/v1")
def login_user(user: UserSchema):
    return lu(user, namespace_for_memory)
