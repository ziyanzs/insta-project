from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth
from app.db.supabase import supabase

app = FastAPI(title="Insta Clone API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)

@app.get("/db-check")
def db_check():
    try:
        res = supabase.table("roles").select("id,name").limit(1).execute()
        return {"ok": True, "data": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))