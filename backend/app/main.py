from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from backend.app.db import engine
from starlette.middleware.cors import CORSMiddleware
from backend.app.api.middleware import BoundaryMiddleware, install_handlers
from backend.app.api.v1.router import router
from fastapi.openapi.utils import get_openapi
from backend.app.schemas.screenshots import ScreenshotUpload

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


def contract_openapi():
    if app.openapi_schema is None:
        schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
        upload = ScreenshotUpload.model_json_schema(ref_template="#/components/schemas/{model}")
        schema["components"]["schemas"].update(upload.pop("$defs", {}))
        schema["components"]["schemas"]["ScreenshotUpload"] = upload
        path = "/api/v1/projects/{project_id}/screenshots"
        metadata = schema["paths"][path]["post"]["requestBody"]["content"]["multipart/form-data"]["schema"]["properties"]["metadata"]
        metadata["contentSchema"] = {"$ref": "#/components/schemas/ScreenshotUpload"}
        for path, operations in schema["paths"].items():
            for operation in operations.values():
                if not isinstance(operation, dict) or "responses" not in operation:
                    continue
                for status, response in operation["responses"].items():
                    response.setdefault("headers", {})["X-Request-ID"] = {"schema": {"type": "string", "format": "uuid"}}
                    if status == "201":
                        response["headers"]["Location"] = {"schema": {"type": "string"}}
                    if status == "503":
                        response["headers"]["Retry-After"] = {"schema": {"type": "integer", "const": 5}}
        app.openapi_schema = schema
    return app.openapi_schema


app.openapi = contract_openapi


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
