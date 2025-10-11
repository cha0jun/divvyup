from fastapi import HTTPException, status
from models import Member, ExpenseGroup, User
from sqlmodel import Session, select
from schemas import MemberUpdate, ExpenseGroupCreate, ExpenseGroupUpdate
from typing import List, Optional
from datetime import datetime


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

def remove_member_from_group(db: Session, member_id: int)-> Member:
    db_member = get_member_by_member_id(db,member_id)
    if not db_member:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(db_member)
    db.commit()
    return db_member

def update_member_role(db: Session, member_id: int,member_update: MemberUpdate)-> Member:
    db_member = get_member_by_member_id(db, member_id=member_id)
    if not db_member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    db_member.is_admin = member_update.is_admin
    db.commit()
    db.refresh(db_member)
    return db_member

def get_group_members(db: Session, group_id: int) -> List[Member]:
    """Retrieve all members of a group."""
    return db.exec(select(Member).where(Member.expense_group_id == group_id)).all()


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

