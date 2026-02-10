from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.db.supabase import supabase

from app.routers.auth import router as auth_router
from app.routers.posts import router as posts_router
from app.routers.comments import router as comments_router

app = FastAPI(title="Insta Clone API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # jangan "*" kalau allow_credentials=True
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(posts_router)
app.include_router(comments_router)

@app.get("/db-check")
def db_check():
    try:
        res = supabase.table("roles").select("id,name").limit(1).execute()
        return {"ok": True, "data": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
from app.ml.predictor import load_model_once

@app.on_event("startup")
def _startup():
    load_model_once()
