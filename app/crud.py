from fastapi import HTTPException, status
from .models import *
from sqlmodel import Session, select, text
from .schemas import *
from typing import List, Optional
from datetime import datetime, timezone
from .security import hash_password
from collections import defaultdict
from sqlalchemy.orm import selectinload
from sqlalchemy import delete

#----User------
def get_user_by_id(db: Session, id: int) -> User | None:
    return db.exec(select(User).where(User.id == id)).first()
    

def get_user_by_email(db: Session, email: str) -> User | None:
    query = select(User).where(User.email == email)
    user = db.exec(query).first()
    return user


# handles user    between app and db


def create_user(db: Session, user: UserCreate):
    if get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")

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
                (Member.user_id == user_id) &
                (Member.expense_group_id == group_id)
            )
        ).first()
    
def get_member_by_member_id(db: Session, member_id: int)-> Member | None:
    return db.exec(
            select(Member).where(
                Member.id == member_id)).first()

def create_member(db: Session, user_to_add: User, group_id: int, added_by_user_id: int) -> Member:
    """Creates a new member in a group."""
    inviter_is_member = get_member(db, user_id=added_by_user_id, group_id=group_id)
    if not inviter_is_member:
        # Check if Invter is from the Expense Group.
        raise HTTPException(status_code=404, detail="Inviter is not a member of the group.")

    member = Member(
        user_id=user_to_add.id, 
        expense_group_id=group_id, 
        added_by=inviter_is_member.id
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    db.refresh(member, ["user"])
    return member


def remove_member_from_group(db: Session, db_member: Member):
    """
    Deletes a given Member object from the database and commits the session.
    """
    db.delete(db_member)
    db.commit()


def get_group_members(db: Session, group_id: int) -> List[Member]:
    """Retrieve all members of a group."""
    statement = select(Member, User).where(
        (Member.expense_group_id == group_id) &
        (Member.user_id == User.id)
    ) #JOIN user table ON member.user_id = user.id

    results = db.exec(statement).all()
    return [MemberRead(
            id=member.id,
            user=UserRead(id=user.id, name=user.name, email=user.email),
            added_on=member.added_on
        )
        for member, user in results
    ]


#----ExpenseGroup------

def get_expense_group(db: Session, group_id: int) -> Optional[ExpenseGroup]:
    return db.exec(
        select(ExpenseGroup).where(ExpenseGroup.id == group_id)
    ).first()

def get_groups_for_user(db: Session, user_id: int):
    # Query ExpenseGroup where user is admin or a member

    # Get all group IDs where the user is a member
    member_group_ids = db.exec(
        select(Member.expense_group_id).where(Member.user_id == user_id)
    ).all()

    groups = db.exec(
        select(ExpenseGroup)
        .where(
            (ExpenseGroup.admin_id == user_id) |
            (ExpenseGroup.id.in_(member_group_ids))
            )
    ).all()
    return groups


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
    
    if group_update.name:
        db_group.name = group_update.name.strip()

    if group_update.description:
        db_group.description = group_update.description.strip()

    db_group.modified_by = modifier.id
    db_group.modified_on = datetime.now()
    db.add(db_group)
    
    db.commit()
    db.refresh(db_group)
    return db_group


def transfer_admin_rights(db: Session, group_id: int, new_admin_user_id: int, modifier: User) -> ExpenseGroup:
    db_group = get_expense_group(db, group_id)
    db_group.admin_id = new_admin_user_id
    db_group.modified_by = modifier.id
    db_group.modified_on = datetime.now()

    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

#-----------Audit-------------------
def get_all_audit(db: Session, group_id: int) -> List[Audit]:
    return db.exec(
        select(Audit).where(Audit.expense_group_id == group_id)
    )

def create_audit(db: Session, audit:AuditRead, group_id : int, created_by: User) -> Audit | None:
    new_audit = Audit(
        change_description = audit.change_description,
        expense_group_id = group_id,
        created_by = created_by.id,
        created_on = datetime.now(),         
    )
    
    db.add(new_audit)
    db.commit()
    db.refresh(new_audit)
    return new_audit

#-----------Expense-----------------
def get_expense(db: Session, expense_id:int ) -> Expense:
    return db.exec(
        select(Expense).where(Expense.id == expense_id)
    ).first()

def get_expenses_by_group_id(db: Session, group_id:int) -> List[Expense]:
    return db.exec(
        select(Expense).where(Expense.expense_group_id == group_id)).all()
    
def get_expense_by_group_id(db: Session, group_id:int) -> List[Expense]:
    return db.exec(
        select(Expense).where(Expense.expense_group_id == group_id)
    )
    
def create_expense(db: Session, expense: ExpenseCreate, group_id:int, creator: User) -> Expense | None:
    new_expense = Expense(
        expense_group_id=group_id,
        name = expense.name,
        amount = expense.amount,
        payment_date = expense.payment_date,
        payer_id = expense.payer_id, # nested object => UserRead
        description = expense.description,
        receipt_path = expense.receipt_path,
        created_by = creator.id,
        # created_on = datetime.now(),
        modified_by = creator.id,
        # modified_on = datetime.now() 
    )
    
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    
    #create the breakdowns
    for breakdown_data in expense.breakdowns:
        create_breakdown(
            db=db,
            breakdown=breakdown_data,
            expense_id=new_expense.id,
            created_by=creator
        )
    
    db.refresh(new_expense)
    return new_expense


def update_expense(db: Session, expense: ExpenseUpdate, expense_id: int, modified_by:User) -> Expense | None:
    db_expense = get_expense(db, expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    if expense.name is not None:
        db_expense.name = expense.name
    if expense.amount is not None:
        db_expense.amount = expense.amount
    if expense.payment_date is not None:
        db_expense.payment_date = expense.payment_date
    if expense.payer_id is not None:
        db_expense.payer_id = expense.payer_id
    if expense.description is not None:
        db_expense.description = expense.description
    if expense.receipt_path is not None:
        db_expense.receipt_path = expense.receipt_path
    
    if getattr(expense, "breakdowns", None) is not None:
        # Delete all old breakdowns for this expense
        for old_breakdown in db_expense.breakdowns:
            db.delete(old_breakdown)


        # Create the new breakdowns from the request
        for breakdown_data in expense.breakdowns:
            create_breakdown(
                db=db,
                breakdown=breakdown_data,
                expense_id=db_expense.id,
                created_by=modified_by
            )
    
    db_expense.modified_by = modified_by.id
    # db_expense.modified_on = datetime.now()
    
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
        select(RecurringExpense).where(RecurringExpense.expense_id == expense_id)
    ).first()

## creation of recurring expense to be a 2 step process (expense created in db first followed by recurring), enforced in BL
def create_recurring_expense(db: Session, expense: RecurringExpenseBase, expense_id:int, creator: User) -> RecurringExpense | None:
    db_expense = get_expense(db, expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    new_recurring_expense = RecurringExpense(
        expense_id = expense_id,
        frequency = expense.frequency,
        start_date = expense.start_date,
        end_date = expense.end_date,
        created_by = creator.id,
        created_on = datetime.now(),
        modified_by = creator.id,
        modified_on = datetime.now()
    )
    
    db.add(new_recurring_expense)
    db.commit()
    db.refresh(new_recurring_expense)
    return new_recurring_expense

def update_recurring_expense(db: Session, expense: RecurringExpenseBase, expense_id: int, modified_by: User) -> RecurringExpense | None:
    db_recurring_expense = get_recurring_expense(db, expense_id)
    if not db_recurring_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    if expense.frequency is not None:
        db_recurring_expense.frequency = expense.frequency
    if expense.start_date is not None:
        db_recurring_expense.start_date = expense.start_date
    if expense.end_date is not None:
        db_recurring_expense.end_date = expense.end_date
    
    db_recurring_expense.modified_by = modified_by.id
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
    ).first()

    
def get_breakdown_by_expense_id(db: Session, expense_id:int) -> List[Breakdown]:
    return db.exec(
        select(Breakdown).where(Breakdown.expense_id == expense_id)
    ).all

def create_breakdown(db: Session, breakdown:BreakdownBase, expense_id: int, created_by: User) -> Breakdown | None:
    new_breakdown = Breakdown(
        expense_id = expense_id,
        amount =  breakdown.amount,
        debtor_id = breakdown.debtor_id,
        created_by = created_by.id,
        modified_by = created_by.id
    )
    
    db.add(new_breakdown)
    db.commit()
    db.refresh(new_breakdown)
    return new_breakdown

def update_breakdown(db: Session, breakdown:BreakdownBase, breakdown_id:int, modified_by: User) -> Breakdown:
    db_breakdown = get_breakdown(db, breakdown_id)
    if not db_breakdown:
        raise HTTPException(status_code=404,detail= "Breakdown not found")
    
    if breakdown.amount is not None:
        db_breakdown.amount = breakdown.amount
    if breakdown.debtor_id is not None:
        db_breakdown.debtor_id = breakdown.debtor_id
    
    # db_breakdown.modified_on = datetime.now()
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

#--------------Payment---------------
def get_payments_by_group_id(db: Session, group_id:int) -> List[Payment]:
    return db.exec(
        select(Payment).where(Payment.expense_group_id == group_id)).all()

def get_payment(db: Session, payment_id:int ) -> Payment:
    return db.exec(
        select(Payment).where(Payment.id == payment_id)
    ).first()

def create_payment(db: Session, payment: PaymentCreate, group_id:int, creator: User) -> Payment | None:
    new_payment = Payment(
        expense_group_id=group_id,
        amount = payment.amount,
        payment_date = payment.payment_date,
        payer_id = payment.payer_id,
        payee_id = payment.payee_id,
        created_by = creator.id,
        # created_on = datetime.now(),
        modified_by = creator.id)
        # modified_on = datetime.now()
    
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment, ["payer", "payee"])

    return new_payment
    
