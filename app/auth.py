import os
from dotenv import load_dotenv
from fastapi import HTTPException, Depends, status, Cookie
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from typing import Annotated, Optional
import uuid

from .crud import get_user_by_email, is_token_blocked
from .database import SessionDep
from .models import User
from .security import verify_password


load_dotenv()


#-----Load secret key----
SECRET = os.environ.get("SECRET_KEY")
ALGO = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 

# --- JWT Token ---

def create_token(user_id: int, email: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    jti = str(uuid.uuid4())
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": exp,
        "jti": jti #token id
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGO])
        return payload
    
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

def authenticate_user(db: SessionDep, email: str, password: str) -> User:
    """Authenticate a user by verifying their email and password."""
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

def get_token_from_cookie(access_token: Annotated[str | None, Cookie()] = None) -> str:
    """
    Dependency to get the token from the access_token cookie.
    Raises 401 if cookie is missing.
    """
    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated (no token).",
        )
    return access_token

def get_current_user(
    db: SessionDep, token: Annotated[str, Depends(get_token_from_cookie)]
    ) -> User:
    """
    Dependency to verify JWT token from cookie 
    and return the current authenticated user.
    """
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")

        if not user_id or not jti:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing claims",
            )
        
        if is_token_blocked(db, jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: logged out",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    
    user = get_user_by_email(db, email=payload.get("email"))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user

def get_current_user_optional(
    db: SessionDep, access_token: Annotated[str | None, Cookie()] = None
) -> User | None:
    """
    Dependency to get the current user if they are logged in,
    but return None instead of raising an error if they are not.
    """
    if access_token is None:
        return None
    try:
        return get_current_user(db, token=access_token)
    except HTTPException:
        return None

UserDep = Annotated[User, Depends(get_current_user)]


