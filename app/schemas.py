from pydantic import BaseModel, ConfigDict, Field as PydanticField, field_validator
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
    # is_admin: bool = False
    #description not showing on swagger 

class MemberUpdate(BaseModel):
    is_admin: bool


class MemberRead(BaseModel):
    id: int
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
    admin_id: int 
    created_on: datetime
    created_by: int

    model_config = ConfigDict(from_attributes=True)
    
class TransferOwnership(BaseModel):
    #User ID of the member to promote to admin
    new_admin_user_id: int

class AuditRead(BaseModel):
    change_description: str

    model_config = ConfigDict(from_attributes=True)

 # ---------Breakdown Schemas--------   

class BreakdownBase(BaseModel):
    debtor_id: int
    amount: float = PydanticField(gt=0)

class BreakdownCreate(BreakdownBase):
    pass

class BreakdownUpdate(BaseModel):
    debtor_id: Optional[int] = None
    amount: Optional[float] = PydanticField(default=None, gt=0)

class BreakdownRead(BreakdownBase):
    id: int
    expense_id: int
    
    model_config = ConfigDict(from_attributes=True)

# ---------Expense Schemas--------
 
class ExpenseBase(BaseModel):
    name: str
    description: Optional[str] = None
    payer_id: int
    amount: float
    payment_date: datetime
    
# might be possible to use ExpenseBase across
    
class ExpenseCreate(ExpenseBase):
    breakdowns: List[BreakdownCreate]

    @field_validator('breakdowns')
    @classmethod
    def validate_breakdowns(cls, breakdowns: List[BreakdownCreate], info):
        if not breakdowns:
            raise ValueError("At least one breakdown is required")
        
        # Optional: Validate total of breakdowns matches expense amount
        total = sum(b.amount for b in breakdowns)
        amount = info.data.get('amount')
        if amount and abs(total - amount) > 0.01:  # Allow for rounding
            raise ValueError(f"Breakdown total ({total}) must equal expense amount ({amount})")
        
        return breakdowns


class ExpenseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    payment_date: Optional[datetime] = None
    payer_id: Optional[int] = None
    breakdowns: Optional[List[BreakdownCreate]] = None

class ExpenseRead(ExpenseBase):
    id: int
    expense_group_id: int
    breakdowns: List[BreakdownRead] = []

    model_config = ConfigDict(from_attributes=True)


## ---------Recurring Expense Schemas--------
class RecurringExpenseBase(BaseModel):
    frequency: str
    start_date: datetime
    end_date: datetime

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