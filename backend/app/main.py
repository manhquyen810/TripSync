from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, status
from fastapi.responses import JSONResponse
from app.database import engine, Base
from app.config import UPLOAD_DIR
import os
from typing import List, Dict
import logging
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- QUAN TRỌNG: Import TỪNG file model để SQLAlchemy nhận diện và tạo bảng ---
from app.models import user, trip, itinerary, expense, document, checklist, exchange_rate

# Import routers
from app.routers import auth as auth_router
from app.routers import users as users_router
from app.routers import trips as trips_router
from app.routers import itinerary as itinerary_router
from app.routers import expenses as expenses_router
from app.routers import documents as documents_router
from app.routers import checklist as checklist_router
from app.routers import exchange_rates as exchange_rates_router

# --- RESET DATABASE (Dùng cho Dev) ---
# Cảnh báo: Dòng này sẽ XÓA SẠCH dữ liệu cũ mỗi khi restart server
# UNCOMMENT CHỈ KHI ĐANG DEV - COMMENT KHI DEPLOY PRODUCTION
# Base.metadata.drop_all(bind=engine) 
# -------------------------------------

# Tạo bảng Database mới
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TripSync Backend", description="API cho ứng dụng TripSync")

# Global Exception Handler - Log tất cả lỗi
@app.middleware("http")
async def log_errors_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        logger.error(f"❌ ERROR in {request.method} {request.url.path}")
        logger.error(f"📋 Error Type: {type(exc).__name__}")
        logger.error(f"💬 Error Message: {str(exc)}")
        logger.error(f"🔍 Traceback:\n{traceback.format_exc()}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "message": "Internal Server Error",
                "detail": str(exc),
                "type": type(exc).__name__
            }
        )

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
app.include_router(exchange_rates_router.router)

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