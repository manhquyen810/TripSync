from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from app import models
from app.schemas import user as user_schema
from app.schemas import trip as trip_schema
from app.schemas import itinerary as itinerary_schema
from app.schemas import expense as expense_schema
from app.core.security import get_password_hash, verify_password
from typing import Optional
from datetime import date
from sqlalchemy.exc import SQLAlchemyError

# --- USERS ---
def get_user_by_email(db: Session, email: str):
    return db.query(models.user.User).filter(models.user.User.email == email).first()

def create_user(db: Session, user: user_schema.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.user.User(
        email=user.email,
        hashed_password=hashed_password,
        name=user.name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def update_user_otp(db: Session, email: str, otp_code: str, otp_expires_at):
    """Update user's OTP code and expiration time"""
    user = get_user_by_email(db, email)
    if user:
        user.otp_code = otp_code
        user.otp_expires_at = otp_expires_at
        db.commit()
        db.refresh(user)
    return user

def verify_user_otp(db: Session, email: str, otp_code: str):
    """Verify OTP code and check if it's still valid"""
    from datetime import datetime, timezone
    
    user = get_user_by_email(db, email)
    if not user or not user.otp_code or not user.otp_expires_at:
        return None
    
    # Check if OTP matches and hasn't expired
    if user.otp_code == otp_code and user.otp_expires_at > datetime.now(timezone.utc):
        return user
    return None

def reset_user_password(db: Session, email: str, new_password: str):
    """Reset user password and clear OTP"""
    user = get_user_by_email(db, email)
    if user:
        user.hashed_password = get_password_hash(new_password)
        user.otp_code = None
        user.otp_expires_at = None
        db.commit()
        db.refresh(user)
    return user

# --- TRIPS ---
def _sync_itinerary_days_for_range(db: Session, trip_id: int, start_date: Optional[date], end_date: Optional[date]):
    if not start_date or not end_date:
        return

    total_days = (end_date - start_date).days + 1
    if total_days <= 0:
        return

    existing_days = db.query(models.itinerary.ItineraryDay).filter(
        models.itinerary.ItineraryDay.trip_id == trip_id
    ).all()
    existing_numbers = {d.day_number for d in existing_days}

    for i in range(1, total_days + 1):
        if i not in existing_numbers:
            db.add(models.itinerary.ItineraryDay(trip_id=trip_id, day_number=i))

    for d in existing_days:
        if d.day_number > total_days:
            db.delete(d)

    db.commit()


def create_trip(db: Session, trip: trip_schema.TripCreate, user_id: int):
    trip_kwargs = {
        "name": trip.name,
        "owner_id": user_id,
        "start_date": trip.start_date,
        "end_date": trip.end_date,
        "base_currency": trip.base_currency,
        "destination": trip.destination,
        "description": trip.description,
        "cover_image_url": getattr(trip, "cover_image_url", None),
    }
    if trip.invite_code is not None:
        trip_kwargs["invite_code"] = trip.invite_code

    db_trip = models.trip.Trip(**trip_kwargs)
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)

    _sync_itinerary_days_for_range(db, trip_id=db_trip.id, start_date=db_trip.start_date, end_date=db_trip.end_date)
    
    # Tự động thêm chủ nhóm vào làm thành viên (Role: Owner)
    member = models.trip.TripMember(trip_id=db_trip.id, user_id=user_id, role="owner")
    db.add(member)
    db.commit()

    return db_trip

def get_trip(db: Session, trip_id: int):
    return db.query(models.trip.Trip).filter(models.trip.Trip.id == trip_id).first()

def update_trip(db: Session, trip_id: int, trip_update: trip_schema.TripUpdate):
    db_trip = db.query(models.trip.Trip).filter(models.trip.Trip.id == trip_id).first()
    if not db_trip:
        return None

    update_data = trip_update.dict(exclude_unset=True)
    if "name" in update_data and update_data["name"] is not None:
        db_trip.name = update_data["name"]
    if "destination" in update_data:
        db_trip.destination = update_data["destination"]
    if "description" in update_data:
        db_trip.description = update_data["description"]
    if "cover_image_url" in update_data:
        db_trip.cover_image_url = update_data["cover_image_url"]
    if "start_date" in update_data:
        db_trip.start_date = update_data["start_date"]
    if "end_date" in update_data:
        db_trip.end_date = update_data["end_date"]
    if "base_currency" in update_data and update_data["base_currency"]:
        db_trip.base_currency = update_data["base_currency"]
    if "invite_code" in update_data and update_data["invite_code"]:
        db_trip.invite_code = update_data["invite_code"]

    db.commit()
    db.refresh(db_trip)

    _sync_itinerary_days_for_range(db, trip_id=trip_id, start_date=db_trip.start_date, end_date=db_trip.end_date)

    return db_trip    


def list_trips_for_user(db: Session, user_id: int):
    return db.query(models.trip.Trip).join(
        models.trip.TripMember, 
        models.trip.TripMember.trip_id == models.trip.Trip.id
    ).filter(models.trip.TripMember.user_id == user_id).all()

def join_trip_by_code(db: Session, invite_code: str, user_id: int):
    trip = db.query(models.trip.Trip).filter(models.trip.Trip.invite_code == invite_code).first()
    if not trip:
        return None
        
    exists = db.query(models.trip.TripMember).filter(
        models.trip.TripMember.trip_id == trip.id,
        models.trip.TripMember.user_id == user_id
    ).first()
    
    if exists:
        return trip 
        
    new_member = models.trip.TripMember(trip_id=trip.id, user_id=user_id, role="member")
    db.add(new_member)
    db.commit()
    
    return trip

def add_member_to_trip(db: Session, trip_id: int, user_email: str):
    user = get_user_by_email(db, user_email)
    if not user:
        return None
        
    exists = db.query(models.trip.TripMember).filter(
        models.trip.TripMember.trip_id == trip_id,
        models.trip.TripMember.user_id == user.id
    ).first()
    
    if exists:
        return {"user": user, "already_member": True}
        
    new_member = models.trip.TripMember(trip_id=trip_id, user_id=user.id, role="member")
    db.add(new_member)
    db.commit()
    
    return {"user": user, "already_member": False}

# --- ITINERARY ---
def create_itinerary_day(db: Session, trip_id: int, day_number: int):
    trip = db.query(models.trip.Trip).filter(models.trip.Trip.id == trip_id).first()
    if not trip:
        raise ValueError("Chuyến đi không tồn tại")
    
    if trip.start_date and trip.end_date:
        total_days = (trip.end_date - trip.start_date).days + 1
        if day_number < 1 or day_number > total_days:
            raise ValueError(f"Không thể tạo ngày {day_number}. Chuyến đi chỉ kéo dài {total_days} ngày {trip.start_date} đến {trip.end_date}.")

    existing_day = db.query(models.itinerary.ItineraryDay).filter(models.itinerary.ItineraryDay.trip_id == trip_id, models.itinerary.ItineraryDay.day_number == day_number).first()

    if existing_day:
        return existing_day
    
    day = models.itinerary.ItineraryDay(trip_id=trip_id, day_number=day_number)
    db.add(day)
    db.commit()
    db.refresh(day)
    return day

def create_activity(db: Session, activity: itinerary_schema.ActivityCreate, user_id: int):
    db_activity = models.itinerary.Activity(
        day_id=activity.day_id,
        created_by=user_id,
        title=activity.title,
        description=activity.description,
        location=activity.location,
        location_lat=activity.location_lat, 
        location_long=activity.location_long, 
        start_time=activity.start_time 
    )
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity

def vote_activity(db: Session, activity_id: int, user_id: int, vote: str = "upvote"):
    if vote not in ("upvote", "downvote"):
        raise ValueError("vote_type phải là upvote hoặc downvote")

    existing = db.query(models.itinerary.ActivityVote).filter(
        models.itinerary.ActivityVote.activity_id == activity_id,
        models.itinerary.ActivityVote.user_id == user_id
    ).first()
    
    if existing:
        # Toggle off when tapping the same vote again.
        if existing.vote == vote:
            db.delete(existing)
            db.commit()
            return None

        existing.vote = vote
        db.commit()
        db.refresh(existing)
        return existing
        
    v = models.itinerary.ActivityVote(activity_id=activity_id, user_id=user_id, vote=vote)
    db.add(v)
    db.commit()
    db.refresh(v)
    return v

def get_activities_for_day(db: Session, day_id: int):
    activities = db.query(models.itinerary.Activity).filter(models.itinerary.Activity.day_id == day_id).all()
    result = []
    for activity in activities:
        upvotes = db.query(models.itinerary.ActivityVote).filter(
            models.itinerary.ActivityVote.activity_id == activity.id,
            models.itinerary.ActivityVote.vote == "upvote"
        ).count()
        downvotes = db.query(models.itinerary.ActivityVote).filter(
            models.itinerary.ActivityVote.activity_id == activity.id,
            models.itinerary.ActivityVote.vote == "downvote"
        ).count()
        result.append({
            "activity": activity,
            "upvotes": upvotes,
            "downvotes": downvotes,
            "net_votes": upvotes - downvotes
        })
    return result

def confirm_activity(db: Session, activity_id: int):
    activity = db.query(models.itinerary.Activity).filter(models.itinerary.Activity.id == activity_id).first()
    if activity:
        activity.is_confirmed = True
        db.commit()
        db.refresh(activity)
    return activity

def get_itinerary_for_trip(db: Session, trip_id: int):
    days = db.query(models.itinerary.ItineraryDay).filter(
        models.itinerary.ItineraryDay.trip_id == trip_id
    ).order_by(models.itinerary.ItineraryDay.day_number).all()
    
    result = []
    for day in days:
        activities_data = get_activities_for_day(db, day.id)
        result.append({
            "day": day,
            "activities": activities_data
        })
    return result

def get_activities_by_trip_and_day_number(
    db: Session,
    trip_id: int,
    day_number: int,
    current_user_id: Optional[int] = None,
):
    activities = (
        db.query(models.itinerary.Activity)
        .join(
            models.itinerary.ItineraryDay,
            models.itinerary.Activity.day_id == models.itinerary.ItineraryDay.id,
        )
        .filter(models.itinerary.ItineraryDay.trip_id == trip_id)
        .filter(models.itinerary.ItineraryDay.day_number == day_number)
        .order_by(models.itinerary.Activity.start_time.asc())
        .all()
    )

    user_ids = {a.created_by for a in activities if a.created_by is not None}
    user_name_by_id: dict[int, str] = {}
    if user_ids:
        users = (
            db.query(models.user.User)
            .filter(models.user.User.id.in_(user_ids))
            .all()
        )
        user_name_by_id = {u.id: (u.name or "").strip() for u in users}

    my_vote_by_activity_id: dict[int, str] = {}
    if current_user_id is not None and activities:
        activity_ids = [a.id for a in activities]
        votes = (
            db.query(models.itinerary.ActivityVote)
            .filter(models.itinerary.ActivityVote.user_id == current_user_id)
            .filter(models.itinerary.ActivityVote.activity_id.in_(activity_ids))
            .all()
        )
        my_vote_by_activity_id = {v.activity_id: v.vote for v in votes}

    result = []
    for activity in activities:
        upvotes = (
            db.query(models.itinerary.ActivityVote)
            .filter(models.itinerary.ActivityVote.activity_id == activity.id)
            .filter(models.itinerary.ActivityVote.vote == "upvote")
            .count()
        )
        downvotes = (
            db.query(models.itinerary.ActivityVote)
            .filter(models.itinerary.ActivityVote.activity_id == activity.id)
            .filter(models.itinerary.ActivityVote.vote == "downvote")
            .count()
        )

        start_time = ""
        if activity.start_time is not None:
            try:
                start_time = activity.start_time.strftime("%H:%M")
            except Exception:
                start_time = str(activity.start_time)

        created_by_name = ""
        if activity.created_by is not None:
            created_by_name = user_name_by_id.get(activity.created_by, "")

        result.append(
            {
                "id": activity.id,
                "day_id": activity.day_id,
                "title": activity.title,
                "description": activity.description,
                "location": activity.location,
                "start_time": start_time,
                "is_confirmed": activity.is_confirmed,
                "created_by": activity.created_by,
                "created_by_name": created_by_name,
                "upvotes": upvotes,
                "total_votes": upvotes + downvotes,
                "my_vote": my_vote_by_activity_id.get(activity.id),
            }
        )

    return result

# --- EXPENSES ---
def create_expense(db: Session, expense: expense_schema.ExpenseCreate, user_id: int):
    # Validate: Check if all involved users are members of the trip
    if expense.involved_user_ids:
        for member_id in expense.involved_user_ids:
            is_member = db.query(models.trip.TripMember).filter(
                models.trip.TripMember.trip_id == expense.trip_id,
                models.trip.TripMember.user_id == member_id
            ).first()
            if not is_member:
                raise ValueError(f"User ID {member_id} không phải là thành viên của chuyến đi này")
    
    # Tạo expense record
    db_expense = models.expense.Expense(
        trip_id=expense.trip_id,
        payer_id=user_id,
        amount=expense.amount,
        currency=expense.currency,
        description=expense.description,
        split_method=expense.split_method,
        expense_date=expense.expense_date
    )
    db.add(db_expense)
    
    # Flush để gán ID cho expense (cần ID để tạo splits), nhưng CHƯA lưu vào DB
    # Nếu có lỗi ở bước sau, toàn bộ transaction sẽ bị rollback
    db.flush()
    
    # Tạo expense splits (chia tiền cho từng người)
    if expense.involved_user_ids:
        num_people = len(expense.involved_user_ids)
        split_amount = expense.amount / num_people

        for member_id in expense.involved_user_ids:
            split = models.expense.ExpenseSplit(
                expense_id=db_expense.id,
                user_id=member_id,
                amount_owed=split_amount
            )
            db.add(split)
    
    # Commit tất cả cùng lúc (expense + splits) để đảm bảo tính toàn vẹn dữ liệu
    # Nếu tạo splits bị lỗi, expense cũng sẽ không được lưu
    db.commit()
    db.refresh(db_expense)
    return db_expense

def list_expenses_for_trip(db: Session, trip_id: int):
    return db.query(models.expense.Expense).filter(models.expense.Expense.trip_id == trip_id).all()

# --- SETTLEMENTS (Mới: Thanh toán nợ) ---
def create_settlement(db: Session, settlement: expense_schema.SettlementCreate, payer_id: int):
    db_settlement = models.expense.Settlement(
        trip_id=settlement.trip_id,
        payer_id=payer_id,
        receiver_id=settlement.receiver_id,
        amount=settlement.amount
    )
    db.add(db_settlement)
    db.commit()
    db.refresh(db_settlement)
    return db_settlement

def list_settlements_for_trip(db: Session, trip_id: int):
    return db.query(models.expense.Settlement).filter(models.expense.Settlement.trip_id == trip_id).all()

# --- DOCUMENTS ---
def create_document(db: Session, trip_id: int, uploader_id: int, filename: str, url: str, category: str | None = None):
    d = models.document.Document(trip_id=trip_id, uploader_id=uploader_id, filename=filename, url=url, category=category)
    db.add(d)
    db.commit()
    db.refresh(d)
    return d

def list_documents_for_trip(db: Session, trip_id: int):
    # Some clients historically uploaded trip cover/avatar through /documents/upload.
    # Hide those categories by default so the trip documents list stays clean.
    hidden_categories = {"avatar", "user_avatar", "cover", "trip_cover", "cover_image"}
    Document = models.document.Document
    return (
        db.query(Document)
        .filter(Document.trip_id == trip_id)
        .filter(or_(Document.category.is_(None), ~Document.category.in_(hidden_categories)))
        .all()
    )

# --- CHECKLIST ---
def create_checklist_item(db: Session, trip_id: int, content: str, assignee: int | None = None):
    it = models.checklist.ChecklistItem(trip_id=trip_id, content=content, assignee=assignee)
    db.add(it)
    db.commit()
    db.refresh(it)
    return it

def toggle_checklist_item(db: Session, item_id: int, is_done: bool):
    it = db.query(models.checklist.ChecklistItem).filter(models.checklist.ChecklistItem.id == item_id).first()
    if it:
        it.is_done = is_done
        db.commit()
        db.refresh(it)
    return it

# --- DELETE OPERATIONS ---
def delete_trip(db: Session, trip_id: int):
    trip = db.query(models.trip.Trip).filter(models.trip.Trip.id == trip_id).first()
    if not trip:
        return None

    try:
        activity_ids_subq = (
            db.query(models.itinerary.Activity.id)
            .join(models.itinerary.ItineraryDay, models.itinerary.Activity.day_id == models.itinerary.ItineraryDay.id)
            .filter(models.itinerary.ItineraryDay.trip_id == trip_id)
            .subquery()
        )

        db.query(models.itinerary.ActivityVote).filter(
            models.itinerary.ActivityVote.activity_id.in_(activity_ids_subq)
        ).delete(synchronize_session=False)

        db.query(models.trip.TripMember).filter(
            models.trip.TripMember.trip_id == trip_id
        ).delete(synchronize_session=False)

        db.query(models.expense.Settlement).filter(
            models.expense.Settlement.trip_id == trip_id
        ).delete(synchronize_session=False)

        db.delete(trip)
        db.commit()
        return trip
    except SQLAlchemyError:
        db.rollback()
        raise

def delete_activity(db: Session, activity_id: int):
    activity = db.query(models.itinerary.Activity).filter(models.itinerary.Activity.id == activity_id).first()
    if activity:
        db.delete(activity)
        db.commit()
    return activity

def delete_expense(db: Session, expense_id: int):
    expense = db.query(models.expense.Expense).filter(models.expense.Expense.id == expense_id).first()
    if expense:
        db.delete(expense)
        db.commit()
    return expense

def delete_document(db: Session, document_id: int):
    document = db.query(models.document.Document).filter(models.document.Document.id == document_id).first()
    if document:
        db.delete(document)
        db.commit()
    return document

def delete_checklist_item(db: Session, item_id: int):
    item = db.query(models.checklist.ChecklistItem).filter(models.checklist.ChecklistItem.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
    return item

def get_checklist_for_trip(db: Session, trip_id: int):
    return db.query(models.checklist.ChecklistItem).filter(models.checklist.ChecklistItem.trip_id == trip_id).all()

# --- GET BY ID ---
def get_user_by_id(db: Session, user_id: int):
    return db.query(models.user.User).filter(models.user.User.id == user_id).first()

def get_activity_by_id(db: Session, activity_id: int):
    return db.query(models.itinerary.Activity).filter(models.itinerary.Activity.id == activity_id).first()

def get_expense_by_id(db: Session, expense_id: int):
    return db.query(models.expense.Expense).filter(models.expense.Expense.id == expense_id).first()

def get_document_by_id(db: Session, document_id: int):
    return db.query(models.document.Document).filter(models.document.Document.id == document_id).first()

def get_checklist_item_by_id(db: Session, item_id: int):
    return db.query(models.checklist.ChecklistItem).filter(models.checklist.ChecklistItem.id == item_id).first()

def get_trip_members(db: Session, trip_id: int):
    members = db.query(models.user.User).join(
        models.trip.TripMember,
        models.trip.TripMember.user_id == models.user.User.id
    ).filter(models.trip.TripMember.trip_id == trip_id).all()
    return members

# --- UPDATE OPERATIONS ---
def update_activity(db: Session, activity_id: int, activity_data):
    activity = get_activity_by_id(db, activity_id)
    if not activity:
        return None
    
    activity.title = activity_data.title
    activity.description = activity_data.description
    activity.location = activity_data.location
    activity.location_lat = activity_data.location_lat
    activity.location_long = activity_data.location_long
    activity.start_time = activity_data.start_time
    
    db.commit()
    db.refresh(activity)
    return activity

def update_expense(db: Session, expense_id: int, expense_data):
    expense = get_expense_by_id(db, expense_id)
    if not expense:
        return None
    
    expense.amount = expense_data.amount
    expense.currency = expense_data.currency
    expense.description = expense_data.description
    expense.expense_date = expense_data.expense_date
    
    db.commit()
    db.refresh(expense)
    return expense

def update_checklist_item_content(db: Session, item_id: int, content: str, assignee: int = None):
    item = get_checklist_item_by_id(db, item_id)
    if not item:
        return None
    
    item.content = content
    if assignee is not None:
        item.assignee = assignee
    
    db.commit()
    db.refresh(item)
    return item

def update_user_profile(db: Session, user_id: int, name: str, avatar_url: str = None):
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    
    user.name = name
    if avatar_url is not None:
        user.avatar_url = avatar_url
    
    db.commit()
    db.refresh(user)
    return user

# --- LOCATIONS FOR MAP ---
def get_trip_locations(db: Session, trip_id: int):
    """Get all confirmed activities with location data for Google Maps"""
    locations = db.query(models.itinerary.Activity).filter(
        models.itinerary.Activity.is_confirmed == True,
        models.itinerary.Activity.location_lat.isnot(None),
        models.itinerary.Activity.location_long.isnot(None)
    ).join(
        models.itinerary.ItineraryDay,
        models.itinerary.ItineraryDay.id == models.itinerary.Activity.day_id
    ).filter(
        models.itinerary.ItineraryDay.trip_id == trip_id
    ).all()
    
    result = []
    for activity in locations:
        result.append({
            "id": activity.id,
            "title": activity.title,
            "location": activity.location,
            "latitude": float(activity.location_lat) if activity.location_lat else None,
            "longitude": float(activity.location_long) if activity.location_long else None,
            "day_number": activity.day_id,
            "start_time": str(activity.start_time) if activity.start_time else None
        })
    
    return result

# --- EXCHANGE RATES ---
def create_exchange_rate(db: Session, exchange_rate, user_id: int):
    from app.models.exchange_rate import ExchangeRate
    rate = ExchangeRate(
        trip_id=exchange_rate.trip_id,
        from_currency=exchange_rate.from_currency,
        to_currency=exchange_rate.to_currency,
        rate=exchange_rate.rate,
        created_by=user_id
    )
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate

def get_exchange_rates_for_trip(db: Session, trip_id: int):
    from app.models.exchange_rate import ExchangeRate
    return db.query(ExchangeRate).filter(ExchangeRate.trip_id == trip_id).all()

def convert_currency(db: Session, trip_id: int, amount: float, from_currency: str, to_currency: str):
    from app.models.exchange_rate import ExchangeRate
    if from_currency == to_currency:
        return amount
    
    rate = db.query(ExchangeRate).filter(
        ExchangeRate.trip_id == trip_id,
        ExchangeRate.from_currency == from_currency,
        ExchangeRate.to_currency == to_currency
    ).first()
    
    if not rate:
        raise ValueError(f"Không tìm thấy tỷ giá từ {from_currency} sang {to_currency}")
    
    return amount * rate.rate