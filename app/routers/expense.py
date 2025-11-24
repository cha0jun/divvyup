from fastapi import APIRouter, status, UploadFile, File
from pydantic import Json
from ..schemas import *
from ..database import *
from ..auth import UserDep
from ..crud import *
from ..services import *
import uuid


router = APIRouter(
    prefix="/api/expenses",  # Add api prefix
    tags=["expenses"]
)

#------File upload---------
async def create_receipt(file: UploadFile | None = None):
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= "No uploaded file found.")
     # 1. Define the upload directory
    upload_dir = "./data/images"
    
    # 2. Ensure the directory exists (creates it if it doesn't)
    os.makedirs(upload_dir, exist_ok=True)
    
    # 3. Construct a secure file path
    # Suggestion: Append IDs to filename to prevent overwriting if different users upload files with same names
    ext = Path(file.filename).suffix
    save_filename = str(uuid.uuid4()) + ext
    file_path = os.path.join(upload_dir, save_filename)

    # 4. Save the file
    try:
        with open(file_path, "wb") as buffer:
            # Read the file content asynchronously
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")

    return file_path

#------Expense Routes-------
@router.get("/{group_id}", response_model=List[ExpenseRead])
def get_expenses_bl(group_id:int,  db: SessionDep, current_user: UserDep):
    validate_expense_group(db, group_id, "Expense group not found.")
    validate_group_member(db, current_user.id, group_id, "Only members can view group expenses")
    
    expenses = get_expenses_by_group_id(db, group_id)
    return expenses
    

@router.get("/{expense_id}", response_model=ExpenseRead)
def get_expense_by_id_bl(group_id:int, expense_id:int, db: SessionDep, current_user: UserDep):
    validate_expense_group(db, group_id, "Expense group not found.")
    validate_group_member(db, current_user.id, group_id, "Only members can view group expenses")
    
    e = validate_expense_in_group(db, expense_id, group_id, "Expense not found in this group")

    return e


@router.post("/{group_id}", response_model=ExpenseRead,status_code=status.HTTP_201_CREATED)
async def create_expense_bl(group_id:int, expense:Json[ExpenseCreate], db: SessionDep, current_user: UserDep, file: UploadFile | None = File(None)):
      
    """
    Create a new expense with breakdowns (splits).
    The sum of breakdown amounts must equal the expense amount.
    """
      
    validate_expense_group(db, group_id, "Expense group not found.")
    validate_group_member(db, current_user.id, group_id, "Only members can add group expenses")
    validate_group_member(db, expense.payer_id, group_id, "Payer must be a group member")

    for breakdown in expense.breakdowns:
        validate_group_member(db, breakdown.debtor_id, group_id, "All debtors must be group members")
        
    if file:
        path = await create_receipt(file)
        expense.receipt_path = path
    else:
        print('no file')
    
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
  
@router.patch("/{expense_id}", response_model=ExpenseRead)
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

@router.delete("/{expense_id}/groups/{group_id}",status_code=204)
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

@router.get("/{expense_id}/groups/{group_id}/breakdown", response_model=BreakdownRead)
def get_breakdown(expense_id:int, group_id:int, db:SessionDep, current_user: UserDep):
    validate_expense_group(db, group_id, "Expense group not found.")
    validate_group_member(db, current_user.id, group_id, "Only members can view recurring expenses")
    res = get_breakdown_by_expense_id(db, expense_id)
    return res


#------Recurring Expense Routes-------
@router.get("/{expense_id}/groups/{group_id}/recurring", response_model = RecurringExpenseBase)
def get_recurring_expense_bl(group_id:int, expense_id:int, db: SessionDep, current_user: UserDep):
    validate_expense_group(db, group_id, "Expense group not found.")
    validate_group_member(db, current_user.id, group_id, "Only members can view recurring expenses")
    re = get_recurring_expense(db, expense_id)
    return RecurringExpenseBase(
        frequency= re.frequency,
        start_date= re.start_date,
        end_date= re.end_date
    )

@router.post("/{expense_id}/groups/{group_id}/recurring", response_model = RecurringExpenseBase)
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
    

@router.put("/{expense_id}/groups/{group_id}/recurring", response_model = RecurringExpense)
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
    

@router.delete("/{expense_id}/groups/{group_id}/recurring", response_model = RecurringExpense)
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


