import os
from dotenv import load_dotenv
from fastapi import HTTPException, Depends, status
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials 
from typing import Annotated

from .crud import get_user_by_email
from .database import SessionDep
from .models import User
from .security import verify_password


load_dotenv()


#-----Load secret key----
SECRET = os.getenv("SECRET_KEY")
ALGO = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 

# --- JWT Token ---

def create_token(user_id: int, email: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": exp, 
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGO])
        return payload
    
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

def authenticate_user(db: SessionDep, email: str, password: str) -> User:
    "Authenticate a user by verifying their email and password."
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

http_bearer_scheme = HTTPBearer()

def get_current_user(db: SessionDep, credentials: HTTPAuthorizationCredentials = Depends(http_bearer_scheme) ):

    """
    Dependency to verify JWT token and return the current authenticated user.
    Raises HTTP 401 if token is invalid or expired.
    """
    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
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



UserDep = Annotated[User, Depends(get_current_user)]


