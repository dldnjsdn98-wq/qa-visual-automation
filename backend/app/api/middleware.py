import logging
from urllib.parse import unquote_to_bytes, parse_qsl
from uuid import uuid4
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from backend.app.errors import DomainError, database_error
from backend.app.validation.unicode import decode_json, validate_unicode

log = logging.getLogger(__name__)


def validation_error(exc, prefix=None):
    error = DomainError()
    for issue in exc.errors():
        location = list(issue["loc"])
        if prefix:
            location.insert(0, prefix)
        # Input and error context are deliberately never serialized.
        error.details.append({"field": ".".join(map(str, location)) or "body", "reason": issue["type"]})
    return error


def error_response(error, request_id, headers=None):
    result_headers = dict(headers or {})
    result_headers["X-Request-ID"] = request_id
    if error.status == 503:
        result_headers["Retry-After"] = "5"
    return JSONResponse({"error": {"code": error.code, "message": error.message, "details": error.details, "request_id": request_id}}, status_code=error.status, headers=result_headers)


def install_handlers(app):
    @app.exception_handler(DomainError)
    async def domain(request, exc):
        return error_response(exc, request.state.request_id)

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return error_response(validation_error(exc), request.state.request_id)

    @app.exception_handler(SQLAlchemyError)
    async def database(request, exc):
        return error_response(database_error(exc), request.state.request_id)

    @app.exception_handler(HTTPException)
    async def http(request, exc):
        if not request.url.path.startswith("/api/v1"):
            return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers)
        code = {404: "RESOURCE_NOT_FOUND", 405: "METHOD_NOT_ALLOWED", 415: "UNSUPPORTED_MEDIA_TYPE"}.get(exc.status_code, "VALIDATION_ERROR")
        message = {404: "Resource not found", 405: "Method not allowed", 415: "Unsupported media type"}.get(exc.status_code, "Request failed")
        return error_response(DomainError(exc.status_code, code, message), request.state.request_id, exc.headers)


class BoundaryMiddleware:
    """Bound actual received bytes before parsing, even without Content-Length."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        request_id = str(uuid4())
        scope.setdefault("state", {})["request_id"] = request_id
        started = False
        async def send_with_id(message):
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
                message["headers"] = [(k, v) for k, v in message.get("headers", []) if k.lower() != b"x-request-id"] + [(b"x-request-id", request_id.encode())]
            await send(message)
        try:
            if scope["path"].startswith("/api/v1"):
                try:
                    path = unquote_to_bytes(scope.get("raw_path", scope["path"].encode())).decode("utf-8", "strict")
                    raw_query = scope.get("query_string", b"").decode("ascii", "strict")
                    query = parse_qsl(raw_query, keep_blank_values=True, encoding="utf-8", errors="strict")
                except UnicodeError:
                    raise DomainError(field="path" if not scope.get("query_string") else "query", reason="invalid UTF-8") from None
                validate_unicode(path, "path")
                for key, value in query:
                    validate_unicode({key: value}, "query")
                headers = dict(scope["headers"])
                if scope["method"] in ("POST", "PUT", "PATCH"):
                    body = bytearray()
                    while True:
                        message = await receive()
                        if message["type"] == "http.disconnect":
                            return
                        body.extend(message.get("body", b""))
                        if len(body) > 22_020_096:
                            raise DomainError(413, "UPLOAD_TOO_LARGE", "Request exceeds 21 MiB")
                        if not message.get("more_body", False):
                            break
                    media = headers.get(b"content-type", b"").split(b";", 1)[0].lower()
                    is_upload = scope["method"] == "POST" and scope["path"].rstrip("/").endswith("/screenshots")
                    if is_upload:
                        if media != b"multipart/form-data":
                            raise DomainError(415, "UNSUPPORTED_MEDIA_TYPE", "Use multipart/form-data")
                    else:
                        if media != b"application/json":
                            raise DomainError(415, "UNSUPPORTED_MEDIA_TYPE", "Use application/json")
                        decode_json(bytes(body))
                    delivered = False
                    original_receive = receive
                    async def replay():
                        nonlocal delivered
                        if not delivered:
                            delivered = True
                            return {"type": "http.request", "body": bytes(body), "more_body": False}
                        return await original_receive()
                    receive = replay
            await self.app(scope, receive, send_with_id)
        except DomainError as exc:
            if started:
                raise
            await error_response(exc, request_id)(scope, receive, send_with_id)
        except Exception:
            if started:
                raise
            log.error("Unhandled request failure; request_id=%s", request_id)
            await error_response(DomainError(500, "INTERNAL_ERROR", "Internal server error"), request_id)(scope, receive, send_with_id)
