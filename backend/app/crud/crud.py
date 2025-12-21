from sqlalchemy.orm import Session
from app import models
from app.schemas import user as user_schema
from app.schemas import trip as trip_schema
from app.schemas import itinerary as itinerary_schema
from app.schemas import expense as expense_schema
from app.core.security import get_password_hash, verify_password
from typing import Optional

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

# --- TRIPS ---
def create_trip(db: Session, trip: trip_schema.TripCreate, user_id: int):
    db_trip = models.trip.Trip(
        name=trip.name,
        owner_id=user_id,
        start_date=trip.start_date, 
        end_date=trip.end_date      
    )
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    
    # Tự động thêm chủ nhóm vào làm thành viên (Role: Owner)
    member = models.trip.TripMember(trip_id=db_trip.id, user_id=user_id, role="owner")
    db.add(member)
    db.commit()
    
    return db_trip

def get_trip(db: Session, trip_id: int):
    return db.query(models.trip.Trip).filter(models.trip.Trip.id == trip_id).first()

def update_trip(db: Session, trip_id: int, trip_update: trip_schema.TripCreate):
    db_trip = db.query(models.trip.Trip).filter(models.trip.Trip.id == trip_id).first()
    if not db_trip:
        return None
    db_trip.name = trip_update.name
    db_trip.start_date = trip_update.start_date
    db_trip.end_date = trip_update.end_date

    if hasattr(trip_update, 'base_currency') and trip_update.base_currency:
        db_trip.base_currency = trip_update.base_currency
    if hasattr(trip_update, 'invite_code') and trip_update.invite_code:
        db_trip.invite_code = trip_update.invite_code

    db.commit()
    db.refresh(db_trip)
    if db_trip.start_date and db_trip.end_date:
        total_days = (db_trip.end_date - db_trip.start_date).days + 1
        
        for i in range(1, total_days + 1):
            existing_day = db.query(models.itinerary.ItineraryDay).filter(
                models.itinerary.ItineraryDay.trip_id == trip_id,
                models.itinerary.ItineraryDay.day_number == i
            ).first()
        
            if not existing_day:
                new_day = models.itinerary.ItineraryDay(trip_id=trip_id, day_number=i)
                db.add(new_day)
        
        db.commit()

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
        return ValueError("Chuyến đi không tồn tại")
    
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
        create_by=user_id,
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
    existing = db.query(models.itinerary.ActivityVote).filter(
        models.itinerary.ActivityVote.activity_id == activity_id,
        models.itinerary.ActivityVote.user_id == user_id
    ).first()
    
    if existing:
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
    db.commit()
    db.refresh(db_expense)
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
        db.commit()
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
    return db.query(models.document.Document).filter(models.document.Document.trip_id == trip_id).all()

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
    if trip:
        db.delete(trip)
        db.commit()
    return trip

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