from fastapi import APIRouter, status
from ..schemas import *
from ..database import *
from ..crud import *
from ..services import *
import logging
from ..security import *
from ..auth import *

router = APIRouter(
    tags=['user']
)


#------User Routes-------

@router.post("/token", response_model = Token)
def login(db: SessionDep, login_data: UserLogin):
    user = get_user_by_email(db, email = login_data.email)
    print(user)
    if not user:
        logging.warning(f"--- Login failed: user not found for email {login_data.email} ---")
        raise HTTPException(
            status_code=401,
            detail="Invalid login credentials."
        )

        
    if not verify_password(login_data.password, user.password_hash):
        # Log the failure reason
        logging.warning("--- Password verification failed! ---")
        if user:
            logging.warning(f"--- Password from form: {login_data.password} ---")
            logging.warning(f"--- Hashed password from DB: {user.password_hash} ---")
            print("verification failed")
            raise HTTPException(
            status_code = 401,
            detail = "Invalid login."
            )
    
    access_token = create_token(user_id = user.id, email = user.email)
    return{
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/register", response_model = UserRead)
def register_new_user(db: SessionDep, user: UserCreate):
    """Register a new user"""
    is_email_exist = get_user_by_email(db, email = user.email)
    if is_email_exist:
        raise HTTPException(
            status_code = 400, 
            detail = "Email is registered, use another email.")
    new_user = create_user(db, user)
    return new_user

@router.post("/logout", status_code = status.HTTP_204_NO_CONTENT)
def logout(db: SessionDep, credentials: HTTPAuthorizationCredentials = Depends(http_bearer_scheme)):
    """Log out current user by adding token to blocklist."""
    token = credentials.credentials
    try:
        payload = decode_token(token)
        jti = payload.get("jti")
        exp = payload.get("exp")

        if not jti or not exp:
            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail = "Invalid token payload."
            )
        
        expiry_dt  = datetime.fromtimestamp(exp, tz = timezone.utc)
        add_token_to_blocklist(db, jti = jti, expiry_dt = expiry_dt)
        return None
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token for logout."
            )