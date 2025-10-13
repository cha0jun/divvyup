import jwt
import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from fastapi import HTTPException, Header
from datetime import datetime, timedelta, timezone

# --- ADD THESE THREE LINES FOR DEBUGGING ---
print("--- INSPECTING THE 'jwt' MODULE ---")
print(f"File location of jwt module: {jwt.__file__}")
print(f"Contents of jwt module: {dir(jwt)}")
# -------------------------------------------

load_dotenv()

# --- Hashing ---
pw_crypt = CryptContext(schemes=["bcrypt"], deprecated = "auto")

def hash_password(password: str):
    return pw_crypt.hash(password)

def verify_password(in_password, hashed_password):
    return pw_crypt.verify(in_password, hashed_password)

# --- JWT Token ---

SECRET = os.getenv("SECRET_KEY")
ALGO = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 

def create_token(user_id: int, email: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": exp, 
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET, algorithms=[ALGO])

def verify_credentials(username: str, password: str) -> dict:
    pass

# This is mandatory token
# If missing token header, return 401
# Decode token, if Error, return 401
def require_user(tcxlogin: str = Header(None, alias="tcxlogin")) -> dict:
    # TODO
    pass

# This is optional token
# If missing token header, return None
# Decode token, if Error, return None
def require_token(tcxlogin: str | None = Header(None, alias="tcxlogin")) -> dict | None:
    # TODO
    pass

