import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from .models import *
from .schemas import *
from .database import SessionDep
from .crud import *
from .auth import *

app = FastAPI()

#------User Routes-------

@app.post("/token", response_model = Token)
def login(db: SessionDep, login_form: OAuth2PasswordRequestForm = Depends()):
    print("hello")
    user = get_user(db, email = login_form.username)
    print(user)
    if not user or verify_password(login_form.password, user.password_hash):
        # Log the failure reason
        logging.warning("--- Password verification failed! ---")
        if user:
            logging.warning(f"--- Password from form: {login_form.password} ---")
            logging.warning(f"--- Hashed password from DB: {user.password_hash} ---")
            print("verification failed")
            raise HTTPException(
            status_code = 401,
            detail = "Invalid login."
            )
    
    access_token = create_token(user_id = user.id, email = user.email)
    return{
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.post("/register", response_model = UserRead)
def validate_registration_email(db: SessionDep, user: UserCreate):
    is_email_exist = get_user(db, email = user.email)
    if is_email_exist:
        raise HTTPException(
            status_code = 400, 
            detail = "Email is registered, use another email.")
    new_user = create_user(db, user)
    return new_user

#------Member Routes-------

'''@app.get("/groups/{group_id}/members", response_model=List[MemberRead])
def read_group_members(
    group_id: int,
    db: SessionDep,
    current_user: UserDep
):
    
    """
    List all members in a specific expense group.
    Only accessible to users who are members of the group.
    """

    if not get_member(db, user_id=current_user.id, group_id=group_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )
    return get_group_members(db, group_id=group_id)'''

'''@app.patch("/groups/{group_id}/members/{member_id}", response_model=MemberRead)
@app.post("/groups/{group_id}/members", response_model=MemberRead, status_code=status.HTTP_201_CREATED)
def add_member(
    group_id: int,
    member_create: MemberCreate, 
    db: SessionDep,
    current_user: User = Depends(get_user)
):
    
    """
    Add a new member to an expense group.
    Only group admins are allowed to add members.
    """
    performing_admin = get_member(db, user_id=current_user.id, group_id=group_id)
    if not performing_admin or not performing_admin.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group admins can add members"
        )
    
    user_to_add = db.get(User, member_create.user_id)
    if not user_to_add:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User to add not found"
        )
    
    return add_member_to_group(db, group_id, user_to_add, performing_admin)
    
    
@app.patch("/groups/{group_id}/members/{member_id}", response_model=MemberRead)
def update_member(
    group_id: int,
    member_id: int,
    member_update: MemberUpdate,
    db: SessionDep,
    current_user: User = Depends(get_user)):

    """
    Update a member's role within a group (promote to admin).
    Only group admins can perform this action.
    """
    
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

    return updated_member'''
    
'''@app.delete("/groups/{group_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    group_id: int,
    member_id: int,
    db:SessionDep,
    current_user: User = Depends(get_user)
):
    
    """
    Remove a member from a group.
    Only group admins have permission to remove members.
    """

    # Permission Check: Ensure the current user is an admin
    performing_admin = get_member(db, user_id=current_user.id, group_id=group_id)
    if not performing_admin or not performing_admin.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group admins can remove members"
        )
    
    remove_member_from_group(db, member_id=member_id, group_id=group_id)
    return None'''

#------Group Routes--------

@app.post("/groups", response_model=MemberRead, status_code=status.HTTP_201_CREATED)
def create_expense_group(
    group: ExpenseGroupCreate,
    db: Session = SessionDep,
    current_user: User = Depends(get_user)
):
    
    """
    Create a new expense group.
    The user who creates the group automatically becomes the first admin member.
    """

    return create_group(db=db, group=group, creator=current_user)

@app.get("/groups/{group_id}", response_model=ExpenseGroupRead)
def read_expense_group(
    group_id: int,
    db: SessionDep,
    current_user: User = Depends(get_user)
):
    """
    Retrieve details of a specific expense group.
    Only accessible if the user is a member of the group.
    """
    db_group = get_expense_group(db, group_id)
    if not db_group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense group not found")
    return db_group

@app.get("/groups/{group_id}", response_model=ExpenseGroupRead)
def update_group_details(
    group_id: int,
    group_update: ExpenseGroupUpdate,
    db: SessionDep,
    current_user: User = Depends(get_user)
):
    """
    Update an expense group's name or description.
    Only the group admin can perform this action.
    """
    db_group = get_expense_group(db, group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Expense group not found")

    if db_group.admin_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the group admin can update this group"
        )

    updated_group = update_expense_group(db, group_id=group_id, group_update=group_update, modifier=current_user)
    return updated_group

@app.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: int,
    db: SessionDep,
    current_user: User = Depends(get_user)
):
    """
    Delete an expense group.
    Only the group admin can delete the group.
    """
    db_group = get_expense_group(db, group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Expense group not found")

    if db_group.admin_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the group admin can delete this group"
        )

    delete_expense_group(db, group_id=group_id)
    return None

#------Expense Routes-------
@app.get("/groups/{group_id}/expenses", response_model=List[ExpenseRead])
def get_expenses(group_id:int, current_user: User = Depends(get_user):
    db_group = get_expense_group(db, group_id)
    if not db_group:
        raise HttpException(status_code=404, detail= "Expense group not found")
    db_member = get_member(db, current_user.id, group_id)
    if not db_member:
        raise HttpException(status_code=status.HTTP_403_FORBIDDEN, detail="Only group members can fetch expenses")

    return get_expenses_by_group_id(db, group_id)

@app.get("/groups/{group_id}/expenses/{expense_id}", response_model=ExpenseRead)
def get_expense_by_id(group_id:int, expense_id:int):
    pass

@app.post("/groups/{group_id}/expenses", response_model=ExpenseCreate)
def create_expense(group_id:int):
    pass

@app.put("/groups/{group_id}/expenses/{expense_id}", response_model=ExpenseUpdate)
def update_expense(group_id:int, expense_id:int):
    pass

@app.delete("/groups/{group_id}/expenses/{expense_id}",response_model = ExpenseBase)
def delete_expense{group_id:int, expense_id:int):
    pass                   

#------Recurring Expense Routes-------
@app.get("/groups/{group_id}/expenses/{expense_id}/recurring", response_model = RecurringExpense)
def get_recurring_expense(group_id:int, expense_id:int):
    pass

@app.post("/groups/{group_id}/expenses/{expense_id}/recurring", response_model = RecurringExpense)
def create_recurring_expense(group_id:int, expense_id:int):
    pass

@app.put("/groups/{group_id}/expenses/{expense_id}/recurring", response_model = RecurringExpense)
def update_recurring_expense(group_id:int, expense_id:int):
    pass

@app.delete("/groups/{group_id}/expenses/{expense_id}/recurring", response_model = RecurringExpense)
def delete_recurring_expense(group_id:int, expense_id:int):
    pass

#------Audit Routes-------
@app.get("/groups/{group_id}/audits", response_model = List[AuditRead])
def get_audits(group_id:int, db: SessionDep, current_user: User = Depends(get_user)):
    db_group = get_expense_group(db, group_id)
    if not db_group:
        raise HttpException(status_code=404, detail= "Expense group not found")

    if db_group.admin_id != current_user.id:
        raise HttpException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the group admin can view the audit trail")

    return get_all_audit(db, group_id)
    