def update_payment(db: Session, payment: PaymentUpdate, payment_id: int, modified_by:User) -> Payment | None:
    db_payment = get_payment(db, payment_id)
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment not found")
 
    if payment.amount is not None:
        db_payment.amount = payment.amount
    if payment.payer_id is not None:
        db_payment.payer_id = payment.payer_id
    if payment.payee_id is not None:
        db_payment.payee_id = payment.payee_id

    db_payment.modified_by = modified_by.id
    # db_payment.modified_on = datetime.now()
    
    db.commit()
    db.refresh(db_payment)
    return db_payment

def delete_payment(db: Session, payment_id: int) -> None:
    db_payment = get_payment(db, payment_id)
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    db.delete(db_payment)
    db.commit()
    return





#--------------Balance Calculation---------------

def calculate_group_balances(group: ExpenseGroup) -> GroupBalanceResponse:
    
    #agrregate all debts
    raw_debts = {}
    for expense in group.expenses:
        payer_id = expense.payer_id
        for split in expense.breakdowns:
            debtor_id = split.debtor_id
            if payer_id != debtor_id:
                key = (debtor_id, payer_id)
                raw_debts[key] = raw_debts.get(key, 0.0) + split.amount

    # Subtract payments from raw_debts
    for payment in group.payments:  
        key = (payment.payer_id, payment.payee_id)  
        raw_debts[key] = raw_debts.get(key, 0.0) - payment.amount
    

    #offset mutual debts
    final_balances = {} #{(debtor_id, payer_id):  amount}
    member_ids = [m.user_id for m in group.members]
    for i, memberA_id in enumerate(member_ids):
        for memberB_id in member_ids[i+1:]:
            debt_AowesB = raw_debts.get((memberA_id, memberB_id), 0)
            debt_BowesA = raw_debts.get((memberB_id, memberA_id), 0)

            if not (debt_AowesB or debt_BowesA):
                continue

            mutual_debt = min( debt_AowesB, debt_BowesA)
            if mutual_debt > 0:
                debt_AowesB -= mutual_debt
                debt_BowesA -= mutual_debt
            
            if debt_AowesB >0 :
                final_balances[(memberA_id, memberB_id)] = round(debt_AowesB, 2)

            if debt_BowesA > 0:
                final_balances[(memberB_id, memberA_id)] = round(debt_BowesA, 2)

    
    #build UserBalance objects for each member for API response
 
    member_names = {m.user_id: m.user.name for m in group.members}

    debts_by_debtor = defaultdict(dict)    # {debtor_id: {creditor_id: amount}}
    debts_by_creditor = defaultdict(dict)  # {creditor_id: {debtor_id: amount}}
    for (debtor_id, creditor_id), amount in final_balances.items():
        debts_by_debtor[debtor_id][creditor_id] = amount
        debts_by_creditor[creditor_id][debtor_id] = amount

    user_balances = {}

    for member in group.members:
        member_id = member.user_id
        member_name = member.user.name
        
         # Find debts this member owes
        owes = {} # {creditor_name: amount}
        if member_id in debts_by_debtor:
            for creditor_id, amount in debts_by_debtor[member_id].items():
                creditor_name = member_names.get(creditor_id)
                if creditor_name:
                    owes[creditor_name] = round(amount, 2)

                
        # Find debts owed to this member
        owed_by = {}  # {debtor_name: amount}
        if member_id in debts_by_creditor:
            for debtor_id, amount in debts_by_creditor[member_id].items():
                debtor_name = member_names.get(debtor_id)
                if debtor_name:
                    owed_by[debtor_name] = round(amount, 2)
    
        
        #calculate net balance
        total_owed = sum(owes.values())
        total_receivable = sum(owed_by.values())
        net_balance = total_receivable - total_owed
        
        user_balances[member_name] = UserBalance(
            owes=owes,
            owed_by=owed_by,
            net_balance=round(net_balance, 2)
        )
    
    return GroupBalanceResponse(balances=user_balances)

