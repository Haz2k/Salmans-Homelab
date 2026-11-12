import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import models
from .database import Base, engine
from .routers import categories, receipts, summary

Base.metadata.create_all(bind=engine)

DATA_DIR = os.environ.get("RECEIPTS_DATA_DIR", "/data/receipts")
os.makedirs(DATA_DIR, exist_ok=True)

app = FastAPI(title="Receipts")

app.include_router(receipts.router)
app.include_router(categories.router)
app.include_router(summary.router)

app.mount("/files", StaticFiles(directory=DATA_DIR), name="files")


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
