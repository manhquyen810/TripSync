import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:123@localhost:5432/tripsync")
SECRET_KEY = os.getenv("SECRET_KEY", "affd69472cda8d2b05c0b6c1fe7f9daffee1ed3dfe1b4af079cba8d37d633935")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
