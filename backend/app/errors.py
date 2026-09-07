class DomainError(Exception):
    def __init__(self, status=422, code="VALIDATION_ERROR", message="Request validation failed", field=None, reason=None):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message
        self.details = [{"field": field, "reason": reason}] if reason else []


def not_found():
    return DomainError(404, "RESOURCE_NOT_FOUND", "Resource not found")


def database_error(exc):
    from sqlalchemy.exc import IntegrityError
    if isinstance(exc, IntegrityError):
        state = getattr(exc.orig, "sqlstate", None)
        if state == "23505":
            return DomainError(409, "DUPLICATE_RESOURCE", "Resource already exists")
        if state == "23503":
            return DomainError(409, "RESOURCE_IN_USE", "Resource is referenced or a reference changed")
        if state in ("23514", "23502", "22021", "22P05"):
            return DomainError(reason="Invalid persisted value")
    return DomainError(503, "DATABASE_UNAVAILABLE", "Database unavailable")
