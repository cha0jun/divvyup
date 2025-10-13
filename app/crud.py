from fastapi import HTTPException, status, Depends
from .models import *
from sqlmodel import Session, select
from .schemas import *
from typing import List, Optional, Annotated
from datetime import datetime
from .database import SessionDep
from .auth import *

#----User------
def get_user(db: Session, email: str) -> User | None:
    query = select(User).where(User.email == email)
    user = db.exec(query).first()
    if user is None:
        False
    return user
# handles user    between app and db
UserDep = Annotated[User, Depends(get_user)]

def create_user(db: Session, user: UserCreate):
    hashed_pw = hash_password(user.password)
    new_user = User(name = user.name, email = user.email, password_hash = hashed_pw)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

#----Member------

def get_member(db: Session, user_id: int, group_id: int)-> Member | None:
    return db.exec(
            select(Member).where(
                Member.user_id == user_id,
                Member.expense_group_id == group_id
            )
        ).first()
    
def get_member_by_member_id(db: Session, member_id: int)-> Member | None:
    return db.exec(
            select(Member).where(
                Member.id == member_id)).first()

def add_member_to_group(db: Session, group_id: int, user_to_add: User, performing_admin: Member)-> Member:
    existing_member = get_member(db, user_to_add.id,group_id )
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this group"
        )
    
    new_member = Member(
                user_id=user_to_add.id,
                expense_group_id=group_id,
                is_admin=False, # New members are not admins by default
                added_by=performing_admin.id
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member

def remove_member_from_group(db: Session, member_id: int, group_id: int)-> Member:
    db_member = get_member_by_member_id(db,member_id)
    if not db_member:
        raise HTTPException(status_code=404, detail="Member not found")
    if db_member.expense_group_id != group_id:
        raise HTTPException(
            status_code=404,
            detail="Member not found in this group"
        )
    db.delete(db_member)
    db.commit()
    return db_member

def update_member_role(db: Session, member_id: int,group_id: int, member_update: MemberUpdate)-> Member:
    db_member = get_member_by_member_id(db, member_id=member_id)
    if not db_member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    if db_member.expense_group_id != group_id:
        raise HTTPException(
            status_code=404,
            detail="Member not found in this group"
        )
    
    db_member.is_admin = member_update.is_admin
    db.commit()
    db.refresh(db_member)
    return db_member

def get_group_members(db: Session, group_id: int) -> List[Member]:
    """Retrieve all members of a group."""
    statement = select(Member, User).where(
        Member.expense_group_id == group_id,
        Member.user_id == User.id
    ) #JOIN user table ON member.user_id = user.id

    results = db.exec(statement).all()
    return [MemberRead(
            id=member.id,
            is_admin=member.is_admin,
            user=UserRead(id=user.id, name=user.name, email=user.email),
            created_on=member.added_on
        )
        for member, user in results
    ]


#----ExpenseGroup------

def get_expense_group(db: Session, group_id: int) -> Optional[ExpenseGroup]:
    return db.exec(
        select(ExpenseGroup).where(ExpenseGroup.id == group_id)
    ).first()

def create_group(db: Session, group: ExpenseGroupCreate, creator: User) -> ExpenseGroup:
    new_group = ExpenseGroup(
        name=group.name,
        description=group.description,
        admin_id=creator.id,
        created_by=creator.id,
        modified_by=creator.id,
        created_on=datetime.now(),
        modified_on=datetime.now()
    )

    db.add(new_group)
    db.commit()
    db.refresh(new_group)

    # Automatically add the creator as the first admin member
    creator_member = Member(
        user_id=creator.id,
        expense_group_id=new_group.id,
        is_admin=True,
        added_by =None, # The creator isn't added by another member, so this is None
        added_on=datetime.now()
        )
    db.add(creator_member)
    db.commit()
    return new_group

def update_expense_group(db: Session, group_id: int, group_update: ExpenseGroupUpdate, modifier: User) -> ExpenseGroup:
    db_group = get_expense_group(db, group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Expense group not found")
    
    if group_update.name is not None:
        db_group.name = group_update.name
    if group_update.description is not None:
        db_group.description = group_update.description

    db_group.modified_by = modifier.id
    db_group.modified_on = datetime.now()
    
    db.commit()
    db.refresh(db_group)
    return db_group

def delete_expense_group(db: Session, group_id: int) -> ExpenseGroup:
    db_group = get_expense_group(db, group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Expense group not found")
    
    db.delete(db_group)
    db.commit()
    return db_group


#-----------Audit-------------------
def get_all_audit(db: Session, group_id: int) -> List[Audit]:
    return db.exec(
        select(Audit).where(Audit.expense_group_id == group_id)
    )

def create_audit(db: Session, audit:AuditRead, group_id : int) -> Audit | None:
    new_audit = Audit(
        change_description = audit.change_description,
        expense_group_id = group_id,
        created_by = audit.created_by.id,
        created_on = audit.created_on,         
    )
    
    db.add(new_audit)
    db.commit()
    db.refresh(new_audit)
    return new_audit

#-----------Expense-----------------
def get_expense(db: Session, expense_id:int) -> Expense:
    return db.exec(
        select(Expense).where(Expense.id == expense_id).first()
    )

def get_expenses_by_group_id(db: Session, group_id:int) -> List[Expense]:
    return db.exec(
        select(Expense).where(Expense.group_id == group_id)
    )
    
def create_expense(db: Session, expense: ExpenseCreate, group_id:int) -> Expense | None:
    new_expense = Expense(
        expense_group_id=group_id,
        name = expense.name,
        amount = expense.amount,
        payment_date = expense.payment_date,
        payer_id = expense.payer.id, # nested object => UserRead
        description = expense.description,
        created_by = expense.created_by.id,
        created_on = datetime.now(),
        modified_by = expense.modified_by.id,
        modified_on = datetime.now() 
    )
    
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense

def update_expense(db: Session, expense: ExpenseUpdate, expense_id: int) -> Expense | None:
    db_expense = get_expense(db, expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    if expense.name is not None:
        db_expense.name = expense.name
    if expense.amount is not None:
        db_expense.amount = expense.amount
    if expense.payment_date is not None:
        db_expense.payment_date = expense.payment_date
    if expense.payer.id is not None:
        db_expense.payer_id = expense.payer.id
    if expense.description is not None:
        db_expense.description = expense.description
    
    db_expense.modified_by = expense.modified_by.id
    db_expense.modified_on = datetime.now()
    
    db.commit()
    db.refresh(db_expense)
    return db_expense

def delete_expense(db: Session, expense_id: int) -> None:
    db_expense = get_expense(db, expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    db.delete(db_expense)
    db.commit()
    return

#------------- Recurring Expense---------------
def get_recurring_expense(db: Session, expense_id:int) -> RecurringExpense:
    return db.exec(
        select(RecurringExpense).where(RecurringExpense.id == expense_id).first()
    )

## creation of recurring expense to be a 2 step process (expense created in db first followed by recurring), enforced in BL
def create_recurring_expense(db: Session, expense: RecurringExpenseBase, group_id:int, expense_id:int) -> RecurringExpense | None:
    db_expense = get_expense(db, expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    new_recurring_expense = RecurringExpense(
        expense_id = expense_id,
        frequency = expense.frequency,
        start_date = expense.start_date,
        end_date = expense.end_date,
        created_by = expense.created_by.id,
        created_on = datetime.now(),
        modified_by = expense.modified_by.id,
        modified_on = datetime.now()
    )
    
    db.add(new_recurring_expense)
    db.commit()
    db.refresh(new_recurring_expense)
    return new_recurring_expense

def update_expense(db: Session, expense: RecurringExpenseBase, expense_id: int) -> RecurringExpense | None:
    db_recurring_expense = get_recurring_expense(db, expense_id)
    if not db_recurring_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    if expense.frequency is not None:
        db_recurring_expense.frequency = expense.frequency
    if expense.start_date is not None:
        db_recurring_expense.start_date = expense.start_date
    if expense.end_date is not None:
        db_recurring_expense.end_date = expense.end_date
    
    db_recurring_expense.modified_by = expense.modified_by.id
    db_recurring_expense.modified_on = datetime.now()
    
    db.commit()
    db.refresh(db_recurring_expense)
    return db_recurring_expense

def delete_recurring_expense(db: Session, expense_id: int) -> None:
    db_expense = get_recurring_expense(db, expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    db.delete(db_expense)
    db.commit()
    return

#--------------Breakdown---------------
def get_breakdown(db: Session, breakdown_id:int) -> Breakdown:
    return db.exec(
        select(Breakdown).where(Breakdown.id == breakdown_id)
    )

def get_breakdown_by_expense_id(db: Session, expense_id:int) -> List[Breakdown]:
    return db.exec(
        select(Breakdown).where(Breakdown.expense_id == expense_id)
    )

def create_breakdown(db: Session, breakdown:BreakdownBase, expense_id: int, created_by: UserRead) -> Breakdown | None:
    new_breakdown = Breakdown(
        expense_id = expense_id,
        amount =  breakdown.amount,
        paid_by_id = breakdown.paid_by.id,
        created_by = created_by.id,
        created_on = datetime.now(),
        modified_by = created_by.id,
        modified_on = datetime.now()
    )
    
    db.add(new_breakdown)
    db.commit()
    db.refresh(new_breakdown)
    return new_breakdown

def update_breakdown(db: Session, breakdown:BreakdownBase, breakdown_id:int, modified_by: UserRead) -> Breakdown:
    db_breakdown = get_breakdown(db, breakdown_id)
    if not db_breakdown:
        raise HTTPException(status_code=404,detail= "Breakdown not found")
    
    if breakdown.amount is not None:
        db_breakdown.amount = breakdown.amount
    if breakdown.paid_by is not None:
        db_breakdown.paid_by_id = breakdown.paid_by.id
    
    db_breakdown.modified_on = datetime.now()
    db_breakdown.modified_by = modified_by.id
    
    db.commit()
    db.refresh(db_breakdown)
    return db_breakdown
    

def delete_breakdown(db: Session, breakdown_id: int) -> None:
    db_breakdown = get_breakdown(db, breakdown_id)
    if not db_breakdown:
        raise HTTPException(status_code=404, detail="Breakdown not found")
    
    db.delete(db_breakdown)
    db.commit()
    
    return