#--------------Invitation---------------
def create_invitation(db: Session, group_id: int, inviter: User, invitee_id: int) -> Invitation:
    """Creates a new invitation record."""
    new_invitation = Invitation(
        expense_group_id=group_id,
        inviter_id=inviter.id,
        invitee_id=invitee_id
    )
    db.add(new_invitation)
    db.commit()
    db.refresh(new_invitation)
    return new_invitation

def get_invitation_by_id(db: Session, invitation_id: int) -> Invitation | None:
    """Retrieve invitation record by Id."""
    return db.exec(select(Invitation).where(Invitation.id == invitation_id)).first()

def get_invitation_by_token(db: Session, invitation_id: str) -> Invitation | None:
    """Retrieve invitation record by token."""
    return db.exec(select(Invitation).where(Invitation.id == invitation_id)).first()

def get_pending_invitations_for_group(db: Session, group_id: int) -> List[Invitation]:
    """Retrieves all pending invitations for an Expense Group."""
    statement = (
        select(Invitation)
        .where(Invitation.expense_group_id == group_id, Invitation.status == InvitationStatus.PENDING)
        .options(selectinload(Invitation.group), selectinload(Invitation.inviter), selectinload(Invitation.invitee))
    )
    return db.exec(statement).all()
    
def get_pending_invitations_for_user(db: Session, user_id: int) -> List[Invitation]:
    """Retrieves all pending invitations for a User."""
    statement = (
        select(Invitation)
        .where(Invitation.invitee_id == user_id, Invitation.status == InvitationStatus.PENDING)
        .options(selectinload(Invitation.group), selectinload(Invitation.inviter), selectinload(Invitation.invitee))
    )
    return db.exec(statement).all()

