from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.crud import create_expense, list_expenses_for_trip, create_settlement, list_settlements_for_trip
from app.schemas.expense import ExpenseCreate, SettlementCreate
from app.schemas.response import ApiResponse
from app.dependencies import get_current_user
from app.services.finance_service import calculate_trip_balances
from app.models.notification import Notification
from app.models.trip import Trip
from app.models.user import User
from app.services.push_notification_service import firebase_service
from app.services.notification_service import email_service

router = APIRouter(prefix="/expenses", tags=["expenses"])

@router.post("", response_model=ApiResponse)
def add_expense(e: ExpenseCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        # Sử dụng payer_id từ request, nếu không có thì dùng current_user
        payer_id = e.payer_id if e.payer_id is not None else current_user.id
        ex = create_expense(db, expense=e, user_id=payer_id)
        
        # Get trip and payer info
        trip = db.query(Trip).filter(Trip.id == e.trip_id).first()
        payer = db.query(User).filter(User.id == payer_id).first()
        
        if trip and payer:
            # Notify all trip members (except payer)
            for member in trip.members:
                if member.id != payer_id:
                    # Create notification
                    notification = Notification(
                        user_id=member.id,
                        trip_id=trip.id,
                        title="New Expense Added",
                        message=f"{payer.name} added an expense of {e.amount} {e.currency}",
                        type="expense_added"
                    )
                    db.add(notification)
                    db.commit()
                    db.refresh(notification)
                    
                    # Send push notification
                    if member.device_token:
                        firebase_service.send_push_notification(
                            device_token=member.device_token,
                            title="New Expense",
                            body=f"{payer.name} added {e.amount} {e.currency} in {trip.name}",
                            data={"trip_id": str(trip.id), "expense_id": str(ex.id), "type": "expense_added"}
                        )
                    
                    # Send email
                    email_service.send_expense_email(
                        to_email=member.email,
                        trip_name=trip.name,
                        payer_name=payer.name,
                        amount=e.amount,
                        currency=e.currency,
                        description=e.description or "No description"
                    )
        
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
    
    # Get trip, payer and receiver info
    trip = db.query(Trip).filter(Trip.id == s.trip_id).first()
    receiver = db.query(User).filter(User.id == s.receiver_id).first()
    
    if trip and receiver:
        # Notify receiver
        notification = Notification(
            user_id=receiver.id,
            trip_id=trip.id,
            title="Payment Received",
            message=f"{current_user.name} paid you {s.amount} {s.currency}",
            type="payment_received"
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        # Send push notification
        if receiver.device_token:
            firebase_service.send_push_notification(
                device_token=receiver.device_token,
                title="Payment Received!",
                body=f"{current_user.name} paid you {s.amount} {s.currency}",
                data={"trip_id": str(trip.id), "settlement_id": str(settlement.id), "type": "payment_received"}
            )
        
        # Send email
        email_service.send_payment_email(
            to_email=receiver.email,
            trip_name=trip.name,
            payer_name=current_user.name,
            amount=s.amount,
            currency=s.currency
        )
    
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