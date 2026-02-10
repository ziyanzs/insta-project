from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator

from app.deps.auth import get_current_user
from app.db.supabase import supabase
from app.ml.predictor import classify_text

router = APIRouter(prefix="/posts", tags=["comments"])

class CommentCreate(BaseModel):
    body: str

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: str) -> str:
        v = (v or "").strip()
        if len(v) == 0:
            raise ValueError("Komentar tidak boleh kosong")
        if len(v) > 500:
            raise ValueError("Komentar maksimal 500 karakter")
        return v


@router.post("/{post_id}/comments")
def create_comment(post_id: int, payload: CommentCreate, user=Depends(get_current_user)):
    # 1) pastikan post ada
    post_res = (
        supabase.table("posts")
        .select("id")
        .eq("id", post_id)
        .limit(1)
        .execute()
    )
    if not post_res.data:
        raise HTTPException(status_code=404, detail="Post tidak ditemukan")

    # 2) ML classify (sexual harassment detection)
    ml = classify_text(payload.body)

    if ml.label == 1:
        # BLOCK
        raise HTTPException(
            status_code=422,
            detail={
                "code": "COMMENT_BLOCKED",
                "message": "Komentar tidak dapat terkirim, terdeteksi pelecehan. Komentar anda melanggar etika komunikasi, perbaiki pilihan kata anda",
                "confidence": round(ml.confidence, 4),
            },
        )

    # 3) insert comment kalau aman
    try:
        res = (
            supabase.table("comments")
            .insert(
                {
                    "body": payload.body,
                    "author_id": int(user["id"]),
                    "post_id": int(post_id),
                    "disabled": False,
                }
            )
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal insert comment: {e}")

    if not res.data:
        raise HTTPException(status_code=500, detail="Insert comment gagal (data kosong).")

    return {"message": "Komentar terkirim", "comment": res.data[0]}