def get_existing_invitations_for_user(db: Session, group_id: int, invitee_id: int) -> Invitation | None:
    """Checks if a user already has existing pending invite for an Expense Group. Validation for duplicated invites."""
    statement = select(Invitation).where(
        Invitation.expense_group_id == group_id,
        Invitation.invitee_id == invitee_id,
        Invitation.status == InvitationStatus.PENDING
    )
    return db.exec(statement).first()

def update_invitation_status(db: Session, invitation: Invitation, new_status: InvitationStatus) -> Invitation:
    invitation.status = new_status
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation

#--------------Blocklist---------------

def add_token_to_blocklist(db: Session, jti: str, expiry_dt: datetime):
    """Add token to blocklist upon log out and delete records of any expired token from table."""
    try:
        expired_tokens = delete(TokenBlockList).where(
            TokenBlockList.expiry_dt < datetime.now(timezone.utc)
        )
        db.exec(expired_tokens)

    except Exception as e:
        print(f"Error deleting records: {e}")
        db.rollback()

    blocklisted_token = TokenBlockList(jti = jti, expiry_dt = expiry_dt)
    db.add(blocklisted_token)
    db.commit()
    db.refresh(blocklisted_token)
    return blocklisted_token

def is_token_blocked(db: Session, jti: str) -> bool:
    """Check if token is in the blocklist."""
    token = db.exec(
        select(TokenBlockList).where(TokenBlockList.jti == jti)
    ).first()
    return token is not None
