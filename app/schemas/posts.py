from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PostResponse(BaseModel):
    id: int
    body: Optional[str]
    uploaded_content_url: str
    author_id: int
    timestamp: datetime

    class Config:
        from_attributes = True