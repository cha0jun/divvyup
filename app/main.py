from fastapi import Depends, HTTPException
from database import *


# can consider shifting this function to services.py
def get_user(username: str, session: SessionDep) -> User | None:
    user = session.get(User, username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

UserDep = Annotated[User, Depends(get_user)]