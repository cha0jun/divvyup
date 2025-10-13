from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime

# interface for business logic to db

class Token(SQLModel, table=True):
    __tablename__ = "token"

    access_token: str = Field(default=None, primary_key=True)
    token_type: str = "bearer"

class User(SQLModel, table=True):
    __tablename__ = "user"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    email: str = Field(nullable=False, unique=True)
    password_hash: str = Field(nullable=False)
    created_on: datetime = Field(default_factory=datetime.now, nullable=False)
    modified_on: datetime = Field(default_factory=datetime.now, nullable=False)

class ExpenseGroup(SQLModel, table=True):
    __tablename__ = "expense_group"

    id: Optional[int] = Field(default=None, primary_key=True)
    admin_id: int = Field(foreign_key="user.id", nullable=False)
    name: str = Field(nullable=False)
    description: Optional[str] = None
    created_by: int = Field(foreign_key="user.id", nullable=False)
    created_on: datetime = Field(default_factory=datetime.now, nullable=False)
    modified_by: int = Field(foreign_key="user.id", nullable=False)
    modified_on: datetime = Field(default_factory=datetime.now, nullable=False)

class Member(SQLModel, table = True):
    __tablename__ = "member"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key= "user.id",nullable=False)
    expense_group_id: int = Field(foreign_key="expense_group.id",nullable=False)
    is_admin: bool = Field(default=False)
    added_by: Optional[int] = Field(default=None, foreign_key="member.id")
    added_on: datetime = Field(default_factory=datetime.now, nullable=False)
    
class Expense(SQLModel, table=True):
    __tablename__ = "expense"

    id: int = Field(primary_key=True)
    expense_group_id: int = Field(foreign_key="expense_group.id", nullable=False)
    amount: float = Field(nullable=False)
    payment_date: datetime = Field(default_factory=datetime.now, nullable=False)
    payer_id: int = Field(foreign_key="user.id", nullable=False)
    name: str = Field(nullable=False)
    description: Optional[str] = None
    created_by: int = Field(foreign_key="user.id", nullable=False)
    created_on: datetime = Field(default_factory=datetime.now, nullable=False)
    modified_by: int = Field(foreign_key="user.id", nullable=False)
    modified_on: datetime = Field(default_factory=datetime.now, nullable=False)

class RecurringExpense(SQLModel, table=True):
    __tablename__ = "recurring_expense"
    
    expense_id: int = Field(primary_key=True, foreign_key="expense.id",nullable=False)
    frequency: str = Field(nullable=False)
    start_date: datetime = Field(default_factory=datetime.now, nullable=False)
    end_date: datetime = Field(default_factory=datetime.now, nullable=False)
    created_by: int = Field(foreign_key="user.id", nullable=False)
    created_on: datetime = Field(default_factory=datetime.now, nullable=False)
    modified_by: int = Field(foreign_key="user.id", nullable=False)
    modified_on: datetime = Field(default_factory=datetime.now, nullable=False)
    
class Audit(SQLModel, table = True):
    __tablename__ = "audit"
    
    id: int = Field(primary_key=True, nullable=False)
    change_description: str = Field(nullable=False)
    expense_group_id: int = Field(foreign_key="expense_group.id")
    created_by: int = Field(foreign_key="user.id", nullable=False)
    created_on: datetime = Field(default_factory=datetime.now, nullable=False)
    
class Breakdown(SQLModel, table = True):
    __tablename__ = "breakdown"
    
    id: int = Field(primary_key=True, nullable=False)
    expense_id: int = Field(foreign_key="expense.id", nullable=False)
    amount: float = Field(nullable=False)
    paid_by_id: int = Field(foreign_key="user.id", nullable=False)
    created_by: int = Field(foreign_key="user.id", nullable=False)
    created_on: datetime = Field(default_factory=datetime.now, nullable=False)
    modified_by: int = Field(foreign_key="user.id", nullable=False)
    modified_on: datetime = Field(default_factory=datetime.now, nullable=False)
    
    
    