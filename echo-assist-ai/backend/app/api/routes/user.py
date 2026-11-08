from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.auth import ProfileResponse, ProfileUpdateRequest
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/user", tags=["user"])


def _profile_response(user: User, profile: UserProfile | None) -> ProfileResponse:
    return ProfileResponse(
        id=user.id, full_name=user.full_name, email=user.email,
        preferred_language=user.preferred_language, phone_number=user.phone_number,
        role=user.role, is_verified=user.is_verified,
        profile_photo_url=profile.profile_photo_url if profile else None,
        date_of_birth=profile.date_of_birth.isoformat() if profile and profile.date_of_birth else None,
        address=profile.address if profile else None,
        medical_accessibility_preferences=profile.medical_accessibility_preferences if profile else None,
    )


@router.get("/profile", response_model=ProfileResponse)
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    return _profile_response(current_user, profile)


@router.put("/profile", response_model=ProfileResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    update_data = payload.model_dump(exclude_unset=True)
    for field in ("full_name", "preferred_language", "phone_number"):
        if field in update_data:
            setattr(current_user, field, update_data[field])
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
    for field in ("profile_photo_url", "address", "medical_accessibility_preferences"):
        if field in update_data:
            setattr(profile, field, update_data[field])
    if "date_of_birth" in update_data:
        try:
            profile.date_of_birth = date.fromisoformat(update_data["date_of_birth"]) if update_data["date_of_birth"] else None
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="date_of_birth must be YYYY-MM-DD") from exc

    db.commit()
    db.refresh(current_user)
    db.refresh(profile)
    return _profile_response(current_user, profile)
