"""Small, structured audit-log helper.

Audit data deliberately excludes passwords, JWTs, refresh tokens and provider
credentials.  Callers may attach only operational identifiers and metadata.
"""

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.system_log import SystemLog


def record_audit_event(
    db: Session,
    *,
    event_type: str,
    message: str,
    user_id: int | None = None,
    severity: str = "info",
    context: dict[str, Any] | None = None,
) -> None:
    """Stage an audit event in the current database transaction."""
    db.add(
        SystemLog(
            user_id=user_id,
            event_type=event_type,
            severity=severity,
            message=message,
            context_json=json.dumps(context, separators=(",", ":")) if context else None,
        )
    )
