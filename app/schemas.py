from pydantic import BaseModel
from datetime import datetime

class UserRead(BaseModel):
    id: int
    name: str
    email: str

class MemberCreate(BaseModel):
    user_id: int  
    is_admin: bool = False

class MemberUpdate(BaseModel):
    is_admin: bool


class MemberRead(BaseModel):
    id: int
    is_admin: bool
    user: UserRead # Show who the member is
    created_on: datetime