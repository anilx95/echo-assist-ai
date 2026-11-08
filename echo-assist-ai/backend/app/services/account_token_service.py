"""Issue and consume short-lived, one-time account-action tokens."""

from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from sqlalchemy.orm import Session

from app.models.account_token import AccountToken


PASSWORD_RESET = "password_reset"
EMAIL_VERIFICATION = "email_verification"


def _now() -> datetime:
    # Database columns are timezone-naive for PostgreSQL/SQLite portability.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _hash(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def issue_account_token(
    db: Session, *, user_id: int, purpose: str, expires_in_minutes: int
) -> str:
    """Invalidate older unused tokens of the same type and stage a fresh one."""
    now = _now()
    (
        db.query(AccountToken)
        .filter(
            AccountToken.user_id == user_id,
            AccountToken.purpose == purpose,
            AccountToken.used_at.is_(None),
        )
        .update({AccountToken.used_at: now}, synchronize_session=False)
    )
    raw_token = secrets.token_urlsafe(32)
    db.add(
        AccountToken(
            user_id=user_id,
            token_hash=_hash(raw_token),
            purpose=purpose,
            expires_at=now + timedelta(minutes=expires_in_minutes),
        )
    )
    return raw_token


def consume_account_token(db: Session, *, raw_token: str, purpose: str) -> int | None:
    """Consume a valid token once and return its user ID, otherwise None."""
    now = _now()
    record = (
        db.query(AccountToken)
        .filter(
            AccountToken.token_hash == _hash(raw_token),
            AccountToken.purpose == purpose,
            AccountToken.used_at.is_(None),
            AccountToken.expires_at >= now,
        )
        .first()
    )
    if not record:
        return None
    record.used_at = now
    return record.user_id
