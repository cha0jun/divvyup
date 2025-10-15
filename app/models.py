from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime

# interface for business logic to db

class User(SQLModel, table=True):
    __tablename__ = "user"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str 
    email: str = Field(unique=True)
    password_hash: str 
    created_on: datetime = Field(default_factory=datetime.now)
    modified_on: datetime = Field(default_factory=datetime.now)

    memberships: List["Member"] = Relationship(back_populates="user")

class ExpenseGroup(SQLModel, table=True):
    __tablename__ = "expense_group"

    id: Optional[int] = Field(default=None, primary_key=True)
    admin_id: int = Field(foreign_key="user.id")
    name: str 
    description: Optional[str] = None
    created_by: int = Field(foreign_key="user.id")
    created_on: datetime = Field(default_factory=datetime.now)
    modified_by: int = Field(foreign_key="user.id")
    modified_on: datetime = Field(default_factory=datetime.now)

    expenses: List["Expense"] = Relationship(back_populates="group")
    members: List["Member"] = Relationship(back_populates="group")


class Member(SQLModel, table = True):
    __tablename__ = "member"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key= "user.id")
    expense_group_id: int = Field(foreign_key="expense_group.id")
    is_admin: bool = Field(default=False)
    added_by: Optional[int] = Field(default=None, foreign_key="member.id")
    added_on: datetime = Field(default_factory=datetime.now)

    user: User = Relationship(back_populates="memberships")
    group: ExpenseGroup = Relationship(back_populates="members")
    
class Expense(SQLModel, table=True):
    __tablename__ = "expense"

    id: Optional[int] = Field(default=None, primary_key=True)
    expense_group_id: int = Field(foreign_key="expense_group.id")
    amount: float
    payment_date: datetime = Field(default_factory=datetime.now)
    #@Matthew payer_id should link to a member id. Only a member can be registered as the payer for an expense. -May
    payer_id: int = Field(foreign_key="user.id")
    name: str
    description: Optional[str] = None
    created_by: int = Field(foreign_key="user.id")
    created_on: datetime = Field(default_factory=datetime.now)
    modified_by: int = Field(foreign_key="user.id")
    modified_on: datetime = Field(default_factory=datetime.now)

    group: ExpenseGroup = Relationship(back_populates="expenses")
    breakdowns: List["Breakdown"] = Relationship(back_populates="expense")

class Breakdown(SQLModel, table = True):
    __tablename__ = "breakdown"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    expense_id: int = Field(foreign_key="expense.id")
    amount: float 
    #debtor_id changed from paid_by_id
    debtor_id: int = Field(foreign_key="user.id")
    created_by: int = Field(foreign_key="user.id")
    created_on: datetime = Field(default_factory=datetime.now)
    modified_by: int = Field(foreign_key="user.id")
    modified_on: datetime = Field(default_factory=datetime.now)
    
    expense: Expense = Relationship(back_populates="breakdowns")


class RecurringExpense(SQLModel, table=True):
    __tablename__ = "recurring_expense"
    
    expense_id: int = Field(primary_key=True, foreign_key="expense.id")
    frequency: str 
    start_date: datetime = Field(default_factory=datetime.now)
    #@Matthew end_date field should be Optional[datetime] = None to allow for expenses that run indefintely. -May
    end_date: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="user.id")
    created_on: datetime = Field(default_factory=datetime.now)
    modified_by: int = Field(foreign_key="user.id")
    modified_on: datetime = Field(default_factory=datetime.now)
    
class Audit(SQLModel, table = True):
    __tablename__ = "audit"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    change_description: str 
    expense_group_id: int = Field(foreign_key="expense_group.id")
    created_by: int = Field(foreign_key="user.id")
    created_on: datetime = Field(default_factory=datetime.now)
    

    