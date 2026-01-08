from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationResponse
from app.schemas.device_token import DeviceTokenCreate
from app.schemas.email import EmailSend
from app.services.push_notification_service import firebase_service
from app.services.notification_service import email_service

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new notification and send push if device token exists"""
    # Save notification to database
    db_notification = Notification(**notification.dict())
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    
    # Get target user
    target_user = db.query(User).filter(User.id == notification.user_id).first()
    
    # Send push notification if device token exists
    if target_user and target_user.device_token:
        firebase_service.send_push_notification(
            device_token=target_user.device_token,
            title=notification.title,
            body=notification.message,
            data={"notification_id": str(db_notification.id), "type": notification.type}
        )
    
    return db_notification

@router.get("", response_model=List[NotificationResponse])
def get_notifications(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all notifications for current user"""
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    return notifications

@router.put("/{notification_id}/read", response_model=NotificationResponse)
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark notification as read"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification

@router.post("/device-token", status_code=status.HTTP_200_OK)
def save_device_token(
    token_data: DeviceTokenCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save device token for push notifications"""
    current_user.device_token = token_data.device_token
    db.commit()
    return {"message": "Device token saved successfully"}

@router.post("/email/send", status_code=status.HTTP_200_OK)
def send_email(
    email_data: EmailSend,
    current_user: User = Depends(get_current_user)
):
    """Send email notification"""
    success = email_service.send_notification_email(
        to_email=email_data.to_email,
        subject=email_data.subject,
        body=email_data.body
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email")
    
    return {"message": "Email sent successfully"}
