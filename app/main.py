import logging
from fastapi import FastAPI, Depends, HTTPException, status
from typing import List
from models import *
from schemas import *
from database import engine, SessionDep
from crud import *
from services import validate_expense_group, validate_group_member, validate_group_admin, validate_user_exists, add_member_to_group_service, validate_member_exists_in_group
from services import validate_expense_in_group
from auth import*

#Add startup event handler 
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield
    
app = FastAPI(lifespan=lifespan)

#------User Routes-------

@app.post("/token", response_model = Token)
def login(db: SessionDep, login_data: UserLogin):
    user = get_user_by_email(db, email = login_data.email)
    print(user)
    if not user:
        logging.warning(f"--- Login failed: user not found for email {login_data.email} ---")
        raise HTTPException(
            status_code=401,
            detail="Invalid login credentials."
        )

        
    if not verify_password(login_data.password, user.password_hash):
        # Log the failure reason
        logging.warning("--- Password verification failed! ---")
        if user:
            logging.warning(f"--- Password from form: {login_data.password} ---")
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
def register_new_user(db: SessionDep, user: UserCreate):
    "Register a new user "
    is_email_exist = get_user_by_email(db, email = user.email)
    if is_email_exist:
        raise HTTPException(
            status_code = 400, 
            detail = "Email is registered, use another email.")
    new_user = create_user(db, user)
    return new_user

#------Member Routes-------

@app.get("/groups/{group_id}/members", response_model=List[MemberRead])
def read_group_members(
    group_id: int,
    db: SessionDep,
    current_user: UserDep
):
    
    """
    List all members in a specific expense group.
    Only accessible to users who are members of the group.
    """
    validate_expense_group(db, group_id, "Expense group not found")
    validate_group_member(db, current_user.id, group_id, "You are not a member of this group")
    return get_group_members(db, group_id=group_id)


@app.post("/groups/{group_id}/members", response_model=MemberRead, status_code=status.HTTP_201_CREATED)
def add_member(
    group_id: int,
    member_create: MemberCreate, 
    db: SessionDep,
    current_user: UserDep
):
    """
    Add a new member to an expense group.
    Only group admins are allowed to add members.
    """

    validate_expense_group(db, group_id, "Expense group not found")
    performing_admin =validate_group_admin(db, current_user.id, group_id, "Only group admins can add members")
    user_to_add = validate_user_exists(db,member_create.user_id, "User to add not found" )
    new_member = add_member_to_group_service(db, user_to_add, group_id, performing_admin)
    
    create_audit(
        db,
        AuditRead(
            change_description= f' {new_member.name} added to group by {current_user.name}.',
            expense_group_id = group_id,
            created_by= current_user.id,
            created_on= datetime.now()
        ),
        group_id,
        current_user
        )
    
    return new_member
    
    
@app.delete("/groups/{group_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    group_id: int,
    member_id: int,
    db:SessionDep,
    current_user: UserDep
):
    
    """
    Remove a member from a group.
    Only group admins have permission to remove members.
    """

    validate_expense_group(db, group_id, "Expense group not found")
    validate_group_admin( db, current_user.id, group_id,"Only group admins can remove members")
    validate_member_exists_in_group(db, member_id, group_id, "Member not found in this group")
    
    create_audit(
        db,
        AuditRead(
            change_description= f'Member {member_id} removed from group by {current_user.name}.',
            expense_group_id = group_id,
            created_by= current_user.id,
            created_on= datetime.now()
        ),
        group_id,
        current_user
        )
    remove_member_from_group(db, member_id=member_id)

#------Group Routes--------

@app.get("/groups", response_model=List[ExpenseGroupRead])
def read_user_groups(
    db: SessionDep,
    current_user: UserDep
):
    """
    Retrieve all expense groups that the logged-in user is a member of.
    """
    groups = get_groups_for_user(db, current_user.id)

    if not groups:
        # Return empty list instead of raising 404; for users who have no groups
        return []


    group_list = [
        ExpenseGroupRead(
            id=g.id,
            name=g.name,
            description=g.description,
            admin_id = g.admin_id,
            created_on=g.created_on,
            created_by = g.created_by
        )
        for g in groups
    ]

    return group_list

@app.post("/groups", response_model= ExpenseGroupRead, status_code=status.HTTP_201_CREATED)
def create_expense_group(
    group: ExpenseGroupCreate,
    db: SessionDep,
    current_user: UserDep
    ):
    
    """
    Create a new expense group.
    The user who creates the group automatically becomes the first admin member.
    """
    new_group = create_group(db=db, group=group, creator=current_user)

    return ExpenseGroupRead(
        id=new_group.id,
        name=new_group.name,
        description=new_group.description,
        admin_id = new_group.admin_id,
        created_by=new_group.created_by,
        created_on=new_group.created_on
    )

