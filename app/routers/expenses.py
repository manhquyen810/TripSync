from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.crud import create_expense, list_expenses_for_trip, create_settlement, list_settlements_for_trip
from app.schemas.expense import ExpenseCreate, SettlementCreate
from app.schemas.response import ApiResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/expenses", tags=["expenses"])

@router.post("", response_model=ApiResponse)
def add_expense(e: ExpenseCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # Truyền nguyên object 'e' để lấy split_method
    ex = create_expense(db, expense=e, user_id=current_user.id)
    return ApiResponse(message="Thêm chi tiêu thành công", data=ex)

@router.get("/trip/{trip_id}", response_model=ApiResponse)
def get_expenses(trip_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    expenses = list_expenses_for_trip(db, trip_id)
    return ApiResponse(message="Danh sách chi tiêu", data=expenses)

# --- API MỚI ---
@router.post("/settle", response_model=ApiResponse)
def settle_debt(s: SettlementCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    settlement = create_settlement(db, settlement=s, payer_id=current_user.id)
    return ApiResponse(message="Ghi nhận trả nợ thành công", data=settlement)

@router.get("/settle/trip/{trip_id}", response_model=ApiResponse)
def get_settlements(trip_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    settlements = list_settlements_for_trip(db, trip_id)
    return ApiResponse(message="Lịch sử trả nợ", data=settlements)