from fastapi import APIRouter, status
from ..schemas import *
from ..database import *
from ..auth import UserDep
from ..crud import *
from ..services import *

router = APIRouter(
    prefix="/api/groups", 
    tags=["payments"]
)

#------Payment Routes-------

@router.get("/{group_id}/payments", response_model=List[PaymentRead])
def get_payments(group_id:int,  db: SessionDep, current_user: UserDep):
    validate_expense_group(db, group_id, "Expense group not found.")
    validate_group_member(db, current_user.id, group_id, "Only members can view group expenses")
    
    payments = get_payments_by_group_id(db, group_id)
    return payments

@router.post("/{group_id}/payments", response_model=PaymentRead,status_code=status.HTTP_201_CREATED)
def create_payment_bl(group_id:int, payment:PaymentCreate, db: SessionDep, current_user: UserDep):
    
    """
    Create a new payment
    """  
    validate_expense_group(db, group_id, "Expense group not found.")
    validate_group_member(db, current_user.id, group_id, "Only members can add group payments")
    validate_group_member(db, payment.payee_id, group_id, "Payee must be a group member")
    created_payment = create_payment(db, payment, group_id,current_user)

    payer_name = created_payment.payer.name
    payee_name = created_payment.payee.name

    create_audit(
        db,
        AuditRead(
            change_description= f'Payment of {created_payment.amount} was made by {payer_name} to {payee_name} on {created_payment.payment_date}.',
            expense_group_id = group_id,
            created_by= current_user.id,
            created_on= datetime.now()
        ),
        group_id,
        current_user
        )
    
    return created_payment

@router.patch("/{group_id}/payments/{payment_id}", response_model=PaymentRead)
def update_payment_bl(group_id:int, payment_id:int, payment: PaymentUpdate, db: SessionDep, current_user: UserDep):
    validate_expense_group(db, group_id, "Expense group not found.")
    validate_group_member(db, current_user.id, group_id, "Only members can update group payments")
    
    updated_payment = update_payment(db, payment, payment_id, current_user)
    create_audit(
        db,
        AuditRead(
            change_description= f'Payment {payment_id} updated by {current_user.name}.', #Should use payment name instead?
            expense_group_id = group_id,
            created_by= current_user.id,
            created_on= datetime.now()
        ),
        group_id,
        current_user
        )
    
    return updated_payment

@router.delete("/{group_id}/payments/{payment_id}",status_code=204)
def delete_payment_bl(group_id:int, payment_id:int, db: SessionDep, current_user: UserDep):
    validate_expense_group(db, group_id, "Expense group not found.")
    validate_group_member(db, current_user.id, group_id, "Only members can delete group payments")
    
    delete_payment(db, payment_id)
    
    create_audit(
        db,
        AuditRead(
            change_description= f'Payment {payment_id} deleted by {current_user.name}.',
            expense_group_id = group_id,
            created_by= current_user.id,
            created_on= datetime.now()
        ),
        group_id,
        current_user
        )
    
    return