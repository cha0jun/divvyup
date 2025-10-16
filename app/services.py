from fastapi import FastAPI, HTTPException, Depends, Body, status
from .database import Session
from .crud import get_expense_group, get_member




def validate_expense_group(db: Session, group_id:int, error_detail: str | None) -> None:
    db_group = get_expense_group(db, group_id)
    if not db_group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= error_detail)
    return db_group
    
def validate_group_member(db: Session, user_id:int, group_id:int, error_detail: str | None) -> None:
    db_member = get_member(db, user_id, group_id)
    if not db_member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_detail)
    return 

def validate_group_admin(db: Session, user_id:int, group_id:int, error_detail: str|None) -> None:
    db_group = get_expense_group(db, group_id)
    if db_group.admin_id != user_id:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_detail)
    return
