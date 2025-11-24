
from passlib.context import CryptContext

# --- Hashing ---
pw_crypt = CryptContext(schemes=["bcrypt"], deprecated = "auto")

def hash_password(password: str):
    return pw_crypt.hash(password)

def verify_password(in_password, hashed_password):
    return pw_crypt.verify(in_password, hashed_password)