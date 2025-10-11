from fastapi import HTTPException, status
from models import Member, ExpenseGroup, User
from sqlmodel import Session, select
from schemas import MemberUpdate

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
