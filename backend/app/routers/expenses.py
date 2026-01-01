from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.crud import create_expense, list_expenses_for_trip, create_settlement, list_settlements_for_trip
from app.schemas.expense import ExpenseCreate, SettlementCreate
from app.schemas.response import ApiResponse
from app.dependencies import get_current_user
from app.services.finance_service import calculate_trip_balances

router = APIRouter(prefix="/expenses", tags=["expenses"])

@router.post("", response_model=ApiResponse)
def add_expense(e: ExpenseCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        # Sử dụng payer_id từ request, nếu không có thì dùng current_user
        payer_id = e.payer_id if e.payer_id is not None else current_user.id
        ex = create_expense(db, expense=e, user_id=payer_id)
        return ApiResponse(message="Thêm chi tiêu thành công", data=ex)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

@router.get("/trip/{trip_id}", response_model=ApiResponse)
def get_expenses(trip_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from sqlalchemy.orm import joinedload
    from app.models.expense import Expense, ExpenseSplit
    
    expenses = db.query(Expense).filter(Expense.trip_id == trip_id).options(
        joinedload(Expense.payer),
        joinedload(Expense.splits).joinedload(ExpenseSplit.user)
    ).all()
    
    return ApiResponse(message="Danh sách chi tiêu", data=expenses)

@router.get("/trip/{trip_id}/balances", response_model=ApiResponse)
def get_trip_balances(trip_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    balances = calculate_trip_balances(db, trip_id)
    return ApiResponse(message="Bảng cân đối chi tiêu", data=balances)

@router.get("/debts/trip/{trip_id}", response_model=ApiResponse)
def get_trip_debts(trip_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Alias cho balances - dễ nhớ hơn"""
    balances = calculate_trip_balances(db, trip_id)
    return ApiResponse(message="Bảng cân đối chi tiêu", data=balances)

# --- API MỚI ---
@router.post("/settle", response_model=ApiResponse)
def settle_debt(s: SettlementCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    settlement = create_settlement(db, settlement=s, payer_id=current_user.id)
    return ApiResponse(message="Ghi nhận trả nợ thành công", data=settlement)

@router.get("/settle/trip/{trip_id}", response_model=ApiResponse)
def get_settlements(trip_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    settlements = list_settlements_for_trip(db, trip_id)
    return ApiResponse(message="Lịch sử trả nợ", data=settlements)

@router.get("/{expense_id}", response_model=ApiResponse)
def get_expense(expense_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from app.crud.crud import get_expense_by_id
    expense = get_expense_by_id(db, expense_id)
    if not expense:
        raise HTTPException(404, "Chi tiêu không tồn tại")
    return ApiResponse(message="Chi tiết chi tiêu", data=expense)

@router.put("/{expense_id}", response_model=ApiResponse)
def update_expense_endpoint(expense_id: int, expense_data: ExpenseCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from app.crud.crud import get_expense_by_id, update_expense
    expense = get_expense_by_id(db, expense_id)
    if not expense:
        raise HTTPException(404, "Chi tiêu không tồn tại")
    if expense.payer_id != current_user.id:
        raise HTTPException(403, "Chỉ người trả tiền mới có thể sửa chi tiêu")
    updated = update_expense(db, expense_id, expense_data)
    return ApiResponse(message="Cập nhật chi tiêu thành công", data=updated)

@router.delete("/{expense_id}", response_model=ApiResponse)
def delete_expense_endpoint(expense_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from app.crud.crud import delete_expense
    from app.models.expense import Expense
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(404, "Chi tiêu không tồn tại")
    if expense.payer_id != current_user.id:
        raise HTTPException(403, "Chỉ người trả tiền mới có thể xóa chi tiêu")
    delete_expense(db, expense_id)
    return ApiResponse(message="Xóa chi tiêu thành công", data=None)