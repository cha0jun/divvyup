from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime

class ExpenseGroup(SQLModel, table=True):
    __tablename__ = "expense_group"

    id: int = Field(primary_key=True)
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
    created_on: datetime = Field(default_factory=datetime.now, nullable=False)

