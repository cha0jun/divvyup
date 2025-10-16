from fastapi import FastAPI, HTTPException, Depends, Body, status
from .database import Session
from .crud import get_expense_group, get_member
from .models import ExpenseGroup, Member, User




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