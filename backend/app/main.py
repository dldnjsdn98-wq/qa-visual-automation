from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from backend.app.db import engine
from starlette.middleware.cors import CORSMiddleware
from backend.app.api.middleware import BoundaryMiddleware, install_handlers
from backend.app.api.v1.router import router

app = FastAPI(title="Game Multilingual QA Visual Automation System", version="0.1.0")
install_handlers(app)
app.include_router(router)
app.add_middleware(BoundaryMiddleware)
app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
    expose_headers=["X-Request-ID", "Location", "Retry-After"],
)


class HealthResponse(BaseModel):
    status: str


@app.get("/health", response_model=HealthResponse, tags=["operations"])
def health() -> HealthResponse:
    """Application liveness; does not claim database readiness."""
    return HealthResponse(status="ok")


@app.get("/ready", response_model=HealthResponse, tags=["operations"])
def ready() -> HealthResponse:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database unavailable") from None
    return HealthResponse(status="ready")
