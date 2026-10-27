from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.contact import EmergencyContact
from app.models.user import User
from app.schemas.contact import ContactCreateRequest, ContactResponse, ContactUpdateRequest
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("", response_model=list[ContactResponse])
def list_contacts(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return (
        db.query(EmergencyContact)
        .filter(EmergencyContact.user_id == current_user.id)
        .all()
    )


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact(
    payload: ContactCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = payload.model_dump()
    # Map 'relationship' field to 'relationship_type' for database model
    if 'relationship' in data:
        data['relationship_type'] = data.pop('relationship')
    contact = EmergencyContact(user_id=current_user.id, **data)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def _get_owned_contact(contact_id: int, current_user: User, db: Session) -> EmergencyContact:
    contact = db.get(EmergencyContact, contact_id)
    if not contact or contact.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: int,
    payload: ContactUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = _get_owned_contact(contact_id, current_user, db)
    update_data = payload.model_dump(exclude_unset=True)
    # Map 'relationship' field to 'relationship_type' for database model
    if 'relationship' in update_data:
        update_data['relationship_type'] = update_data.pop('relationship')
    for field, value in update_data.items():
        setattr(contact, field, value)
    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = _get_owned_contact(contact_id, current_user, db)
    db.delete(contact)
    db.commit()
