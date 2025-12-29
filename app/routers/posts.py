from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from app.deps.auth import get_current_user
from app.db.supabase import supabase
from app.core.config import settings
from typing import Optional

import uuid

router = APIRouter(prefix="/posts", tags=["posts"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/jpg"}
ALLOWED_EXT = {"jpg", "jpeg", "png"}
MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

##create post
@router.post("/")
async def create_post(
    file: UploadFile = File(...),
    body: str | None = Form(default=None),
    user=Depends(get_current_user),
):
    # 1) validasi mimetype
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail="File harus berupa gambar (jpg, jpeg, png)."
        )

    # 2) validasi ekstensi
    filename = file.filename or ""
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=415, detail="Ekstensi file tidak didukung.")

    # 3) baca bytes & validasi ukuran
    content = await file.read()
    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Ukuran file maksimal 5MB.")

    # 4) upload ke Supabase Storage
    # path file: userId/uuid.ext
    obj_name = f"{user['id']}/{uuid.uuid4().hex}.{ext}"

    try:
        # supabase-py expects bytes
        supabase.storage.from_(settings.SUPABASE_POSTS_BUCKET).upload(
            path=obj_name,
            file=content,
            file_options={"content-type": file.content_type},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal upload ke storage: {e}")

    # 5) ambil public URL
    public_url = supabase.storage.from_(settings.SUPABASE_POSTS_BUCKET).get_public_url(obj_name)

    # 6) insert ke tabel posts
    try:
        res = supabase.table("posts").insert({
            "body": body,
            "uploaded_content_url": public_url,
            "author_id": int(user["id"]),
        }).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal insert posts: {e}")

    if not res.data:
        raise HTTPException(status_code=500, detail="Insert post gagal (data kosong).")

    return {"message": "Post berhasil dibuat", "post": res.data[0]}

##tampilan feed (10 postingan)
@router.get("/feed")
def get_feed(offset: int = 0, user=Depends(get_current_user)):
    limit = 10
    offset = max(0, offset)

    # 1) ambil daftar user yang kita follow
    follows = (
        supabase.table("follows")
        .select("following_to")
        .eq("follower_id", user["id"])
        .execute()
    )

    # include diri sendiri + hindari duplikasi
    following_ids = list({f["following_to"] for f in follows.data} | {user["id"]})

    # 2) ambil post dari following_ids
    posts_res = (
        supabase.table("posts")
        .select("id, body, uploaded_content_url, timestamp, author_id")
        .in_("author_id", following_ids)
        .order("timestamp", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    posts = posts_res.data or []

    # 3) ambil data author (username + foto profil) untuk semua author_id yang muncul di posts
    author_ids = list({p["author_id"] for p in posts})
    authors_map = {}

    if author_ids:
        users_res = (
            supabase.table("users")
            .select("id, username, user_image_url")
            .in_("id", author_ids)
            .execute()
        )
        authors_map = {u["id"]: u for u in (users_res.data or [])}

    # 4) tempelkan author ke tiap post
    for p in posts:
        p["author"] = authors_map.get(p["author_id"], None)

    return {
        "data": posts,
        "limit": limit,
        "offset": offset,
        "next_offset": offset + limit,
    }

##detail postingan
@router.get("/{post_id}")
def get_post_detail(
    post_id: int,
    comments_limit: int = 20,
    comments_offset: int = 0,
):
    comments_limit = max(1, min(comments_limit, 50))
    comments_offset = max(0, comments_offset)

    # 1) ambil post
    post_res = (
        supabase.table("posts")
        .select("id, body, uploaded_content_url, timestamp, author_id")
        .eq("id", post_id)
        .limit(1)
        .execute()
    )

    if not post_res.data:
        raise HTTPException(status_code=404, detail="Post tidak ditemukan")

    post = post_res.data[0]

    # 2) ambil author post
    author_res = (
        supabase.table("users")
        .select("id, username, user_image_url")
        .eq("id", post["author_id"])
        .limit(1)
        .execute()
    )
    post["author"] = author_res.data[0] if author_res.data else None

    # 3) ambil comments per post (paginasi)
    comments_res = (
        supabase.table("comments")
        .select("id, body, timestamp, author_id, post_id, disabled")
        .eq("post_id", post_id)
        .eq("disabled", False)  # hanya komentar yang tidak di-disable
        .order("timestamp", desc=False)  # IG biasanya urut lama -> baru
        .range(comments_offset, comments_offset + comments_limit - 1)
        .execute()
    )

    comments = comments_res.data or []

    # 4) ambil author untuk semua komentar (batch)
    comment_author_ids = list({c["author_id"] for c in comments})
    authors_map = {}

    if comment_author_ids:
        users_res = (
            supabase.table("users")
            .select("id, username, user_image_url")
            .in_("id", comment_author_ids)
            .execute()
        )
        authors_map = {u["id"]: u for u in (users_res.data or [])}

    # 5) tempelkan author ke tiap comment
    for c in comments:
        c["author"] = authors_map.get(c["author_id"], None)

    return {
        "post": post,
        "comments": {
            "data": comments,
            "limit": comments_limit,
            "offset": comments_offset,
            "next_offset": comments_offset + comments_limit,
        },
    }
