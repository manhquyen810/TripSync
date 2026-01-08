from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.crud import (
    create_trip,
    list_trips_for_user,
    get_trip,
    join_trip_by_code,
    update_trip,
    add_member_to_trip,
)
from app.schemas.trip import TripCreate, TripRead, TripUpdate
from app.schemas.response import ApiResponse
from app.dependencies import get_current_user
from pydantic import BaseModel, EmailStr
from app.models.notification import Notification
from app.models.user import User
from app.services.push_notification_service import firebase_service
from app.services.notification_service import email_service


router = APIRouter(prefix="/trips", tags=["trips"])

@router.post("", response_model=ApiResponse)
def create(trip_in: TripCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    trip = create_trip(db, trip=trip_in, user_id=current_user.id)
    return ApiResponse(message="Tạo chuyến đi thành công", data=TripRead.from_orm(trip))

@router.get("", response_model=ApiResponse)
def list_trips(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    trips = list_trips_for_user(db, current_user.id)
    return ApiResponse(
        message="Danh sách chuyến đi",
        data=[TripRead.from_orm(t) for t in trips],
    )

@router.get("/{trip_id}", response_model=ApiResponse)
def get_trip_detail(trip_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    trip = get_trip(db, trip_id)
    if not trip:
        raise HTTPException(404, "Chuyến đi không tồn tại")
    return ApiResponse(message="Chi tiết chuyến đi", data=TripRead.from_orm(trip))

@router.put("/{trip_id}", response_model=TripRead)
def update_trip_endpoint(
    trip_id: int, 
    trip_in: TripUpdate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    trip = get_trip(db, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Chuyến đi không tồn tại")
        
    if trip.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền cập nhật chuyến đi này")

    updated_trip = update_trip(db, trip_id=trip_id, trip_update=trip_in)
    
    return updated_trip

class JoinTripCode(BaseModel):
    invite_code: str

@router.post("/join", response_model=ApiResponse)
def join_trip(join_data: JoinTripCode, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    trip = join_trip_by_code(db, invite_code=join_data.invite_code, user_id=current_user.id)
    if not trip:
        raise HTTPException(404, "Mã mời không hợp lệ hoặc bạn đã tham gia chuyến đi này")
    
    # Notify all existing members
    for member in trip.members:
        if member.id != current_user.id:
            notification = Notification(
                user_id=member.id,
                trip_id=trip.id,
                title="New Member Joined",
                message=f"{current_user.name} joined {trip.name}",
                type="member_joined"
            )
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            # Send push notification
            if member.device_token:
                firebase_service.send_push_notification(
                    device_token=member.device_token,
                    title="New Member!",
                    body=f"{current_user.name} joined {trip.name}",
                    data={"trip_id": str(trip.id), "type": "member_joined"}
                )
            
            # Send email
            email_service.send_member_joined_email(
                to_email=member.email,
                trip_name=trip.name,
                member_name=current_user.name
            )
    
    return ApiResponse(message="Tham gia chuyến đi thành công", data=TripRead.from_orm(trip))

class AddMemberRequest(BaseModel):
    user_email: EmailStr

@router.post("/{trip_id}/members", response_model=ApiResponse)
def add_member(trip_id: int, member_data: AddMemberRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    trip = get_trip(db, trip_id)
    if not trip:
        raise HTTPException(404, "Chuyến đi không tồn tại")
    if trip.owner_id != current_user.id:
        raise HTTPException(403, "Chỉ chủ nhóm mới có thể mời thành viên")
    
    result = add_member_to_trip(db, trip_id, member_data.user_email)
    if not result:
        raise HTTPException(404, "Không tìm thấy người dùng với email này")
    
    if result["already_member"]:
        return ApiResponse(message="Người dùng đã là thành viên", data=result["user"])
    
    # Send invite notification to new member
    new_member = db.query(User).filter(User.email == member_data.user_email).first()
    if new_member:
        notification = Notification(
            user_id=new_member.id,
            trip_id=trip.id,
            title="Trip Invitation",
            message=f"{current_user.name} invited you to {trip.name}",
            type="invite_trip"
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        # Send push notification
        if new_member.device_token:
            firebase_service.send_push_notification(
                device_token=new_member.device_token,
                title="You're Invited!",
                body=f"{current_user.name} invited you to {trip.name}",
                data={"trip_id": str(trip.id), "invite_code": trip.invite_code, "type": "invite_trip"}
            )
        
        # Send email
        email_service.send_trip_invite_email(
            to_email=new_member.email,
            trip_name=trip.name,
            inviter_name=current_user.name,
            invite_code=trip.invite_code
        )
    
    return ApiResponse(message="Thêm thành viên thành công", data=result["user"])

@router.get("/{trip_id}/members", response_model=ApiResponse)
def get_members(trip_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from app.crud.crud import get_trip_members
    trip = get_trip(db, trip_id)
    if not trip:
        raise HTTPException(404, "Chuyến đi không tồn tại")
    members = get_trip_members(db, trip_id)
    return ApiResponse(message="Danh sách thành viên", data=members)

@router.delete("/{trip_id}", response_model=ApiResponse)
def delete_trip_endpoint(trip_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from app.crud.crud import delete_trip
    trip = get_trip(db, trip_id)
    if not trip:
        raise HTTPException(404, "Chuyến đi không tồn tại")
    if trip.owner_id != current_user.id:
        raise HTTPException(403, "Chỉ chủ nhóm mới có thể xóa chuyến đi")
    delete_trip(db, trip_id)
    return ApiResponse(message="Xóa chuyến đi thành công", data=None)