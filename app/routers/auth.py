from fastapi import APIRouter, HTTPException, Depends
from app.db.supabase import supabase
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.core.security import hash_password, verify_password
from app.core.jwt_utils import create_access_token
from app.deps.auth import get_current_user

router = APIRouter(tags=["auth"])

@router.get("/me")
def me(user=Depends(get_current_user)):
    return {"user": user}

@router.post("/register")
def register(payload: RegisterRequest):
    # cek email
    email_check = supabase.table("users").select("id").eq("email", payload.email).limit(1).execute()
    if email_check.data:
        raise HTTPException(status_code=409, detail="Email sudah terdaftar")

    # cek username
    uname_check = supabase.table("users").select("id").eq("username", payload.username).limit(1).execute()
    if uname_check.data:
        raise HTTPException(status_code=409, detail="Username sudah terpakai")

    ins = supabase.table("users").insert({
        "email": payload.email,
        "username": payload.username,
        "password_hash": hash_password(payload.password),
        # role_id boleh null dulu; nanti bisa set default role
    }).execute()

    return {"message": "Register berhasil", "user": ins.data[0]}

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    res = supabase.table("users").select("id,email,username,password_hash").eq("email", payload.email).limit(1).execute()
    if not res.data:
        raise HTTPException(status_code=401, detail="Email atau password salah")

    user = res.data[0]
    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email atau password salah")

    token = create_access_token(user_id=int(user["id"]))
    return TokenResponse(access_token=token)
