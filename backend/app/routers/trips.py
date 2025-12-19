from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.crud import create_trip, list_trips_for_user, get_trip, join_trip_by_code, update_trip
from app.schemas.trip import TripCreate, TripRead
from app.schemas.response import ApiResponse
from app.dependencies import get_current_user
from pydantic import BaseModel


router = APIRouter(prefix="/trips", tags=["trips"])

@router.post("", response_model=ApiResponse)
def create(trip_in: TripCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    trip = create_trip(db, trip=trip_in, user_id=current_user.id)
    return ApiResponse(message="Tạo chuyến đi thành công", data=trip)

@router.get("", response_model=ApiResponse)
def list_trips(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    trips = list_trips_for_user(db, current_user.id)
    return ApiResponse(message="Danh sách chuyến đi", data=trips)

@router.get("/{trip_id}", response_model=ApiResponse)
def get_trip_detail(trip_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    trip = get_trip(db, trip_id)
    if not trip:
        raise HTTPException(404, "Chuyến đi không tồn tại")
    return ApiResponse(message="Chi tiết chuyến đi", data=trip)

@router.put("/{trip_id}", response_model=TripRead)
def update_trip_endpoint(
    trip_id: int, 
    trip_in: TripCreate, 
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
    return ApiResponse(message="Tham gia chuyến đi thành công", data=trip)