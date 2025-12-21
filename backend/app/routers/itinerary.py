from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.crud import create_itinerary_day, create_activity, vote_activity, get_activities_for_day, confirm_activity, get_itinerary_for_trip, get_trip_locations
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

@router.get("/trip/{trip_id}", response_model=ApiResponse)
def get_trip_itinerary(trip_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    itinerary = get_itinerary_for_trip(db, trip_id)
    return ApiResponse(message="Lịch trình chuyến đi", data=itinerary)

@router.get("/days/{day_id}/activities", response_model=ApiResponse)
def get_day_activities(day_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    activities = get_activities_for_day(db, day_id)
    return ApiResponse(message="Danh sách hoạt động", data=activities)

@router.post("/activities", response_model=ApiResponse)
def add_activity(a: ActivityCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    activity = create_activity(db, activity=a,user_id=current_user.id)
    return ApiResponse(message="Thêm hoạt động thành công", data=activity)

@router.post("/activities/{activity_id}/vote", response_model=ApiResponse)
def vote(activity_id: int, vote_type: str = "upvote", db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    v = vote_activity(db, activity_id=activity_id, user_id=current_user.id, vote=vote_type)
    return ApiResponse(message="Bình chọn thành công", data={"vote_id": v.id, "type": v.vote})

@router.post("/activities/{activity_id}/confirm", response_model=ApiResponse)
def confirm_activity_endpoint(activity_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    activity = confirm_activity(db, activity_id)
    if not activity:
        raise HTTPException(404, "Hoạt động không tồn tại")
    return ApiResponse(message="Xác nhận hoạt động thành công", data=activity)

@router.get("/activities/{activity_id}", response_model=ApiResponse)
def get_activity(activity_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from app.crud.crud import get_activity_by_id
    activity = get_activity_by_id(db, activity_id)
    if not activity:
        raise HTTPException(404, "Hoạt động không tồn tại")
    return ApiResponse(message="Chi tiết hoạt động", data=activity)

@router.put("/activities/{activity_id}", response_model=ApiResponse)
def update_activity_endpoint(activity_id: int, activity_data: ActivityCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from app.crud.crud import get_activity_by_id, update_activity
    from app.models.itinerary import Activity
    activity = get_activity_by_id(db, activity_id)
    if not activity:
        raise HTTPException(404, "Hoạt động không tồn tại")
    if activity.create_by != current_user.id:
        raise HTTPException(403, "Chỉ người tạo mới có thể sửa hoạt động")
    updated = update_activity(db, activity_id, activity_data)
    return ApiResponse(message="Cập nhật hoạt động thành công", data=updated)

@router.delete("/activities/{activity_id}", response_model=ApiResponse)
def delete_activity_endpoint(activity_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from app.crud.crud import delete_activity
    from app.models.itinerary import Activity
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(404, "Hoạt động không tồn tại")
    if activity.create_by != current_user.id:
        raise HTTPException(403, "Chỉ người tạo mới có thể xóa hoạt động")
    delete_activity(db, activity_id)
    return ApiResponse(message="Xóa hoạt động thành công", data=None)

@router.get("/trip/{trip_id}/locations", response_model=ApiResponse)
def get_map_locations(trip_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Lấy tất cả địa điểm confirmed để hiển thị trên Google Maps"""
    locations = get_trip_locations(db, trip_id)
    return ApiResponse(
        message="Danh sách địa điểm trên bản đồ", 
        data={
            "trip_id": trip_id,
            "locations": locations,
            "center": {
                "lat": 21.0285,
                "lng": 105.8542
            } if len(locations) == 0 else {
                "lat": sum(loc["latitude"] for loc in locations) / len(locations),
                "lng": sum(loc["longitude"] for loc in locations) / len(locations)
            }
        }
    )