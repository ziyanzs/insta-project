from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Insta Clone API (FastAPI + Supabase)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # nanti bisa kamu batasi ke domain frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}
