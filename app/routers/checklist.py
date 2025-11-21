from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.crud import create_checklist_item, toggle_checklist_item
from app.schemas.response import ApiResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/checklist", tags=["checklist"])

@router.post("/item", response_model=ApiResponse)
def add_item(trip_id: int, content: str, assignee: int | None = None, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    item = create_checklist_item(db, trip_id=trip_id, content=content, assignee=assignee)
    return ApiResponse(message="Thêm checklist thành công", data=item)

@router.post("/item/{item_id}/toggle", response_model=ApiResponse)
def toggle_item(item_id: int, is_done: bool, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    item = toggle_checklist_item(db, item_id=item_id, is_done=is_done)
    return ApiResponse(message="Cập nhật trạng thái thành công", data=item)
