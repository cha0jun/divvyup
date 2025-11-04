from fastapi import APIRouter, status
from schemas import *
from database import *
from auth import UserDep
from crud import *
from services import *
router = APIRouter(
    tags= ["groups"]
)

#------Member Routes-------

@router.get("/groups/{group_id}/members", response_model=List[MemberRead])
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


@router.post("/groups/{group_id}/members", response_model=MemberRead, status_code=status.HTTP_201_CREATED)
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
            change_description= f' {user_to_add.name} added to group by {current_user.name}.',
            expense_group_id = group_id,
            created_by= current_user.id,
            created_on= datetime.now()
        ),
        group_id,
        current_user
        )
    
    return new_member
    

    
@router.delete("/groups/{group_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
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

@router.get("/groups", response_model=List[ExpenseGroupRead])
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

@router.post("/groups", response_model= ExpenseGroupRead, status_code=status.HTTP_201_CREATED)
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

@router.get("/groups/{group_id}", response_model=ExpenseGroupRead)
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

@router.patch("/groups/{group_id}", response_model=ExpenseGroupRead)
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

@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
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

@router.patch("/groups/{group_id}/change-admin", response_model=ExpenseGroupRead)
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


#------Audit Routes-------
@router.get("/groups/{group_id}/audits", response_model = List[AuditRead])
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

@router.get("/groups/{group_id}/balances", response_model = GroupBalanceResponse)
def get_group_balances(group_id: int, db: SessionDep, current_user: UserDep):
    validate_expense_group(db, group_id, error_detail="Expense group not found")
    group = get_expense_group(db, group_id)
    group_balances = calculate_group_balances(group)

    return group_balances