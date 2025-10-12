import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Header

'''
@may @sirhan this is the auth login from test 3, i paste it here for now, we can enhance for our app if required
'''

SECRET = "dev-secret"
ALGO = "HS256"

pw_crypt = CryptContext(schemes=["bcrypt"], deprecated = "auto")

def hash_password(password: str):
    return pw_crypt.hash(password)

def verify_password(in_password, hashed_password):
    return pw_crypt.verify(in_password, hashed_password)

def create_token(user_id: int, username: str) -> str:
    payload = {
        "sub": str(user_id),
        "username": username,
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET, algorithms=[ALGO])

def verify_credentials(username: str, password: str) -> dict:
    user = get_user(username)
    if user and user.password == password:
        return user
    return None
    
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

