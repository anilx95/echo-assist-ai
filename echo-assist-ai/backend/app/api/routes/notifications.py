from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.services.auth_service import get_current_user


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
def list_notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    records = db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).limit(100).all()
    return [
        {
            "id": record.id, "channel": record.channel, "recipient": record.recipient,
            "title": record.title, "message": record.message, "status": record.status,
            "created_at": record.created_at, "delivered_at": record.delivered_at,
        }
        for record in records
    ]
