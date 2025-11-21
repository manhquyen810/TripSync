from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.crud import create_itinerary_day, create_activity, vote_activity
from app.schemas.response import ApiResponse
from app.schemas.itinerary import ActivityCreate
from app.dependencies import get_current_user

router = APIRouter(prefix="/itinerary", tags=["itinerary"])

@router.post("/days", response_model=ApiResponse)
def create_day(trip_id: int, day_number: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    day = create_itinerary_day(db, trip_id=trip_id, day_number=day_number)
    return ApiResponse(message="Tạo ngày thành công", data=day)

@router.post("/activities", response_model=ApiResponse)
def add_activity(a: ActivityCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # Truyền nguyên object 'a' để lấy start_time
    activity = create_activity(db, activity=a)
    return ApiResponse(message="Thêm hoạt động thành công", data=activity)

@router.post("/activities/{activity_id}/vote", response_model=ApiResponse)
def vote(activity_id: int, vote_type: str = "upvote", db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    v = vote_activity(db, activity_id=activity_id, user_id=current_user.id, vote=vote_type)
    return ApiResponse(message="Bình chọn thành công", data={"vote_id": v.id, "type": v.vote})