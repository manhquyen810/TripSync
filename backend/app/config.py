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


def _optional_env(name: str) -> str | None:
	value = os.getenv(name)
	if value is None:
		return None
	value = str(value).strip()
	return value if value else None


DATABASE_URL = _require_env("DATABASE_URL")
SECRET_KEY = _require_env("SECRET_KEY")

_expire_raw = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200")
ACCESS_TOKEN_EXPIRE_MINUTES = int(_expire_raw.split("#", 1)[0].strip())
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")


def _parse_cors_origins(raw: str) -> list[str]:
	value = (raw or "").strip()
	if not value:
		return ["*"]
	if value == "*":
		return ["*"]
	items = [v.strip() for v in value.split(",")]
	return [v for v in items if v]

CORS_ORIGINS = _parse_cors_origins(os.getenv("CORS_ORIGINS", "*"))

# SendGrid Email Configuration
SENDGRID_API_KEY = _require_env("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = _require_env("SENDGRID_FROM_EMAIL")

# OTP Configuration
OTP_EXPIRE_MINUTES = int(os.getenv("OTP_EXPIRE_MINUTES", "5"))

# Cloudinary (optional, recommended for Render free to persist uploads)
# Either provide CLOUDINARY_URL or the triplet CLOUDINARY_CLOUD_NAME/API_KEY/API_SECRET.
CLOUDINARY_URL = _optional_env("CLOUDINARY_URL")
CLOUDINARY_CLOUD_NAME = _optional_env("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = _optional_env("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = _optional_env("CLOUDINARY_API_SECRET")

CLOUDINARY_ENABLED = bool(
	CLOUDINARY_URL
	or (CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET)
)
