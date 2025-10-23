from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship, UniqueConstraint, Column, DateTime
from datetime import datetime,  timezone
from enum import Enum

# interface for business logic to db

class User(SQLModel, table=True):
    __tablename__ = "user"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str 
    email: str = Field(unique=True)
    password_hash: str 

    # UTC timestamp set by Python when inserting
    created_on: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, nullable=False)
    )
    # Modified timestamp can be auto-updated by triggers in DB
    modified_on: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, nullable=False)
    )
    memberships: List["Member"] = Relationship(back_populates="user")
    sent_invitations: List["Invitation"] = Relationship(
        back_populates="inviter",
        sa_relationship_kwargs={"foreign_keys": "[Invitation.inviter_id]"}
    )
    received_invitations: List["Invitation"] = Relationship(
        back_populates="invitee",
        sa_relationship_kwargs={"foreign_keys": "[Invitation.invitee_id]"}
    )

class ExpenseGroup(SQLModel, table=True):
    __tablename__ = "expense_group"

    id: Optional[int] = Field(default=None, primary_key=True)
    admin_id: int = Field(foreign_key="user.id")
    name: str 
    description: Optional[str] = None
    created_by: int = Field(foreign_key="user.id")
    created_on: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, nullable=False)
    )
    modified_by: int = Field(foreign_key="user.id")
    modified_on: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, nullable=False)
    )

    expenses: List["Expense"] = Relationship(back_populates="group")
   
    #cascade delete to delete all related Member rows(child) immediately when deleting an ExpenseGroup(parent)
    members: List["Member"] = Relationship(
    back_populates="group",
    sa_relationship_kwargs={"cascade": "all, delete"}
    )
    invitations: List["Invitation"] = Relationship(back_populates="group")


class Member(SQLModel, table = True):
    __tablename__ = "member"
    __table_args__ = (
        UniqueConstraint("user_id", "expense_group_id", name="unique_user_group"),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key= "user.id")
    expense_group_id: int = Field(foreign_key="expense_group.id")
    added_by: Optional[int] = Field(default=None, foreign_key="member.id")
    added_on: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, nullable=False)
    )

    user: User = Relationship(back_populates="memberships")
    group: ExpenseGroup = Relationship(back_populates="members")
    

    
class Expense(SQLModel, table=True):
    __tablename__ = "expense"

    id: Optional[int] = Field(default=None, primary_key=True)
    expense_group_id: int = Field(foreign_key="expense_group.id")
    amount: float = Field(gt =0)
    payment_date: datetime 
    payer_id: int = Field(foreign_key="user.id")
    name: str
    description: Optional[str] = None
    created_by: int = Field(foreign_key="user.id")
    created_on: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, nullable=False)
    )
    modified_by: int = Field(foreign_key="user.id")
    modified_on: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, nullable=False)
    )

    group: ExpenseGroup = Relationship(back_populates="expenses")
    breakdowns: List["Breakdown"] = Relationship(
    back_populates="expense",
    sa_relationship_kwargs={
        "cascade": "all, delete-orphan",
        "passive_deletes": True
    }
    )


class Breakdown(SQLModel, table = True):
    __tablename__ = "breakdown"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    expense_id: int = Field(foreign_key="expense.id")
    amount: float = Field(gt =0)
    debtor_id: int = Field(foreign_key="user.id") #debtor_id changed from paid_by_id
    created_by: int = Field(foreign_key="user.id")
    created_on: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, nullable=False)
    )
    modified_by: int = Field(foreign_key="user.id")
    modified_on: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, nullable=False)
    )
    
    expense: Optional["Expense"] = Relationship(back_populates="breakdowns")


class RecurringExpense(SQLModel, table=True):
    __tablename__ = "recurring_expense"
    
    expense_id: int = Field(primary_key=True, foreign_key="expense.id")
    frequency: str 
    start_date: datetime #removed default. User must provide
    end_date: datetime
    created_by: int = Field(foreign_key="user.id")
    created_on: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, nullable=False)
    )
    modified_by: int = Field(foreign_key="user.id")
    modified_on: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, nullable=False)
    ) 
    
class Audit(SQLModel, table = True):
    __tablename__ = "audit"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    change_description: str 
    #@Matthew expense_group_id and created_by are nullable in the schemas. 
    expense_group_id: int = Field(foreign_key="expense_group.id")
    created_by: int = Field(foreign_key="user.id")
    created_on: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, nullable=False)
    )
    
class InvitationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CANCELED = "canceled"

class Invitation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    expense_group_id: int = Field(foreign_key="expense_group.id")
    inviter_id: int = Field(foreign_key="user.id")
    invitee_id: int = Field(foreign_key="user.id")
    status: InvitationStatus = Field(default=InvitationStatus.PENDING, nullable=False)
    created_on: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, nullable=False)
    )
    
    #Relationships
    group: "ExpenseGroup" = Relationship(back_populates="invitations")
    inviter: "User" = Relationship(
        back_populates="sent_invitations",
        sa_relationship_kwargs={"foreign_keys": "[Invitation.inviter_id]"}
    )
    invitee: "User" = Relationship(
        back_populates="received_invitations",
        sa_relationship_kwargs={"foreign_keys": "[Invitation.invitee_id]"}
        )

class TokenBlockList(SQLModel, table = True):
    __tablename__ = "token_blocklist"

    id: Optional[int] = Field(default=None, primary_key=True)
    jti: str = Field(unique = True, index = True)
    expiry_dt: datetime = Field(
        sa_column = Column(DateTime(timezone = True), nullable = False)
    )

    