@app.get("/groups/{group_id}", response_model=ExpenseGroupRead)
def read_expense_group(
    group_id: int,
    db: SessionDep,
    current_user: UserDep
):
    """
    Retrieve details of a specific expense group.
    Only accessible if the user is a member of the group.
    """
    db_group =validate_expense_group(db, group_id, error_detail="Expense group not found")
    validate_group_member(db, user_id=current_user.id, group_id=group_id, 
                          error_detail="You are not a member of this group")
 
    return db_group

@app.patch("/groups/{group_id}", response_model=ExpenseGroupRead)
def update_group_details(
    group_id: int,
    group_update: ExpenseGroupUpdate,
    db: SessionDep,
    current_user: UserDep
):
    """
    Update an expense group's name or description.
    Only the group admin can perform this action.
    """
    validate_expense_group(db, group_id, error_detail="Expense group not found")

    validate_group_admin(db, user_id=current_user.id, group_id=group_id,
                         error_detail="Only the group admin can update this group")

    updated_group = update_expense_group(db, group_id=group_id, group_update=group_update, modifier=current_user)
    
    create_audit(
        db,
        AuditRead(
            change_description= f'Group updated by {current_user.name}.',
            expense_group_id = group_id,
            created_by= current_user.id,
            created_on= datetime.now()
        ),
        group_id,
        current_user
        )
    
    return updated_group

@app.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: int,
    db: SessionDep,
    current_user: UserDep
):
    """
    Delete an expense group.
    Only the group admin can delete the group.
    """
    db_group = validate_expense_group(db, group_id, error_detail="Expense group not found")
    validate_group_admin(db, current_user.id, group_id, "Only the group admin can delete this group")
  
    db.delete(db_group)
    db.commit()
    return None

@app.patch("/groups/{group_id}/change-admin", response_model=ExpenseGroupRead)
def change_admin(
    group_id: int,
    transfer_data: TransferOwnership,
    db: SessionDep,
    current_user: UserDep
):
    validate_expense_group(db, group_id, "Expense group not found")
    validate_group_admin(db, current_user.id, group_id, "Only the group owner can transfer ownership")
    validate_group_member(db, transfer_data.new_admin_user_id, group_id, "New admin must be an existing member of the group")

    updated_group = transfer_admin_rights(db, group_id, transfer_data.new_admin_user_id, current_user)

    return updated_group

#------Expense Routes-------
@app.get("/groups/{group_id}/expenses", response_model=List[ExpenseRead])
def get_expenses_bl(group_id:int,  db: SessionDep, current_user: UserDep):
    validate_expense_group(db, group_id, "Expense group not found.")
    validate_group_member(db, current_user.id, group_id, "Only members can view group expenses")
    
    expenses = get_expenses_by_group_id(db, group_id)
    return expenses
    

@app.get("/groups/{group_id}/expenses/{expense_id}", response_model=ExpenseRead)
def get_expense_by_id_bl(group_id:int, expense_id:int, db: SessionDep, current_user: UserDep):
    validate_expense_group(db, group_id, "Expense group not found.")
    validate_group_member(db, current_user.id, group_id, "Only members can view group expenses")
    
    e = validate_expense_in_group(db, expense_id, group_id, "Expense not found in this group")

    return e


@app.post("/groups/{group_id}/expenses", response_model=ExpenseRead,status_code=status.HTTP_201_CREATED)
def create_expense_bl(group_id:int, expense:ExpenseCreate, db: SessionDep, current_user: UserDep):
      
    """
    Create a new expense with breakdowns (splits).
    The sum of breakdown amounts must equal the expense amount.
    """
      
    validate_expense_group(db, group_id, "Expense group not found.")
    validate_group_member(db, current_user.id, group_id, "Only members can add group expenses")
    validate_group_member(db, expense.payer_id, group_id, "Payer must be a group member")

    for breakdown in expense.breakdowns:
        validate_group_member(db, breakdown.debtor_id, group_id, "All debtors must be group members")
    
    created_expense = create_expense(db, expense, group_id,current_user)
    create_audit(
        db,
        AuditRead(
            change_description= f'Expense {expense.name} created by {current_user.name}.',
            expense_group_id = group_id,
            created_by= current_user.id,
            created_on= datetime.now()
        ),
        group_id,
        current_user
        )
    
    return created_expense
  
@app.patch("/groups/{group_id}/expenses/{expense_id}", response_model=ExpenseRead)
def update_expense_bl(group_id:int, expense_id:int, expense: ExpenseUpdate, db: SessionDep, current_user: UserDep):
    validate_expense_group(db, group_id, "Expense group not found.")
    validate_group_member(db, current_user.id, group_id, "Only members can update group expenses")
    
    updated_expense = update_expense(db, expense, expense_id, current_user)
    create_audit(
        db,
        AuditRead(
            change_description= f'Expense {expense.name} updated by {current_user.name}.',
            expense_group_id = group_id,
            created_by= current_user.id,
            created_on= datetime.now()
        ),
        group_id,
        current_user
        )
    
    return updated_expense

