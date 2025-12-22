from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.crud import create_exchange_rate, get_exchange_rates_for_trip, convert_currency
from app.schemas.exchange_rate import ExchangeRateCreate
from app.schemas.response import ApiResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/exchange-rates", tags=["exchange-rates"])

@router.post("", response_model=ApiResponse)
def add_exchange_rate(rate: ExchangeRateCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    exchange_rate = create_exchange_rate(db, exchange_rate=rate, user_id=current_user.id)
    return ApiResponse(message="Thêm tỷ giá thành công", data=exchange_rate)

@router.get("/trip/{trip_id}", response_model=ApiResponse)
def get_trip_exchange_rates(trip_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    rates = get_exchange_rates_for_trip(db, trip_id)
    return ApiResponse(message="Danh sách tỷ giá", data=rates)

@router.post("/convert", response_model=ApiResponse)
def convert_currency_endpoint(
    trip_id: int, 
    amount: float, 
    from_currency: str, 
    to_currency: str, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    try:
        converted = convert_currency(db, trip_id, amount, from_currency, to_currency)
        return ApiResponse(
            message="Quy đổi thành công", 
            data={
                "original_amount": amount,
                "from_currency": from_currency,
                "converted_amount": converted,
                "to_currency": to_currency
            }
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
