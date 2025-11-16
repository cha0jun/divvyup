from fastapi import HTTPException,status
from database import Session
from crud import get_expense_group, get_member, create_member, get_member_by_member_id, get_expense, get_user_by_email
from models import ExpenseGroup, Member, User, Expense
from sqlalchemy.exc import IntegrityError




def validate_expense_group(db: Session, group_id:int, error_detail: str | None) -> ExpenseGroup:
    db_group = get_expense_group(db, group_id)
    print(f"validate_expense_group: group_id={group_id}, db_group={db_group}")
    if not db_group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= error_detail)
    return db_group
    
def validate_group_member(db: Session, user_id:int, group_id:int, error_detail: str | None) -> Member:
    db_member = get_member(db, user_id, group_id)
    if not db_member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_detail)
    return db_member

def validate_group_admin(db: Session, user_id:int, group_id:int, error_detail: str|None) -> Member:
    db_group = get_expense_group(db, group_id)
    if db_group.admin_id != user_id:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_detail)
    performing_admin = get_member(db, user_id, group_id)
    return performing_admin

def validate_user_exists(db: Session, user_id: int, error_detail: str | None = None) -> User:
    user = db.get(User, user_id)
    if not user:
        detail = error_detail or "User not found"
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )
    return user

def validate_user_by_email(db: Session, email: str, error_detail: str | None = None) -> User:
    user = get_user_by_email(db, email)
    if not user:
        detail = error_detail or f"User with email '{email}' not found."
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )
    return user

def add_member_to_group_service(db: Session, user_to_add: User, group_id: int, performing_admin: Member)-> Member:
    existing = get_member(db, user_to_add.id, group_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this group."
        )

    # To catch IntegrityError
    try:
        return create_member(db, user_to_add, group_id, performing_admin.user_id)
    except IntegrityError as e:
        db.rollback()
        if "UNIQUE constraint failed" in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this group (database constraint)."
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error"
                )
    

def validate_member_exists_in_group(db: Session, member_id: int, group_id: int, error_detail: str | None = None) -> Member:
    db_member = get_member_by_member_id(db, member_id)
    if not db_member:
        raise HTTPException(
            status_code=404,
            detail= error_detail or "Member not found in this group"
        )
    if db_member.expense_group_id != group_id:
        raise HTTPException(
            status_code=404,
            detail=error_detail or "Member not found in this group"
        )
    return db_member

def validate_membership_exists(db: Session, user_id: int, group_id: int) -> Member:
    """
    Finds the membership record for a specific user and group.
    Raises 404 if the user is not in the group.
    """
    membership = get_member(db, user_id=user_id, group_id=group_id)
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This user is not a member of this group."
        )
    
    return membership

def validate_member_is_not_admin(member: Member, group: ExpenseGroup):
    """
    Checks if a specific member is the admin of the group.
    Raises 400 if they are the admin.
    """
    # Add safety check: cannot remove the group admin
    if member.user_id == group.admin_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the group admin. Change the admin first."
        )

#---------Expense route validation-------
def validate_expense_in_group( db: Session, expense_id: int, group_id: int, error_detail: str | None = None) -> Expense:
    """
    Validate that an expense exists and belongs to the specified group.
    """
    expense = get_expense(db, expense_id)
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_detail or "Expense not found"
        )
    
    if expense.expense_group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_detail or "Expense not found in this group"
        )
    
    return expense