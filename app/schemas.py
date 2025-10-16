from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List, Dict

# interface for frontend to backend

class Token(BaseModel):
    access_token: str 
    token_type: str = "bearer"

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserRead(BaseModel):
    id: int
    name: str
    email: str
    
    #model_config to allow this schema to be created from a database object.
    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    email: str
    password: str
    

class MemberCreate(BaseModel):
    #User.id of the new user to be added to the group
    user_id: int 
    is_admin: bool = False
    #description not showing on swagger 

class MemberUpdate(BaseModel):
    is_admin: bool


class MemberRead(BaseModel):
    id: int
    is_admin: bool
    user: UserRead # Show who the member is
    added_on: datetime

    model_config = ConfigDict(from_attributes=True)

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
    created_by: int

    model_config = ConfigDict(from_attributes=True)

class AuditRead(BaseModel):
    change_description: str
    created_by: UserRead
    created_on: datetime

    model_config = ConfigDict(from_attributes=True)

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
    id: int
    payer: UserRead
    created_by: UserRead
    modified_by: UserRead

    model_config = ConfigDict(from_attributes=True)

class ExpenseCreate(ExpenseBase):
    payer_id: int
#When creating an expense, the client should only send the ID of the payer.
## The `created_by` and `modified_by` will be set by the server from the current user.

class ExpenseUpdate(ExpenseBase):
    name: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    payment_date: Optional[datetime] = None
    payer_id: Optional[int] = None

#For updates, all fields should be optional.

class RecurringExpenseBase(ExpenseBase):
    frequency: str
    start_date: datetime
    end_date: Optional[datetime] = None

## to create delete when nesscessary

class BreakdownBase(BaseModel):
    amount: float
    debtor_id: int
    #Changed from 'paid_by: UserRead' to 'debtor_id: int'. 
    ## The client should send the ID of the user who owes money.
    
    
class UserBalance(BaseModel):
    owes: Dict[str, float] = {}
    owed_by: Dict[str, float] = {}
    net_balance: float = 0.0

class GroupBalanceResponse(BaseModel):
    balances: Dict[str, UserBalance]