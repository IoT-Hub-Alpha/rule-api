from fastapi import FastAPI

from ..api.routes import router as rules_router
from ..db.db import Base, engine
from .settings import settings


app = FastAPI(title="Rule API Service")

if settings.create_tables:
    Base.metadata.create_all(bind=engine)

app.include_router(rules_router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
