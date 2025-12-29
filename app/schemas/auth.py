from pydantic import BaseModel, EmailStr, field_validator

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if v is None:
            raise ValueError("Password wajib diisi")
        v = v.strip()  # buang spasi depan/belakang
        if len(v) < 8:
            raise ValueError("Password minimal 8 karakter")
        # bcrypt limit 72 bytes (bukan chars). Kita cek bytes UTF-8.
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password terlalu panjang (maks 72 bytes)")
        return v

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
