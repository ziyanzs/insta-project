from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(password: str) -> str:
    password = (password or "").strip()
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    password = (password or "").strip()
    return pwd_context.verify(password, password_hash)
