from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.crud import create_itinerary_day, create_activity, vote_activity, get_activities_by_trip_and_day_number
from app.schemas.response import ApiResponse
from app.schemas.itinerary import ActivityCreate
from app.dependencies import get_current_user

router = APIRouter(prefix="/itinerary", tags=["itinerary"])

@router.post("/days", response_model=ApiResponse)
def create_day(trip_id: int, day_number: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        day = create_itinerary_day(db, trip_id=trip_id, day_number=day_number)
        return ApiResponse(message="Tạo ngày thành công", data=day)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))





@router.post("/activities", response_model=ApiResponse)
def add_activity(a: ActivityCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    activity = create_activity(db, activity=a,user_id=current_user.id)
    return ApiResponse(message="Thêm hoạt động thành công", data=activity)

@router.post("/activities/{activity_id}/vote", response_model=ApiResponse)
def vote(activity_id: int, vote_type: str = "upvote", db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    v = vote_activity(db, activity_id=activity_id, user_id=current_user.id, vote=vote_type)
    return ApiResponse(message="Bình chọn thành công", data={"vote_id": v.id, "type": v.vote})


@router.get("/trips/{trip_id}/days/{day_number}/activities", response_model=ApiResponse)
def list_activities_by_day_number(trip_id: int, day_number: int, db: Session = Depends(get_db)):
    activities = get_activities_by_trip_and_day_number(db, trip_id=trip_id, day_number=day_number)
    return ApiResponse(message=f"Danh sách hoạt động ngày {day_number}", data=activities)