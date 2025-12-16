from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.database import engine, Base
from app.config import UPLOAD_DIR
import os
from typing import List, Dict

# --- QUAN TRỌNG: Import TỪNG file model để SQLAlchemy nhận diện và tạo bảng ---
from app.models import itinerary, user, trip, expense, document, checklist

# Import routers
from app.routers import auth as auth_router
from app.routers import users as users_router
from app.routers import trips as trips_router
from app.routers import itinerary as itinerary_router
from app.routers import expenses as expenses_router
from app.routers import documents as documents_router
from app.routers import checklist as checklist_router

# --- RESET DATABASE (Dùng cho Dev) ---
# Cảnh báo: Dòng này sẽ XÓA SẠCH dữ liệu cũ mỗi khi restart server
# Base.metadata.drop_all(bind=engine) 
# -------------------------------------

# Tạo bảng Database mới
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TripSync Backend", description="API cho ứng dụng TripSync")

# Mount thư mục upload
if os.path.isdir(UPLOAD_DIR):
    from fastapi.staticfiles import StaticFiles
    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(trips_router.router)
app.include_router(itinerary_router.router)
app.include_router(expenses_router.router)
app.include_router(documents_router.router)
app.include_router(checklist_router.router)

# --- QUẢN LÝ WEBSOCKET (Đã nâng cấp để chia theo từng Trip) ---
class ConnectionManager:
    def __init__(self):
        # Lưu connection theo trip_id: { "trip_1": [ws1, ws2], "trip_2": [ws3] }
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, trip_id: str):
        await websocket.accept()
        if trip_id not in self.active_connections:
            self.active_connections[trip_id] = []
        self.active_connections[trip_id].append(websocket)

    def disconnect(self, websocket: WebSocket, trip_id: str):
        if trip_id in self.active_connections:
            if websocket in self.active_connections[trip_id]:
                self.active_connections[trip_id].remove(websocket)

    async def broadcast(self, message: str, trip_id: str):
        if trip_id in self.active_connections:
            for connection in self.active_connections[trip_id]:
                await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{trip_id}")
async def websocket_endpoint(websocket: WebSocket, trip_id: str):
    await manager.connect(websocket, trip_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Chỉ gửi tin nhắn cho người trong cùng chuyến đi
            await manager.broadcast(f"Trip update: {data}", trip_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, trip_id)