@app.delete("/groups/{group_id}/expenses/{expense_id}",status_code=204)
def delete_expense_bl(group_id:int, expense_id:int, db: SessionDep, current_user: UserDep):
    validate_expense_group(db, group_id, "Expense group not found.")
    validate_group_member(db, current_user.id, group_id, "Only members can delete group expenses")
    
    expense = get_expense(db, expense_id)
    delete_expense(db, expense_id)
    
    create_audit(
        db,
        AuditRead(
            change_description= f'Expense {expense.name} deleted by {current_user.name}.',
            expense_group_id = group_id,
            created_by= current_user.id,
            created_on= datetime.now()
        ),
        group_id,
        current_user
        )
    
    return
             
#--------Expense Breakdown Routes------

# @app.post("/groups/{group_id}/expenses/{expense_id}/breakdowns"_)
# def add_breakdown():
#     pass


#------Recurring Expense Routes-------
@app.get("/groups/{group_id}/expenses/{expense_id}/recurring", response_model = RecurringExpenseBase)
def get_recurring_expense_bl(group_id:int, expense_id:int, db: SessionDep, current_user: UserDep):
    validate_expense_group(db, group_id, "Expense group not found.")
    validate_group_member(db, current_user.id, group_id, "Only members can view recurring expenses")
    re = get_recurring_expense(db, expense_id)
    return RecurringExpenseBase(
        frequency= re.frequency,
        start_date= re.start_date,
        end_date= re.end_date
    )

@app.post("/groups/{group_id}/expenses/{expense_id}/recurring", response_model = RecurringExpenseBase)
def create_recurring_expense_bl(group_id:int, expense_id:int, recurring_expense: RecurringExpenseBase , db: SessionDep, current_user: UserDep):
    validate_expense_group(db, group_id, "Expense group not found.")
    validate_group_member(db, current_user.id, group_id, "Only members can add a recurring expense")
    
    created_re = create_recurring_expense(db,recurring_expense, expense_id, current_user)
    e = get_expense(db,expense_id)
    
    create_audit(
        db,
        AuditRead(
            change_description= f'Recurring expense {e.name} created by {current_user.name}.',
            expense_group_id = group_id,
            created_by= current_user.id,
            created_on= datetime.now()
        ),
        group_id,
        current_user
        )
    
    return RecurringExpenseBase(
            frequency = created_re.frequency,
            start_date = created_re.start_date,
            end_date = created_re.end_date
    )
    

@app.put("/groups/{group_id}/expenses/{expense_id}/recurring", response_model = RecurringExpense)
def update_recurring_expense_bl(group_id:int, expense_id:int, recurring_expense: RecurringExpenseBase, db: SessionDep, current_user: UserDep):
    validate_expense_group(db, group_id, "Expense group not found.")
    validate_group_member(db, current_user.id, group_id, "Only members can updated a recurring expense")
    
    updated_re = update_recurring_expense(db, recurring_expense,expense_id, current_user)
    
    create_audit(
        db,
        AuditRead(
            change_description= f'Recurring expense {recurring_expense.name} updated by {current_user.name}.',
            expense_group_id = group_id,
            created_by= current_user.id,
            created_on= datetime.now()
        ),
        group_id,
        current_user
        )
    return RecurringExpense(
            frequency = updated_re.frequency,
            start_date = updated_re.start_date,
            end_date = updated_re.end_date
    )
    

@app.delete("/groups/{group_id}/expenses/{expense_id}/recurring", response_model = RecurringExpense)
def delete_recurring_expense_bl(group_id:int, expense_id:int, db: SessionDep, current_user: UserDep):
    validate_expense_group(db, group_id, "Expense group not found.")
    validate_group_member(db, current_user.id, group_id, "Only members can delete a recurring expense")
    
    re = get_recurring_expense(db, expense_id)
    
    delete_recurring_expense(db, expense_id)
    
    create_audit(
        db,
        AuditRead(
            change_description= f'Recurring expense {re.name} deleted by {re.created_by.name}.',
            expense_group_id = group_id,
            created_by= current_user.id,
            created_on= datetime.now()
        ),
        group_id,
        current_user
        )
    return
    

#------Audit Routes-------
@app.get("/groups/{group_id}/audits", response_model = List[AuditRead])
def get_audits_bl(group_id:int, db: SessionDep, current_user: UserDep):
    validate_expense_group(db, group_id, "Expense group not found")
    validate_group_admin(db, current_user.id, group_id, "Only the group admin can view the audit trail")
    
    aud_list = get_all_audit(db, group_id)
    
    out = [
        AuditRead(
            change_description = a.change_description,
        ) for a in aud_list
    ]
    
    return out
    
#------Balance Summary Route-------

@app.get("/groups/{group_id}/balances", response_model = GroupBalanceResponse)
def get_group_balances(group_id: int, db: SessionDep, current_user: UserDep):
    validate_expense_group(db, group_id, error_detail="Expense group not found")
    group = get_expense_group(db, group_id)
    group_balances = calculate_group_balances(group)

    return group_balances