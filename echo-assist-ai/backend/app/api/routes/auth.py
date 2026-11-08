from datetime import datetime, timezone
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.config import settings
from app.database import get_db
from app.models.user import User
from app.models.user_settings import UserSettings
from app.models.user_profile import UserProfile
from app.models.refresh_session import RefreshSession
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.services.account_token_service import (
    EMAIL_VERIFICATION,
    PASSWORD_RESET,
    consume_account_token,
    issue_account_token,
)
from app.services.audit_service import record_audit_event
from app.services.notification_service import NotificationService, get_notification_service
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


def _email_address(email: str) -> str:
    """Canonicalize user input without changing legacy stored records."""
    return email.strip().lower()


def _find_user_by_email(db: Session, email: str) -> User | None:
    """Allow existing mixed-case accounts to authenticate consistently."""
    return (
        db.query(User)
        .filter(func.lower(User.email) == _email_address(email))
        .first()
    )


def issue_token_pair(user: User, db: Session) -> TokenResponse:
    refresh_token, session_id, expires_at = create_refresh_token(subject=str(user.id))
    db.add(RefreshSession(user_id=user.id, session_id=session_id, expires_at=expires_at))
    db.commit()
    return TokenResponse(access_token=create_access_token(subject=str(user.id)), refresh_token=refresh_token)


def _action_url(action: str, token: str) -> str:
    return f"{settings.FRONTEND_BASE_URL.rstrip('/')}/?action={action}&token={quote(token, safe='')}"


def _issue_and_send_action_token(
    *,
    db: Session,
    user: User,
    notifier: NotificationService,
    purpose: str,
    action: str,
    subject: str,
    message_prefix: str,
    expires_in_minutes: int,
) -> None:
    raw_token = issue_account_token(
        db,
        user_id=user.id,
        purpose=purpose,
        expires_in_minutes=expires_in_minutes,
    )
    db.commit()
    notifier.send_email(user.email, subject, f"{message_prefix} {_action_url(action, raw_token)}")


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = _email_address(str(payload.email))
    existing = _find_user_by_email(db, email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        full_name=payload.full_name,
        email=email,
        hashed_password=hash_password(payload.password),
        preferred_language=payload.preferred_language,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    db.add(UserSettings(user_id=user.id, language=payload.preferred_language))
    db.add(UserProfile(user_id=user.id))
    record_audit_event(
        db,
        event_type="account.registered",
        message="User account registered",
        user_id=user.id,
    )
    db.commit()
    return issue_token_pair(user, db)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = _find_user_by_email(db, str(payload.email))
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    record_audit_event(
        db,
        event_type="account.login",
        message="User authenticated successfully",
        user_id=user.id,
    )
    db.commit()
    return issue_token_pair(user, db)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        decoded = decode_token(payload.refresh_token)
        if decoded.get("type") != "refresh":
            raise JWTError("Not a refresh token")
        user_id = decoded["sub"]
        session_id = decoded.get("sid")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token"
        )

    user = db.get(User, int(user_id))
    session = db.query(RefreshSession).filter(RefreshSession.session_id == session_id).first()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if not user or not session or not session.is_active or session.expires_at < now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    session.is_active = False
    session.revoked_at = datetime.now(timezone.utc)
    record_audit_event(
        db,
        event_type="session.refreshed",
        message="Refresh session rotated",
        user_id=user.id,
    )
    return issue_token_pair(user, db)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        decoded = decode_token(payload.refresh_token)
        if decoded.get("type") != "refresh":
            raise JWTError("Not a refresh token")
        session_id = decoded.get("sid")
    except JWTError:
        return None
    if session_id:
        session = db.query(RefreshSession).filter(RefreshSession.session_id == session_id).first()
        if session and session.is_active:
            session.is_active = False
            session.revoked_at = datetime.now(timezone.utc)
            record_audit_event(
                db,
                event_type="account.logout",
                message="User session logged out",
                user_id=session.user_id,
            )
            db.commit()
    return None


@router.post("/forgot-password", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED)
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
    notifier: NotificationService = Depends(get_notification_service),
):
    """Request a reset without revealing whether an address is registered."""
    user = _find_user_by_email(db, str(payload.email))
    if user and user.is_active:
        _issue_and_send_action_token(
            db=db,
            user=user,
            notifier=notifier,
            purpose=PASSWORD_RESET,
            action="reset-password",
            subject="Reset your ECHO-ASSIST password",
            message_prefix="Use this one-time password-reset link:",
            expires_in_minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
        )
        record_audit_event(
            db,
            event_type="account.password_reset_requested",
            message="Password reset requested",
            user_id=user.id,
        )
        db.commit()
    return MessageResponse(detail="If an active account matches that email, a reset link has been requested.")


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    user_id = consume_account_token(db, raw_token=payload.token, purpose=PASSWORD_RESET)
    user = db.get(User, user_id) if user_id else None
    if not user or not user.is_active:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    user.hashed_password = hash_password(payload.new_password)
    db.query(RefreshSession).filter(RefreshSession.user_id == user.id, RefreshSession.is_active.is_(True)).update(
        {RefreshSession.is_active: False, RefreshSession.revoked_at: datetime.now(timezone.utc)},
        synchronize_session=False,
    )
    record_audit_event(
        db,
        event_type="account.password_reset",
        message="Password changed through a one-time reset token",
        user_id=user.id,
        severity="warning",
    )
    db.commit()
    return None


@router.post("/request-email-verification", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED)
def request_email_verification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    notifier: NotificationService = Depends(get_notification_service),
):
    if not current_user.is_verified:
        _issue_and_send_action_token(
            db=db,
            user=current_user,
            notifier=notifier,
            purpose=EMAIL_VERIFICATION,
            action="verify-email",
            subject="Verify your ECHO-ASSIST email",
            message_prefix="Use this one-time email-verification link:",
            expires_in_minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES,
        )
        record_audit_event(
            db,
            event_type="account.email_verification_requested",
            message="Email verification requested",
            user_id=current_user.id,
        )
        db.commit()
    return MessageResponse(detail="If verification is needed, a verification link has been requested.")


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    user_id = consume_account_token(db, raw_token=payload.token, purpose=EMAIL_VERIFICATION)
    user = db.get(User, user_id) if user_id else None
    if not user or not user.is_active:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token")
    user.is_verified = True
    record_audit_event(
        db,
        event_type="account.email_verified",
        message="Email address verified",
        user_id=user.id,
    )
    db.commit()
    return MessageResponse(detail="Email address verified.")

#
@router.post("/token", response_model=TokenResponse)
def swagger_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(func.lower(User.email) == _email_address(form_data.username))
        .first()
    )

    if not user or not verify_password(
        form_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return issue_token_pair(user, db)
