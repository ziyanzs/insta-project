from datetime import datetime, timedelta, timezone
from jose import jwt
import uuid
from app.core.config import settings

ALGO = "HS256"

def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "user_id": user_id,
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": exp,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGO)