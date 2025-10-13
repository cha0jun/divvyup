from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# interface for frontend to backend

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

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

class ExpenseGroupBase(BaseModel):
    name: str
    description: Optional[str] = None

class ExpenseGroupCreate(ExpenseGroupBase):
    pass

class ExpenseGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ExpenseGroupRead(ExpenseGroupBase):
    id: int
    created_on: datetime
    creator: UserRead
    modified_on: Optional[datetime] = None
    modified_by: Optional[UserRead] = None
    
class AuditRead(BaseModel):
    change_description: str
    created_by: UserRead
    created_on: datetime

class ExpenseBase(BaseModel):
    name: str
    description: Optional[str] = None
    payer: UserRead
    amount: float
    payment_date: datetime
    created_by: UserRead
    modified_by: UserRead
    
# might be possible to use ExpenseBase across
    
class ExpenseRead(ExpenseBase):
    pass

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(ExpenseBase):
    pass

class RecurringExpenseBase(ExpenseBase):
    frequency: str
    start_date: datetime
    end_date: datetime

## to create delete when nesscessary

class BreakdownBase(BaseModel):
    amount: float
    paid_by: UserRead
    
    
