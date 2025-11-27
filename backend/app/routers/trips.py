from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.crud import create_trip, list_trips_for_user, get_trip
from app.schemas.trip import TripCreate
from app.schemas.response import ApiResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/trips", tags=["trips"])

@router.post("", response_model=ApiResponse)
def create(trip_in: TripCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # Truyền nguyên object trip_in xuống CRUD để lấy cả start_date, end_date
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
        raise HTTPException(404, "Trip not found")
    return ApiResponse(message="Chi tiết chuyến đi", data=trip)