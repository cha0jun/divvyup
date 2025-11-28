from fastapi import APIRouter, status, Response, Depends, Cookie
from typing import Annotated
from ..schemas import *
from ..database import *
from ..crud import *
from ..services import *
from ..security import *
from ..auth import *

router = APIRouter(
    tags=['user']
)


#------User Routes-------

@router.post("/token")
def login(
    response: Response, 
    db: SessionDep, 
    login_data: UserLogin
    ) -> UserRead:
    """
    Logs a user in and sets an HttpOnly access_token cookie.
    Returns the user's basic info.
    """
    user = authenticate_user(db, login_data.email, login_data.password) #validation
    access_token = create_token(user_id = user.id, email = user.email) 
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,      # <-- The most important security flag!
        secure=True,        # <-- For HTTPS
        samesite="lax",     # <-- Good security default
        path="/"
    )
    
    create_log(db, f'{user.name} logged in.', user)
    
    return UserRead(id=user.id, name=user.name, email=user.email)

@router.post("/register", response_model = UserRead)
def register_new_user(db: SessionDep, user: UserCreate):
    """Register a new user"""
    is_email_exist = get_user_by_email(db, email = user.email)
    if is_email_exist:
        raise HTTPException(
            status_code = 400, 
            detail = "Email is registered, use another email.")
    new_user = create_user(db, user)
    create_log(db, f'Account created for {new_user.name}', new_user)
    return new_user

@router.post("/logout", status_code = status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    db: SessionDep,
    access_token: Annotated[str | None, Cookie()] = None
    ):
    """
    Log out current user by adding token 
    to blocklist and clearing the cookie.
    """
    if access_token:
        try:
            payload = decode_token(access_token)
            jti = payload.get("jti")
            exp = payload.get("exp")

            if jti and exp:
                expiry_dt  = datetime.fromtimestamp(exp, tz = timezone.utc)
                add_token_to_blocklist(db, jti = jti, expiry_dt = expiry_dt)
        
        except JWTError:
            # Token is invalid, but we'll clear the cookie anyway
            pass

    # Clear the access_token cookie
    response.delete_cookie(
        key="access_token", 
        path="/", 
        secure=True, 
        httponly=True, 
        samesite="lax"
        )
    
    create_log(db, f"Token added to blocklist - {access_token}",None)
    return None