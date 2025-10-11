from fastapi import FastAPI, Depends, HTTPException, status
from typing import List, Annotated
from models import User, Member, ExpenseGroup, Expense, RecurringExpense, Audit, Breakdown
from schemas import (
    MemberRead, MemberCreate, MemberUpdate,
    ExpenseGroupCreate, ExpenseGroupUpdate, ExpenseGroupRead, UserRead,
    AuditRead, ExpenseRead, ExpenseCreate, ExpenseUpdate, RecurringExpenseBase
)
from database import SessionDep

from crud import (
    get_member, get_member_by_member_id, add_member_to_group,
    remove_member_from_group, update_member_role, get_group_members,
    get_expense_group, create_group, update_expense_group, delete_expense_group
)

app = FastAPI()


# can consider shifting this function to services.py
def get_user(username: str, session: SessionDep) -> User | None:
    user = session.get(User, username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

UserDep = Annotated[User, Depends(get_user)]


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