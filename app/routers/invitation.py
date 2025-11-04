from fastapi import APIRouter, status
from schemas import *
from database import *
from auth import UserDep
from crud import *
from services import *

router = APIRouter()



#------Invitation Routes-------

# Route 1: Create an invite to an Expense Group.
@router.post("/groups/{group_id}/invitations", response_model=InvitationDetailsRead, status_code=status.HTTP_201_CREATED)
def invite_member_to_group(group_id: int, invite_data: InvitationCreate, db: SessionDep, current_user: UserDep):
    validate_expense_group(db, group_id, "Expense group not found.")
    validate_group_member(db, current_user.id, group_id, "Only members can send invitations.")
    
    invitee = get_user_by_email(db, email=invite_data.invitee_email)
    if not invitee:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User with this email does not exist.")
    if get_member(db, user_id=invitee.id, group_id=group_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "User is already a member of this group.")
    if get_existing_invitations_for_user(db, group_id, invitee.id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "An invitation is already pending for this user.")

    new_invitation = create_invitation(db, group_id, current_user, invitee_id=invitee.id)\
    
    create_audit(
        db,
        AuditRead(
            change_description= f'Invite sent to {invitee.name} by {current_user.name}.',
            expense_group_id = group_id,
            created_by= current_user.id,
            created_on= datetime.now()
        ),
        group_id,
        current_user
        )
    
    return new_invitation

# Route 2: List all pending invites to the Expense Group.
@router.get("/groups/{group_id}/invitations", response_model=List[InvitationDetailsRead])
def list_group_invitations(group_id: int, db: SessionDep, current_user: UserDep):
    validate_expense_group(db, group_id, "Expense group not found.")
    validate_group_member(db, current_user.id, group_id, "Only members can view group invitations.")
    return get_pending_invitations_for_group(db, group_id)

# Route 3: List all pending invites received for the User.
@router.get("/invitations/me", response_model=List[InvitationDetailsRead])
def list_my_received_invitations(db: SessionDep, current_user: UserDep):
    return get_pending_invitations_for_user(db, current_user.id)

# Route 4: Respond to invite (Accept/Decline)
@router.patch("/invitations/{invitation_id}", response_model=InvitationDetailsRead)
def respond_to_invitation(invitation_id: int, response: InvitationResponse, db: SessionDep, current_user: UserDep):
    invitation = get_invitation_by_token(db, invitation_id)
    if not invitation or invitation.status != InvitationStatus.PENDING:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invitation not found or has expired.")
    if current_user.id != invitation.invitee_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You are not authorized to respond to this invitation.")

    if response.action == InvitationAction.ACCEPT:
        create_member(db, current_user, invitation.expense_group_id, invitation.inviter_id)
        updated_invitation = update_invitation_status(db, invitation, InvitationStatus.ACCEPTED)
    else:
        updated_invitation = update_invitation_status(db, invitation, InvitationStatus.DECLINED)
        
    return updated_invitation

# Route 5: Cancel an invite.
@router.delete("/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_sent_invitation(invitation_id: int, db: SessionDep, current_user: UserDep):
    invitation = get_invitation_by_id(db, invitation_id)
    if not invitation or invitation.status != InvitationStatus.PENDING:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invitation not found or is no longer pending.")
    
    group = get_expense_group(db, invitation.expense_group_id)
    is_admin = group.admin_id == current_user.id
    is_inviter = invitation.inviter_id == current_user.id

    if not is_admin and not is_inviter:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the inviter or group admin can cancel this invitation.")
    
    update_invitation_status(db, invitation, InvitationStatus.CANCELED)

    create_audit(
        db,
        AuditRead(
            change_description= f'Invite for {invitation.invitee.name} canceled by {current_user.name}.',
            expense_group_id = group.id,
            created_by= current_user.id,
            created_on= datetime.now()
        ),
        group.id,
        current_user
        )
    
    return None