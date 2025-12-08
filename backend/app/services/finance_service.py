from sqlalchemy.orm import Session
from app import models
from collections import defaultdict
import math

# Định nghĩa một class nhỏ để chứa kết quả trả về
class TransactionSuggestion:
    def __init__(self, from_user: int, to_user: int, amount: float):
        self.from_user = from_user # Người cần trả
        self.to_user = to_user     # Người thụ hưởng
        self.amount = amount

def calculate_trip_balances(db: Session, trip_id: int):
    """
    Hàm tính toán ai nợ ai trong chuyến đi.
    Trả về danh sách các giao dịch cần thực hiện để mọi người 'huề' tiền.
    """
    
    # ---------------------------------------------------------
    # BƯỚC 1: Tính Net Balance (Dư/Nợ) từ các khoản chi tiêu (Expenses)
    # ---------------------------------------------------------
    # Logic: Balance = (Tổng tiền mình đã trả dùm) - (Tổng tiền mình tiêu thụ)
    
    balances = defaultdict(float) # Key: user_id, Value: amount (Dương là được nhận, Âm là phải trả)

    # Lấy tất cả expense của trip
    expenses = db.query(models.expense.Expense).filter(models.expense.Expense.trip_id == trip_id).all()

    for exp in expenses:
        # Người trả tiền (Payer) được cộng tiền vào balance
        balances[exp.payer_id] += exp.amount
        
        # Lấy danh sách những người phải chia tiền trong khoản này
        splits = db.query(models.expense.ExpenseSplit).filter(
            models.expense.ExpenseSplit.expense_id == exp.id
        ).all()
        
        for split in splits:
            # Người hưởng thụ (Split) bị trừ tiền khỏi balance
            balances[split.user_id] -= split.amount_owed

    # ---------------------------------------------------------
    # BƯỚC 2: Tính toán các khoản Đã Thanh Toán (Settlements)
    # ---------------------------------------------------------
    # Nếu A nợ B 100k, nhưng A đã dùng chức năng "Trả nợ" để trả 50k,
    # thì nợ thực tế chỉ còn 50k.
    
    settlements = db.query(models.expense.Settlement).filter(
        models.expense.Settlement.trip_id == trip_id
    ).all()
    
    for settlement in settlements:
        # Người trả nợ (Payer) bị trừ tiền (vì tiền đã ra khỏi túi) -> Sai! 
        # Logic đúng: Trong bảng Balance ảo này:
        # Payer (người trả nợ) đã thực hiện nghĩa vụ, nên balance của họ tăng lên (bớt âm).
        balances[settlement.payer_id] += settlement.amount
        
        # Receiver (người nhận nợ) đã nhận tiền, nên balance của họ giảm xuống (bớt dương).
        balances[settlement.receiver_id] -= settlement.amount

    # Làm tròn số tiền để tránh lỗi float (ví dụ 33333.3333)
    for user_id in balances:
        balances[user_id] = round(balances[user_id], 2)

    # ---------------------------------------------------------
    # BƯỚC 3: Thuật toán Tối giản nợ (Greedy Algorithm)
    # ---------------------------------------------------------
    debtors = []   # Danh sách người nợ (Balance < 0)
    creditors = [] # Danh sách chủ nợ (Balance > 0)

    for user_id, amount in balances.items():
        if amount < -0.01: # Dùng ngưỡng nhỏ để tránh lỗi làm tròn số 0
            debtors.append({"id": user_id, "amount": amount})
        elif amount > 0.01:
            creditors.append({"id": user_id, "amount": amount})

    # Sắp xếp danh sách (Optional: Giúp ưu tiên trả khoản lớn trước)
    debtors.sort(key=lambda x: x["amount"])       # Tăng dần (ví dụ -500, -200)
    creditors.sort(key=lambda x: x["amount"], reverse=True) # Giảm dần (ví dụ 400, 300)

    transactions = []
    
    i = 0 # Con trỏ cho debtors
    j = 0 # Con trỏ cho creditors

    while i < len(debtors) and j < len(creditors):
        debtor = debtors[i]
        creditor = creditors[j]

        # Số tiền cần xử lý là min của (khoản nợ, khoản được nhận)
        amount = min(abs(debtor["amount"]), creditor["amount"])
        
        # Làm tròn 2 số thập phân
        amount = round(amount, 2)

        # Ghi nhận giao dịch: Debtor trả cho Creditor
        if amount > 0:
            transactions.append({
                "from_user_id": debtor["id"],
                "to_user_id": creditor["id"],
                "amount": amount
            })

        # Cập nhật lại số dư sau khi trả
        debtor["amount"] += amount
        creditor["amount"] -= amount

        # Nếu debtor đã hết nợ -> Chuyển sang người tiếp theo
        if abs(debtor["amount"]) < 0.01:
            i += 1
        
        # Nếu creditor đã nhận đủ -> Chuyển sang người tiếp theo
        if abs(creditor["amount"]) < 0.01:
            j += 1

    # BƯỚC 4: Lấy thông tin User (Tên, Avatar) để hiển thị Frontend đẹp hơn
    final_result = []
    for t in transactions:
        from_user = db.query(models.user.User).get(t["from_user_id"])
        to_user = db.query(models.user.User).get(t["to_user_id"])
        
        final_result.append({
            "from_user": {
                "id": from_user.id,
                "name": from_user.name,
                "avatar_url": from_user.avatar_url
            },
            "to_user": {
                "id": to_user.id,
                "name": to_user.name,
                "avatar_url": to_user.avatar_url
            },
            "amount": t["amount"]
        })
        
    return final_result