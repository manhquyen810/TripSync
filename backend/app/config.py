import os
from pathlib import Path

from dotenv import load_dotenv


_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=_ENV_PATH, override=False)


def _require_env(name: str) -> str:
	value = os.getenv(name)
	if value is None or not str(value).strip():
		raise RuntimeError(f"Missing required environment variable: {name}")
	return value


DATABASE_URL = _require_env("DATABASE_URL")
SECRET_KEY = _require_env("SECRET_KEY")

_expire_raw = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200")
ACCESS_TOKEN_EXPIRE_MINUTES = int(_expire_raw.split("#", 1)[0].strip())
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")

# SendGrid Email Configuration
SENDGRID_API_KEY = _require_env("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = _require_env("SENDGRID_FROM_EMAIL")

# OTP Configuration
OTP_EXPIRE_MINUTES = int(os.getenv("OTP_EXPIRE_MINUTES", "5"))
