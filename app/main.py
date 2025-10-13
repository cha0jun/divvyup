from fastapi import FastAPI, Depends, HTTPException, status
from typing import List
from models import *
from schemas import *
from database import SessionDep
from crud import *

app = FastAPI()

#------Member Routes-------

@app.get("/groups/{group_id}/members", response_model=List[MemberRead])
def read_group_members(
    group_id: int,
    db: SessionDep,
    current_user: User = Depends(get_user)
):
    if not get_member(db, user_id=current_user.id, group_id=group_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )
    return get_group_members(db, group_id=group_id)

@app.patch("/groups/{group_id}/members/{member_id}", response_model=MemberRead)
def update_member(
    group_id: int,
    member_id: int,
    member_update: MemberUpdate,
    db: SessionDep,
    current_user: User = Depends(get_user)):
    
    performing_admin = get_member(db, user_id=current_user.id, group_id=group_id)
    if not performing_admin or not performing_admin.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group admins can update member roles"
        )
    
    updated_member = update_member_role(
        db=db,
        member_id=member_id,
        group_id=group_id,
        member_update=member_update
    )

    return updated_member
    
@app.delete("/groups/{group_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    group_id: int,
    member_id: int,
    db:SessionDep,
    current_user: User = Depends(get_user)
):
    # Permission Check: Ensure the current user is an admin
    performing_admin = get_member(db, user_id=current_user.id, group_id=group_id)
    if not performing_admin or not performing_admin.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group admins can remove members"
        )
    
    remove_member_from_group(db, member_id=member_id, group_id=group_id)
    return None



#------Expense Routes-------
#get, put, patch, delete

@app.get("/group/{group_id}/expenses", response_model=List[ExpenseBase])
def get_expense():
    pass


#------Recurring Expense Routes-------

#------Breakdown Routes-------