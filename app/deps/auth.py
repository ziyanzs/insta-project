from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError

from app.core.config import settings
from app.db.supabase import supabase

bearer = HTTPBearer()
ALGO = "HS256"

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    token = creds.credentials

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGO])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Optional: cek token_blocklist kalau nanti kamu implement logout revocation
    # jti = payload.get("jti")
    # blocked = supabase.table("token_blocklist").select("id").eq("jti", jti).limit(1).execute()
    # if blocked.data:
    #     raise HTTPException(status_code=401, detail="Token revoked")

    res = supabase.table("users").select("id,email,username,user_image_url,role_id,created_at").eq("id", user_id).limit(1).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="User not found")
    return res.data[0]
