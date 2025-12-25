from fastapi import APIRouter, Depends, HTTPException
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

@router.get("/trip/{trip_id}", response_model=ApiResponse)
def get_trip_checklist(trip_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from app.crud.crud import get_checklist_for_trip
    items = get_checklist_for_trip(db, trip_id)
    return ApiResponse(message="Danh sách checklist", data=items)

@router.get("/item/{item_id}", response_model=ApiResponse)
def get_item(item_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from app.crud.crud import get_checklist_item_by_id
    item = get_checklist_item_by_id(db, item_id)
    if not item:
        raise HTTPException(404, "Checklist item không tồn tại")
    return ApiResponse(message="Chi tiết checklist item", data=item)

@router.put("/item/{item_id}", response_model=ApiResponse)
def update_item(item_id: int, content: str, assignee: int = None, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from app.crud.crud import update_checklist_item_content
    item = update_checklist_item_content(db, item_id, content, assignee)
    if not item:
        raise HTTPException(404, "Checklist item không tồn tại")
    return ApiResponse(message="Cập nhật checklist item thành công", data=item)

@router.delete("/item/{item_id}", response_model=ApiResponse)
def delete_checklist_item_endpoint(item_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from app.crud.crud import delete_checklist_item
    from app.models.checklist import ChecklistItem
    item = db.query(ChecklistItem).filter(ChecklistItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "Checklist item không tồn tại")
    delete_checklist_item(db, item_id)
    return ApiResponse(message="Xóa checklist item thành công", data=None)
