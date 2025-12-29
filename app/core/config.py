from pydantic import BaseModel
import os

class Settings(BaseModel):
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

    SUPABASE_POSTS_BUCKET: str = os.getenv("SUPABASE_POSTS_BUCKET", "posts")

settings = Settings()
